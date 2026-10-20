#!/usr/bin/env python3
"""Enemy voice takes drafted with the local Chatterbox server (D87), processed for listening.

D87 (2026-10-20): the enemy voices come now from Chatterbox Multilingual and
its predefined male voices, drafts first, the CEO listens before anything
installs. What to say, in which language and how is owned by
`docs/sound/VOICE-SCRIPT.md` §1 (the 16 spoken rows; the six wordless rows,
grunts and last breaths, are not generated: their fallback stays on SFX);
the shout vs death settings come from
`docs/product/2026-10-14_2156_P2_local-voice-generation.md` §4.2 and §4.4.

Three steps, each its own sub-command:

    generate   POST /tts to the Chatterbox-TTS-Server already running at
               http://127.0.0.1:8004 (never started or stopped here), one
               request per take, the WAV kept as the server returned it
               (VOICE-SCRIPT §0.7: "tal como sale") with a JSON sidecar of
               the request. Takes already on disk are not regenerated.
    process    each raw take -> trim the silence (and anything after a long
               gap, where these models leave junk), high-pass 90 Hz, a gentle
               radio colour on the Liberty Legion only (VOICE-SCRIPT §1.2;
               the full LEGION-RADIO chain of ENEMY-SOUNDS §4 comes later),
               then levelled to the Freedoom sound the line replaces with
               the ruler of gen_weapon_alts.py (loudest 50 ms, A-weighted;
               peak at -1 dBFS; a look-ahead limiter, never a clip). OGG out.
    page       the listening page (OK/NO/?, "Copiar resultado").

Outputs (gitignored `work/`, VOICE-SCRIPT §0.5 names + `_tNN`):

    work/audio/voice_takes/raw/<row>_<lump>_ai_chatterbox_<date>_tNN.wav   as generated
    work/audio/voice_takes/raw/<same>.json                                  the request, the server
    work/audio/voice_takes/<row>_<lump>_ai_chatterbox_<date>_tNN.ogg        processed
    work/audio/voice_takes/AI-LOG.csv          VOICE-SCRIPT §0.7, one row per take
    work/audio/voice_takes/MANIFEST.txt        the cast, levels, lengths

Run:

    .venv/Scripts/python.exe tools/audio/process_voice_takes.py generate
    .venv/Scripts/python.exe tools/audio/process_voice_takes.py process \\
        --page docs/art/previews/<YYYY-MM-DD_HHMM>_P2_voice-takes.html
    .venv/Scripts/python.exe -m unittest tests.test_process_voice_takes -v

GPL-3.0 (the script). The audio it drafts is not cleared for the mod until
the CEO approves it and its licence row exists (D36, D87).
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:  # numpy is the venv's; the tables below stay importable without it
    import numpy as np
    import gen_weapon_alts as wa  # noqa: E402  (the ruler and the limiter)
    import gen_weapon_sfx as gws  # noqa: E402  (decode, WAV/OGG, the IWAD)
except ImportError:  # pragma: no cover - the fast tier's bare Python
    np = wa = gws = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "work" / "audio" / "voice_takes"
RAW_DIR = OUT_DIR / "raw"
FREEDOOM_PREVIEW_DIR = PROJECT_ROOT / "work" / "audio" / "preview" / "freedoom"
ASR_PATH = OUT_DIR / "ASR.json"          # optional Whisper transcripts, shown on the page

SERVER = "http://127.0.0.1:8004"
TOOL_TAG = "chatterbox"                  # the <herramienta> of VOICE-SCRIPT §0.5
TOOL_NAME = ("Chatterbox-TTS-Server 2.0.2 (github.com/devnen/Chatterbox-TTS-Server) "
             "+ Chatterbox Multilingual (Resemble AI)")
MODEL_NAME = "ChatterboxMultilingualTTS (chatterbox-multilingual, 24 kHz, cuda)"
LICENCE_NOTE = ("MIT, https://huggingface.co/ResembleAI/chatterbox; read 2026-10-14 by the P2 study "
                "(docs/product/2026-10-14_2156_P2_local-voice-generation.md), not re-read today; "
                "output carries the inaudible PerTh watermark")
VOICE_ORIGIN_NOTE = "predefined voice shipped with Chatterbox-TTS-Server, origin not documented (D87, R1)"
PLAN = "free, local"
TAKES = 3
# More takes where the first three failed a check (2026-10-20): G02 is the one
# line the player must understand and its first three were heard by Whisper as
# "Forts"/"Forex"; R04's one syllable as "Bye"/"Find"; L04 t02 ran away for 9 s.
# The counts are VOICE-SCRIPT §1's own for those rows (8, 5, 5).
EXTRA_TAKES = {"G02": 8, "R04": 5, "L04": 5}
REQUEST_TIMEOUT_S = 180

# --- The cast (D87: male-named predefined voices only) ---------------------------------
# The 18 male-named voices were measured from their reference WAVs in
# Z:/Chatterbox/Chatterbox-TTS-Server/voices/ (autocorrelation F0, 40 ms
# frames, median of voiced frames; spectral centroid of the whole clip).
# Henry (176 Hz), Julian (175 Hz), Connor and Jeremiah (164 Hz) sit in the
# male/female overlap and were dropped. The three picked are the furthest
# apart in F0 and centroid. Not heard by the PM or by me: the page is the test.
MALE_VOICES = ("Adrian", "Alexander", "Austin", "Axel", "Connor", "Eli", "Everett", "Gabriel",
               "Henry", "Ian", "Jeremiah", "Jordan", "Julian", "Leonardo", "Michael", "Miles",
               "Ryan", "Thomas")
DROPPED_VOICES = ("Henry", "Julian", "Connor", "Jeremiah")
MAX_MEDIAN_F0_HZ = 160.0                # above this a reference was not cast


@dataclass(frozen=True)
class Voice:
    name: str               # predefined voice id without .wav
    f0_hz: float            # median F0 of the reference clip
    centroid_hz: int        # spectral centroid of the reference clip
    why: str                # Spanish, for the page


CAST: dict[str, Voice] = {
    "rifleman": Voice("Austin", 122.5, 393,
                      "grave y oscura (el centroide más bajo de las 18): seca, para el Reich"),
    "trooper": Voice("Jordan", 147.0, 818,
                     "la más aguda de las elegidas y brillante: las consonantes sobreviven a la radio"),
    "general": Voice("Thomas", 110.0, 1034,
                     "la más grave de las 18 y de timbre áspero; luego se baja 4 semitonos (GENERAL-SLOT)"),
}
CLASS_LABEL = {   # Spanish, for the page
    "rifleman": "Fusilero del Cuarto Reich (SD_ReichRifleman) · alemán",
    "trooper": "Soldado de la Legión de la Libertad (SD_LegionTrooper) · inglés, por radio",
    "general": "El General (SD_General) · inglés y una orden en alemán",
}


@dataclass(frozen=True)
class Delivery:
    exaggeration: float
    cfg_weight: float
    temperature: float
    note: str


# P2 study §4.2 and §4.4; the task's "shouts high exaggeration, low cfg".
DELIVERY: dict[str, Delivery] = {
    "idle": Delivery(0.4, 0.5, 0.8, "murmullo"),
    "shout": Delivery(1.3, 0.3, 0.9, "ladrido"),
    "pain": Delivery(1.0, 0.3, 0.9, "dolor, tenso"),
    "death": Delivery(0.6, 0.3, 1.0, "muerte, apagándose"),
    "calm": Delivery(0.3, 0.6, 0.6, "el General: calma"),
}


@dataclass(frozen=True)
class Line:
    row: str
    lump: str
    cls: str
    moment: str         # VOICE-SCRIPT "Moment"
    text: str           # what Chatterbox reads (the script's line)
    lang: str
    delivery: str
    freedoom: str       # the Freedoom lump the line replaces today (src/lumps/SNDINFO)
    translation: str    # Spanish
    dur: tuple[float, float]   # VOICE-SCRIPT's target length of the finished sound

    @property
    def radio(self) -> bool:
        return self.cls == "trooper"


# The 16 spoken rows of VOICE-SCRIPT §1 (a test checks them against the script).
# Wordless rows skipped: R07, R08, L07, L09, G03, G04.
LINES: tuple[Line, ...] = (
    Line("R01", "SDRRIACT", "rifleman", "idle", "Stellung halten.", "de", "idle", "DSPOSACT",
         "Mantened la posición.", (1.0, 1.5)),
    Line("R02", "SDRRIACT", "rifleman", "idle", "Augen auf.", "de", "idle", "DSPOSACT",
         "Ojos abiertos.", (0.8, 1.2)),
    Line("R03", "SDRRIACT", "rifleman", "idle", "Ruhe da hinten.", "de", "idle", "DSPOSACT",
         "Silencio ahí detrás.", (1.0, 1.5)),
    Line("R04", "SDRRISIT", "rifleman", "alert", "Feind!", "de", "shout", "DSPOSIT1",
         "¡Enemigo!", (0.0, 0.5)),
    Line("R05", "SDRRISIT", "rifleman", "alert", "Da!", "de", "shout", "DSPOSIT1",
         "¡Ahí!", (0.0, 0.4)),
    Line("R06", "SDRRISIT", "rifleman", "alert", "Kontakt!", "de", "shout", "DSPOSIT1",
         "¡Contacto!", (0.0, 0.6)),
    Line("R09", "SDRRIDTH", "rifleman", "death", "Sani…", "de", "death", "DSPODTH1",
         "Sanitario… (apenas dicho, apagándose)", (0.0, 1.2)),
    Line("L01", "SDLTRACT", "trooper", "idle", "Sector four, clear.", "en", "idle", "DSPOSACT",
         "Sector cuatro, despejado.", (1.2, 1.6)),
    Line("L02", "SDLTRACT", "trooper", "idle", "Copy. Holding position.", "en", "idle", "DSPOSACT",
         "Recibido. Mantenemos posición.", (1.2, 1.8)),
    Line("L03", "SDLTRACT", "trooper", "idle", "Command, say again?", "en", "idle", "DSPOSACT",
         "Mando, repita.", (1.0, 1.4)),
    Line("L04", "SDLTRSIT", "trooper", "alert", "Contact!", "en", "shout", "DSPOSIT2",
         "¡Contacto!", (0.0, 0.6)),
    Line("L05", "SDLTRSIT", "trooper", "alert", "Hostile, front!", "en", "shout", "DSPOSIT2",
         "¡Hostil, al frente!", (0.0, 0.7)),
    Line("L06", "SDLTRSIT", "trooper", "alert", "Got movement!", "en", "shout", "DSPOSIT2",
         "¡Movimiento!", (0.0, 0.7)),
    Line("L08", "SDLTRPAI", "trooper", "pain", "I'm hit!", "en", "pain", "DSPOPAIN",
         "¡Me han dado!", (0.4, 0.5)),
    Line("G01", "SDGENSIT", "general", "alert", "Engage.", "en", "calm", "DSCYBSIT",
         "Atacad.", (1.0, 1.5)),
    Line("G02", "SDGENSUM", "general", "summon", "Vorwärts.", "de", "calm", "DSVILSIT",
         "Adelante.", (0.0, 1.2)),
)
WORDLESS_ROWS = ("R07", "R08", "L07", "L09", "G03", "G04")
LANG_LABEL = {"de": "alemán", "en": "inglés"}

# The Freedoom lumps these replace, measured from iwads/freedoom2.wad 0.13.0
# with gen_weapon_alts' rulers; a test re-measures them.
# name -> (peak dBFS, A-weighted loudest 50 ms dB, plain RMS dBFS)
FREEDOOM_LEVELS: dict[str, tuple[float, float, float]] = {
    "DSPOSACT": (-9.68, -28.63, -25.48),
    "DSPOSIT1": (0.0, -10.12, -11.04),
    "DSPOSIT2": (0.0, -11.15, -9.0),
    "DSPODTH1": (0.0, -10.6, -12.46),
    "DSPOPAIN": (-2.14, -11.37, -14.1),
    "DSCYBSIT": (-0.42, -14.01, -18.19),
    "DSVILSIT": (0.0, -9.6, -14.83),
}
LEVEL_TOLERANCE_DB = 0.2

# --- Processing constants -----------------------------------------------------------------
HIGH_PASS_HZ = 90.0
RADIO_BAND_HZ = (280.0, 3600.0)          # gentle: the full chain is 400-3200 plus crush (later)
RADIO_DRIVE = 1.6                        # a touch of tanh, the handset's grit
PEAK_DBFS = -1.0                         # the project's headroom (ENEMY-SOUNDS §6)
LOUDNESS_TOLERANCE_DB = 1.0
MIN_VOICE_DRIVE = 0.05                   # tanh(0.05 x) is linear to 0.01 dB
MAX_VOICE_DRIVE = 4.0                    # past this a voice crackles; the shortfall is reported
LEVEL_SEARCH_STEPS = 24
RUNAWAY_FACTOR = 3.0                     # a take this many times the script's length ran away
FRAME_S = 0.01                           # the trimming envelope
GATE_DB = -42.0                          # below the loudest frame: silence
MAX_GAP_S = 0.45                         # a longer pause ends the line (junk after it is cut)
PRE_ROLL_S = 0.02
POST_ROLL_S = 0.08
FADE_IN_S = 0.004
FADE_OUT_S = 0.03
TAIL_SILENCE_S = 0.002                   # the last samples are silent (tests)


def seed_of(line: Line, take: int) -> int:
    """Deterministic, distinct per row and take: 'R04' take 2 -> 14042."""
    group = {"R": 1, "L": 2, "G": 3}[line.row[0]]
    return group * 10000 + int(line.row[1:]) * 1000 + 40 + take


def take_name(line: Line, take: int, day: str) -> str:
    """VOICE-SCRIPT §0.5 for AI + _tNN: R04_SDRRISIT_ai_chatterbox_20261020_t01."""
    return f"{line.row}_{line.lump}_ai_{TOOL_TAG}_{day}_t{take:02d}"


def request_body(line: Line, take: int) -> dict:
    d = DELIVERY[line.delivery]
    return {"text": line.text, "voice_mode": "predefined",
            "predefined_voice_id": CAST[line.cls].name + ".wav", "output_format": "wav",
            "language": line.lang, "exaggeration": d.exaggeration, "cfg_weight": d.cfg_weight,
            "temperature": d.temperature, "seed": seed_of(line, take), "speed_factor": 1.0,
            "split_text": False}


def takes_of(line: Line) -> int:
    return EXTRA_TAKES.get(line.row, TAKES)


def line_of(name: str) -> Line:
    row = name.split("_", 1)[0]
    return next(l for l in LINES if l.row == row)


# --- generate ---------------------------------------------------------------------------

def post_tts(body: dict, server: str = SERVER) -> bytes:
    req = urllib.request.Request(server + "/tts", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as r:
        data = r.read()
    if data[:4] != b"RIFF":
        raise RuntimeError(f"the server did not return a WAV: {data[:200]!r}")
    return data


def generate(day: str, raw_dir: Path = RAW_DIR, server: str = SERVER, rows=None,
             takes: int | None = None, poster=post_tts, log=print) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for line in LINES:
        if rows and line.row not in rows:
            continue
        for t in range(1, (takes or takes_of(line)) + 1):
            name = take_name(line, t, day)
            wav = raw_dir / f"{name}.wav"
            if wav.is_file():
                continue
            body = request_body(line, t)
            data = poster(body, server)
            wav.write_bytes(data)
            (raw_dir / f"{name}.json").write_text(json.dumps(
                {"file": wav.name, "date": f"{day[:4]}-{day[4:6]}-{day[6:]}", "server": server,
                 "endpoint": "/tts", "model": MODEL_NAME, "request": body},
                ensure_ascii=False, indent=1), encoding="utf-8")
            made.append(wav)
            log(f"  {name}  {len(data)} bytes")
    return made


# --- process ----------------------------------------------------------------------------

def frames_db(x: "np.ndarray", rate: int) -> "np.ndarray":
    n = max(1, int(round(FRAME_S * rate)))
    m = len(x) // n
    if m == 0:
        return np.array([-120.0])
    e = np.mean(x[:m * n].reshape(m, n) ** 2, axis=1)
    return 10 * np.log10(np.maximum(e, 1e-12))


def trim(x: "np.ndarray", rate: int) -> tuple["np.ndarray", float]:
    """-> (the line, seconds cut after a long gap). Leading/trailing silence out."""
    db = frames_db(x, rate)
    on = np.flatnonzero(db >= db.max() + GATE_DB)
    if on.size == 0:
        return x[:0], 0.0
    n = max(1, int(round(FRAME_S * rate)))
    gap = int(round(MAX_GAP_S / FRAME_S))
    last = on[0]
    for f in on[1:]:
        if f - last > gap:
            break
        last = f
    a = max(0, on[0] * n - int(round(PRE_ROLL_S * rate)))
    b = min(len(x), (last + 1) * n + int(round(POST_ROLL_S * rate)))
    cut = (on[-1] - last) * FRAME_S
    y = x[a:b].copy()
    fi, fo = int(round(FADE_IN_S * rate)), int(round(FADE_OUT_S * rate))
    if len(y) > fi + fo:
        y[:fi] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
        y[-fo:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fo))
    tail = int(round(TAIL_SILENCE_S * rate))
    if len(y) > tail:
        y[-tail:] = 0.0
    return y, cut


def high_pass(x: "np.ndarray", f: float = HIGH_PASS_HZ) -> "np.ndarray":
    return gws.filt(x, lambda fr: gws.butter(fr, lo=f, order=2))


def radio_colour(x: "np.ndarray") -> "np.ndarray":
    lo, hi = RADIO_BAND_HZ
    y = gws.filt(x, lambda fr: gws.butter(fr, lo=lo, hi=hi, order=2))
    p = np.max(np.abs(y)) or 1.0
    return np.tanh(RADIO_DRIVE * y / p) / np.tanh(RADIO_DRIVE)


def _at_peak(x: "np.ndarray") -> "np.ndarray":
    p = np.max(np.abs(x))
    return x / p * 10 ** (PEAK_DBFS / 20) if p > 0 else x


def level(x: "np.ndarray", target_db: float) -> tuple["np.ndarray", float]:
    """-> (levelled, saturation drive used, 0 if none). Peak <= -1 dBFS.

    The loudest 50 ms, A-weighted (wa.loud_a_db), is brought to target_db:
    too loud at -1 dBFS, plain gain down; too quiet, a soft saturation
    (wa.soft: tanh, peak back at -1 dBFS) whose drive is searched up to
    MAX_VOICE_DRIVE. A look-ahead limiter does not work here: its 12 ms gain
    window spans a whole pitch period, so on a held vowel it is only a gain
    (measured: -6 to -24 dB of ceiling moved a shout by < 1 dB). Freedoom's
    voices are 8-bit and clipped, so a dark voice can stay short of them at
    the drive ceiling; the shortfall is reported, never forced.
    """
    y = _at_peak(x)
    loud = wa.loud_a_db(y)
    if loud >= target_db:
        return y * 10 ** ((target_db - loud) / 20), 0.0
    lo, hi = np.log(MIN_VOICE_DRIVE), np.log(MAX_VOICE_DRIVE)
    if wa.loud_a_db(wa.soft(y, MAX_VOICE_DRIVE)) < target_db:
        return wa.soft(y, MAX_VOICE_DRIVE), MAX_VOICE_DRIVE
    for _ in range(LEVEL_SEARCH_STEPS):
        mid = (lo + hi) / 2
        if wa.loud_a_db(wa.soft(y, float(np.exp(mid)))) < target_db:
            lo = mid
        else:
            hi = mid
    d = float(np.exp((lo + hi) / 2))
    return wa.soft(y, d), d


@dataclass
class Processed:
    name: str
    line: Line
    x: "np.ndarray"
    raw_s: float
    cut_s: float
    drive: float            # saturation drive used to reach the level, 0 if gain only


def process_wave(x: "np.ndarray", line: Line) -> tuple["np.ndarray", float, float]:
    """A raw take at gws.SR -> (finished, seconds cut after a gap, saturation drive)."""
    y, cut = trim(high_pass(x), gws.SR)
    if line.radio:
        y = radio_colour(y)
    y, drive = level(y, FREEDOOM_LEVELS[line.freedoom][1])
    tail = gws.n_of(TAIL_SILENCE_S)
    y[-tail:] = 0.0
    return y, cut, drive


def process(day: str, raw_dir: Path = RAW_DIR, out_dir: Path = OUT_DIR,
            log=print) -> list[Processed]:
    done = []
    for line in LINES:
        for wav in sorted(raw_dir.glob(f"{line.row}_{line.lump}_ai_{TOOL_TAG}_{day}_t*.wav")):
            x = gws.decode(wav)
            y, cut, drive = process_wave(x, line)
            ogg = gws.ogg_bytes(gws.wav_bytes(y))
            (out_dir / f"{wav.stem}.ogg").write_bytes(ogg)
            done.append(Processed(wav.stem, line, y, len(x) / gws.SR, cut, drive))
            log(f"  {wav.stem}  {len(y) / gws.SR:.2f} s  drive {drive:.2f}  cut {cut:.2f} s")
    return done


# --- AI-LOG.csv (VOICE-SCRIPT §0.7) ---------------------------------------------------------

LOG_FIELDS = ("fichero", "herramienta", "version_o_modelo", "fecha", "plan", "licencia_de_uso",
              "voz", "texto", "ajustes")


def log_rows(raw_dir: Path = RAW_DIR) -> list[dict]:
    rows = []
    for side in sorted(raw_dir.glob("*.json")):
        meta = json.loads(side.read_text(encoding="utf-8"))
        rq = meta["request"]
        rows.append({
            "fichero": meta["file"], "herramienta": TOOL_NAME, "version_o_modelo": meta["model"],
            "fecha": meta["date"], "plan": PLAN, "licencia_de_uso": LICENCE_NOTE,
            "voz": f"{rq['predefined_voice_id']} ({VOICE_ORIGIN_NOTE})", "texto": rq["text"],
            "ajustes": (f"language {rq['language']}, exaggeration {rq['exaggeration']}, "
                        f"cfg_weight {rq['cfg_weight']}, temperature {rq['temperature']}, "
                        f"seed {rq['seed']}, speed_factor {rq['speed_factor']}, "
                        f"split_text {str(rq['split_text']).lower()}, voice_mode {rq['voice_mode']}"),
        })
    return rows


def log_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LOG_FIELDS, delimiter=";", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def manifest_text(done: list[Processed]) -> str:
    out = ["Enemy voice drafts (D87), Chatterbox Multilingual, predefined male voices.", "",
           "Cast:"]
    for cls, v in CAST.items():
        out.append(f"  {cls:9s} {v.name:8s} F0 {v.f0_hz:5.1f} Hz  centroid {v.centroid_hz:4d} Hz")
    out += ["", "take; Freedoom ref; target dB; peak dBFS; loud_a dB; length s; raw s; cut after gap s; drive"]
    for p in done:
        lv = wa.levels(p.x)
        out.append(f"{p.name}; {p.line.freedoom}; {FREEDOOM_LEVELS[p.line.freedoom][1]:.2f}; "
                   f"{lv['peak']:.2f}; {lv['loud_a']:.2f}; {lv['length']:.2f}; {p.raw_s:.2f}; "
                   f"{p.cut_s:.2f}; {p.drive:.2f}")
    return "\n".join(out) + "\n"


# --- The listening page (the style of the M3 sheets) -----------------------------------------

PAGE_KEY_PREFIX = "sd-p2-voice-takes-"


def _rel(target: Path, page: Path) -> str:
    return wa._rel(target, page)


def is_runaway(length_s: float, line: Line) -> bool:
    """The model kept talking: far longer than the script's line."""
    return length_s > RUNAWAY_FACTOR * line.dur[1]


def short_by(loud_a: float, line: Line) -> float:
    """dB the take stays under its Freedoom sound (0 when within tolerance)."""
    gap = FREEDOOM_LEVELS[line.freedoom][1] - loud_a
    return gap if gap > LOUDNESS_TOLERANCE_DB else 0.0


def load_asr(path: Path) -> dict:
    """Optional automatic transcripts {take: {"text", "model"}} (made outside this tool)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def page_items(done: list[Processed], page: Path, out_dir: Path = OUT_DIR,
               raw_dir: Path = RAW_DIR, asr: dict | None = None) -> list[dict]:
    items = []
    asr = asr or {}
    for p in done:
        l, d = p.line, DELIVERY[p.line.delivery]
        lv = wa.levels(p.x)
        lo, hi = l.dur
        over = lv["length"] > hi + 0.05
        short = short_by(lv["loud_a"], l)
        heard = asr.get(p.name, {}).get("text")
        items.append({
            "runaway": is_runaway(lv["length"], l), "asr": heard,
            "id": p.name, "row": l.row, "lump": l.lump, "cls": l.cls, "take": int(p.name[-2:]),
            "text": l.text, "tr": l.translation, "lang": LANG_LABEL[l.lang], "moment": l.moment,
            "voice": CAST[l.cls].name, "seed": seed_of(l, int(p.name[-2:])),
            "set": f"exaggeration {d.exaggeration:g} · cfg {d.cfg_weight:g} · temperatura {d.temperature:g} ({d.note})",
            "src": _rel(out_dir / f"{p.name}.ogg", page),
            "raw": _rel(raw_dir / f"{p.name}.wav", page),
            "rep": l.freedoom, "repSrc": _rel(FREEDOOM_PREVIEW_DIR / f"{l.freedoom}.wav", page),
            "dur": round(lv["length"], 2),
            "target": (f"≤ {hi:g} s" if lo == 0 else f"{lo:g}-{hi:g} s").replace(".", ","),
            "over": over, "radio": l.radio,
            "lvl": (f"pico {lv['peak']:.1f} dBFS · fuerza {lv['loud_a']:.1f} dB "
                    f"(Freedoom {l.freedoom}: {FREEDOOM_LEVELS[l.freedoom][1]:.1f})"
                    + (f" · saturación suave {p.drive:.1f}" if p.drive > 0 else "")
                    + (f" · se queda {short:.1f} dB por debajo (sin forzar)" if short else "")
                    + (f" · cortados {p.cut_s:.2f} s tras una pausa larga" if p.cut_s > 0 else "")),
        })
    return items


PAGE_CSS_EXTRA = """
.line{padding:10px 12px 2px;border-top:1px solid var(--line)}
.line .say{font-size:17px;font-weight:600}.line .say i{font-weight:400;color:var(--mute);font-size:14px}
.warn{display:inline-block;font-size:11px;border-radius:10px;padding:0 7px;margin-left:6px;background:var(--q);color:#fff}
.castt{width:100%;border-collapse:collapse;font-size:13.5px;margin:6px 0 4px}
.castt th,.castt td{border-top:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.castt th{font-size:12.5px;color:var(--mute);font-weight:600}
"""

PAGE_JS = r"""
const KEY = "__KEY__";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = s => s.toFixed(2).replace(".", ",") + " s";
const audio = src => `<audio controls preload="none" src="${esc(src)}"></audio>`;
const vote = it => `<div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div><textarea class="note" placeholder="Nota (opcional)">${esc(st(it.id).n || "")}</textarea></div>`;
function row(it){
  let p = `<div class="pl main"><span>Toma ${it.take} · ${fmt(it.dur)}${it.runaway ? '<span class="warn">se desbocó: siguió hablando</span>' : (it.over ? '<span class="warn">más larga que el guion</span>' : "")}</span>${audio(it.src)}</div>`;
  p += `<div class="pl"><span>Tal como salió de Chatterbox (sin procesar)</span>${audio(it.raw)}</div>`;
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><div class="name"><code>${esc(it.id)}</code></div>
      <div class="meta"><b>Semilla</b> ${it.seed} · ${esc(it.set)}</div>
      <div class="meta"><b>Nivel:</b> ${esc(it.lvl)}</div>
      ${it.asr != null ? `<div class="meta"><b>Whisper entendió:</b> «${esc(it.asr)}»</div>` : ""}</div>
    <div class="players">${p}</div>${vote(it)}</div>`;
}
function build(){
  let h = "";
  for (const C of [...new Set(ITEMS.map(i => i.cls))]) {
    const its = ITEMS.filter(i => i.cls === C);
    h += `<details class="grp" open><summary>${esc(CLASSES[C])} · voz <b>${esc(its[0].voice)}</b><span class="gcount" data-l="${esc(C)}"></span></summary>`;
    for (const R of [...new Set(its.map(i => i.row))]) {
      const rs = its.filter(i => i.row === R), a = rs[0];
      h += `<div class="line"><div class="say"><code>${esc(R)}</code> «${esc(a.text)}» <i>${esc(a.tr)}</i></div>
        <div class="meta">${esc(a.lang)} · momento <b>${esc(a.moment)}</b> · lump <code>${esc(a.lump)}</code> · duración del guion ${esc(a.target)}${a.radio ? " · con color de radio suave" : ""}</div>
        <div class="pl"><span>Lo que sustituiría: Freedoom <code>${esc(a.rep)}</code> (suena hoy)</span>${audio(a.repSrc)}</div></div>`;
      for (const it of rs) h += row(it);
    }
    h += `</details>`;
  }
  document.getElementById("groups").innerHTML = h;
  for (const it of ITEMS) paint(it.id);
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
  r.classList.toggle("hide", document.getElementById("onlyOpen").checked && !!s.v);
}
function summary(){
  const by = v => ITEMS.filter(i => st(i.id).v === v).map(i => i.id);
  const done = ITEMS.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  document.getElementById("pBar").style.width = (100 * done / ITEMS.length) + "%";
  for (const C of new Set(ITEMS.map(i => i.cls))) {
    const g = ITEMS.filter(i => i.cls === C), el = document.querySelector(`.gcount[data-l="${C}"]`);
    if (el) el.textContent = `${g.filter(i => st(i.id).v).length} / ${g.length}`;
  }
  const notes = ITEMS.filter(i => (st(i.id).n || "").trim()).map(i => `${i.id}: «${st(i.id).n.trim().replace(/\s+/g, " ")}»`);
  const open = ITEMS.filter(i => !st(i.id).v).map(i => i.id);
  const L = [`Voces de enemigos con Chatterbox (__STAMP__): ${done}/${ITEMS.length} juzgadas`,
    `OK (${by("ok").length}): ${by("ok").join(", ") || "—"}`,
    `NO (${by("no").length}): ${by("no").join(", ") || "—"}`,
    `? (${by("q").length}): ${by("q").join(", ") || "—"}`,
    `notas: ${notes.join(" / ") || "—"}`];
  if (open.length) L.push(`sin juzgar (${open.length}): ${open.join(", ")}`);
  document.getElementById("result").value = L.join("\n");
}
function copy(){
  const t = document.getElementById("result"), msg = document.getElementById("copied");
  summary();
  const done = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? done() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } t.scrollIntoView({block:"center"}); };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(done, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.addEventListener("play", e => { document.querySelectorAll("audio").forEach(a => { if (a !== e.target) a.pause(); }); }, true);
document.getElementById("onlyOpen").addEventListener("change", () => ITEMS.forEach(i => paint(i.id)));
document.getElementById("copyTop").addEventListener("click", copy);
document.getElementById("copyBottom").addEventListener("click", copy);
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar todas las respuestas y notas de esta hoja?")) { S = {}; save(); build(); summary(); } });
build(); summary();
"""


def cast_table_html() -> str:
    rows = "".join(
        f"<tr><td>{html.escape(CLASS_LABEL[c])}</td><td><b>{html.escape(v.name)}</b></td>"
        f"<td>{v.f0_hz:.0f} Hz</td><td>{v.centroid_hz} Hz</td><td>{html.escape(v.why)}</td></tr>"
        for c, v in CAST.items())
    return ("<table class=\"castt\"><thead><tr><th>Enemigo</th><th>Voz</th><th>Tono medio (F0)</th>"
            "<th>Brillo (centroide)</th><th>Por qué</th></tr></thead><tbody>" + rows + "</tbody></table>")


def page_html(done: list[Processed], page: Path, stamp: str, out_dir: Path = OUT_DIR,
              raw_dir: Path = RAW_DIR, asr: dict | None = None) -> str:
    items = page_items(done, page, out_dir, raw_dir, asr)
    asr_model = next((v.get("model") for v in (asr or {}).values()), None)
    n = len(items)
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    classes = json.dumps(CLASS_LABEL, ensure_ascii=False)
    js = PAGE_JS.replace("__KEY__", PAGE_KEY_PREFIX + stamp).replace("__STAMP__", stamp)
    skipped = ", ".join(WORDLESS_ROWS)
    dropped = ", ".join(DROPPED_VOICES)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voces de enemigos</title>
<style>{wa.PAGE_CSS}{PAGE_CSS_EXTRA}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Voces de enemigos (Chatterbox)</h1>
  <span class="prog">Juzgadas <b id="pDone">0</b> de <b>{n}</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> solo sin juzgar</label>
  <button class="primary" id="copyTop">Copiar resultado</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>Borradores de las <b>{len(LINES)} frases habladas</b> del guion de voces (<code>docs/sound/VOICE-SCRIPT.md</code> §1), {TAKES} tomas de cada una con semillas distintas (más en {", ".join(EXTRA_TAKES)}, donde las primeras fallaron), generadas con <b>Chatterbox Multilingual</b> en tu PC y sus voces predefinidas de nombre masculino (D87). El Reich habla alemán y la Legión inglés (D36). Pulsa <b>OK</b>, <b>NO</b> o <b>?</b> en cada toma y escribe una nota si quieres. Se guarda solo en este navegador. Al terminar, <b>Copiar resultado</b> y pégalo en el chat. Nada entra en el juego hasta que lo apruebes.</p>
  {cast_table_html()}
  <ul>
    <li><b>Reparto:</b> una voz por enemigo, elegida por el nombre y medida (tono y brillo de su clip de referencia), sin escucharla. Descartadas por tono dudoso (zona de solape hombre/mujer): {html.escape(dropped)}. Las voces predefinidas vienen con el servidor y su origen no está documentado (D87).</li>
    <li><b>Procesado:</b> silencio recortado, filtro de graves a {HIGH_PASS_HZ:.0f} Hz, y la Legión con un <b>color de radio suave</b> (la cadena de radio completa, con crujido y squelch, va después). Cada toma está <b>al volumen del sonido de Freedoom que sustituiría</b> (la misma regla que las armas: los 50 ms más fuertes, ponderación A); el reproductor de Freedoom está encima de cada frase.</li>
    <li><b>Aún sin cadena de facción:</b> el fusilero no tiene todavía la bajada de tono ni la saturación (REICH-DRY), ni el General sus −4 semitonos y la ranura (GENERAL-SLOT). Juzga la <b>interpretación y el alemán/inglés</b>, no el timbre final.</li>
    <li><b>Más larga que el guion:</b> el aviso marca tomas que pasan de la duración prevista; se puede acelerar o recortar al elegir.</li>
    <li><b>Sin palabras ({html.escape(skipped)}):</b> gruñidos y últimos alientos no se generan; siguen con los efectos de respaldo.</li>
    {f'<li><b>Whisper entendió:</b> transcripción automática de cada toma procesada con <code>{html.escape(asr_model)}</code>, en el idioma de la frase, para ver de un vistazo si se entiende. Es una máquina, no un oyente: tu oído manda.</li>' if asr_model else ''}
    <li>El registro de cada toma (herramienta, modelo, voz, semilla, ajustes) está en <code>work/audio/voice_takes/AI-LOG.csv</code>.</li>
  </ul>
</section>
<main id="groups"></main>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Resultado para pegar en el chat</h2>
  <p class="meta">Se actualiza solo. Si el botón no copia (algunos navegadores lo bloquean en archivos locales), selecciona el texto y Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copiar resultado</button> <button id="reset">Borrar todas mis respuestas</button></p>
</section>
<footer>Generado {html.escape(stamp)} por sound-designer con <code>tools/audio/process_voice_takes.py</code>. Audio: <code>work/audio/voice_takes/</code> (procesadas), <code>work/audio/voice_takes/raw/</code> (tal como salieron), <code>work/audio/preview/freedoom/</code> (Freedoom de hoy). La página lee los archivos del repo por ruta relativa: no la muevas de <code>docs/art/previews/</code>.</footer>
</div>
<script>
const ITEMS = {data};
const CLASSES = {classes};
{js}
</script>
</body>
</html>
"""


# --- CLI ----------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("generate", "process", "list"))
    ap.add_argument("--date", default=_date.today().strftime("%Y%m%d"), help="YYYYMMDD in the file names")
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--rows", nargs="*", help="only these rows (R04 L04 ...)")
    ap.add_argument("--page", type=Path, help="write the listening page here (process)")
    ap.add_argument("--stamp", help="the page's stamp (default: from the page name)")
    a = ap.parse_args(argv)
    if a.command == "list":
        for l in LINES:
            print(f"{l.row} {l.lump} {l.lang} {CAST[l.cls].name:7s} {l.delivery:5s} {l.freedoom:9s} {l.text}")
        return 0
    if a.command == "generate":
        made = generate(a.date, server=a.server, rows=a.rows)
        print(f"{len(made)} new takes in {RAW_DIR}")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        done = process(a.date)
        (OUT_DIR / "MANIFEST.txt").write_text(manifest_text(done), encoding="utf-8")
        print(f"{len(done)} takes processed into {OUT_DIR}")
        if a.page:
            page = a.page if a.page.is_absolute() else PROJECT_ROOT / a.page
            stamp = a.stamp or page.stem.split("_P2")[0]
            page.write_text(page_html(done, page, stamp, asr=load_asr(ASR_PATH)), encoding="utf-8")
            print(f"page: {page}")
    (OUT_DIR / "AI-LOG.csv").write_text(log_csv(log_rows()), encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
