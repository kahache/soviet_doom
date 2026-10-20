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
    .venv/Scripts/python.exe tools/audio/process_voice_takes.py refs        # round 2 (after D91)
    .venv/Scripts/python.exe tools/audio/process_voice_takes.py generate2
    .venv/Scripts/python.exe tools/audio/process_voice_takes.py process2 \\
        --page docs/art/previews/<YYYY-MM-DD_HHMM>_P2_voice-takes-aggressive.html
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
                "NOT watermarked: perth.PerthImplicitWatermarker is None in the server's Python "
                "(checked 2026-10-20), so the server and the CPU fallback skip the PerTh watermark")
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
            "voz": voice_note(meta), "texto": rq["text"],
            "ajustes": (f"language {rq['language']}, exaggeration {rq['exaggeration']}, "
                        f"cfg_weight {rq['cfg_weight']}, temperature {rq['temperature']}, "
                        f"seed {rq['seed']}, speed_factor {rq['speed_factor']}, "
                        f"split_text {str(rq['split_text']).lower()}, voice_mode {rq['voice_mode']}"),
        })
    return rows


def voice_note(meta: dict) -> str:
    """The AI-LOG "voz": the predefined voice, or the cloned reference with its sources and licences."""
    rq = meta["request"]
    if rq.get("voice_mode") != "clone":
        return f"{rq['predefined_voice_id']} ({VOICE_ORIGIN_NOTE})"
    ref = meta["reference"]
    src = "; ".join(f"{s['title']} by {s['author']}, {s['licence']}, {s['url']}"
                    + (f", credit: {s['credit']}" if s["credit"] else "") for s in ref["sources"])
    return f"clone of {ref['file']} (sha256 {ref['sha256']}; {src})"


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
      ${it.ref ? `<div class="meta"><b>Referencia:</b> ${esc(it.ref)}</div>` : ""}
      ${it.asr != null ? `<div class="meta"><b>Whisper entendió:</b> «${esc(it.asr)}»${it.asrWarn ? `<span class="warn">${esc(it.asrWarn)}</span>` : ""}</div>` : ""}</div>
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


# --- Round 2: cloned from aggressive references (after D91) ---------------------------------
# D91: Chatterbox takes no instructions, it copies the emotion of its reference, and the
# predefined voices are calm narration. So the lines with no approved take are redrafted in
# clone mode from shouted, licence-clean references the CEO authorised downloading
# (docs/sound/2026-10-20_1234_P2_aggressive-voice-references.md, §2 and §4). The downloads
# stay in work/audio/voice_refs/ (gitignored, never committed). Sub-commands:
#
#     refs       cut the downloads into 12-18 s references (mono 24 kHz, one speaker, dry,
#                peak -2 dBFS), write SOURCES.tsv (SHA-256 + licence of every file used) and
#                upload them with POST /upload_reference (the name carries the content hash:
#                the server skips a name it already has, so a changed cut gets a new name)
#     generate2  one /tts request per take (voice_mode clone), never several lines in one text
#     process2   the same chain as round 1, into work/audio/voice_takes/aggressive/; with
#                --page, the takes whose Whisper transcript (aggressive/ASR.json, made outside
#                this tool as in round 1) has extra words or a cut line are rejected first

import hashlib
import os
import re
import subprocess
import wave
from difflib import SequenceMatcher

REFS_DIR = PROJECT_ROOT / "work" / "audio" / "voice_refs"
SOURCES_TSV = REFS_DIR / "SOURCES.tsv"
AGGR_DIR = OUT_DIR / "aggressive"
AGGR_RAW_DIR = AGGR_DIR / "raw"
AGGR_ASR_PATH = AGGR_DIR / "ASR.json"
ROUND2_FIRST_TAKE = 11              # round-2 takes are t11, t12...: no name is shared with round 1
REF_SR = 24000                      # Chatterbox's own rate
REF_GAP_S = 0.25                    # silence between concatenated clips (research §4)
REF_MAX_PAUSE_S = 0.3               # longer pauses inside a clip are shortened to this
REF_GATE_DB = -40.0                 # below a clip's loudest 10 ms frame: silence
REF_PEAK_DBFS = -2.0                # never clip: a distorted reference clones the distortion
REF_LEN_S = (12.0, 18.0)            # under 8 s the timbre is unstable; over 20 s adds nothing
REF_CLIP_DBFS = -0.5                # a source clip whose decoded peak passes this is left out

# D91: the CEO's OK takes, kept untouched and shown as the reference row of the new page.
APPROVED = ("R06_SDRRISIT_ai_chatterbox_20261020_t01", "R06_SDRRISIT_ai_chatterbox_20261020_t03",
            "L01_SDLTRACT_ai_chatterbox_20261020_t01", "L01_SDLTRACT_ai_chatterbox_20261020_t03",
            "L02_SDLTRACT_ai_chatterbox_20261020_t01", "L02_SDLTRACT_ai_chatterbox_20261020_t02",
            "L02_SDLTRACT_ai_chatterbox_20261020_t03")
APPROVED_ROWS = tuple(sorted({n.split("_", 1)[0] for n in APPROVED}))


@dataclass(frozen=True)
class Source:
    path: str           # under REFS_DIR, as downloaded
    title: str
    author: str
    licence: str
    url: str
    credit: str         # the line the credits must carry ("" when CC0 asks none)


SOURCES: dict[str, Source] = {
    "thorsten": Source("thorsten/thorsten-emotional_v02.tgz", "Thorsten-Voice Dataset 2021.06 emotional v02, style angry",
                       "Thorsten Müller (voice), Dominik Kreutz (audio)", "CC0 1.0",
                       "https://zenodo.org/records/5525023", ""),
    "kurt_battle": Source("kurt/battlecries.ogg", "Soldier Voice Acting: battlecries.ogg", "kurt", "CC-BY 3.0",
                          "https://opengameart.org/content/soldier-voice-acting",
                          "Voice reference: kurt, \"Soldier Voice Acting\", OpenGameArt, CC-BY 3.0"),
    "kurt_wounded": Source("kurt/wounded.ogg", "Soldier Voice Acting: wounded.ogg", "kurt", "CC-BY 3.0",
                           "https://opengameart.org/content/soldier-voice-acting",
                           "Voice reference: kurt, \"Soldier Voice Acting\", OpenGameArt, CC-BY 3.0"),
    "haeldb": Source("haeldb/yelling_sounds.zip", "Male Grunt/Yelling sounds, vocalist 3 (3yell*)", "HaelDB",
                     "CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked)",
                     "https://opengameart.org/content/male-gruntyelling-sounds", ""),
}

THORSTEN_ANGRY = "thorsten/thorsten-emotional_v02/angry/"
HAELDB_DIR = "haeldb/unz/yelling sounds/"


@dataclass(frozen=True)
class Ref:
    key: str                # short id; the uploaded file is sd_ref_<key>_<sha8>.wav
    sources: tuple[str, ...]  # SOURCES keys: always one person
    lang: str               # "de", "en" or "-" (wordless)
    parts: tuple[tuple[str, float, float], ...]   # (file under REFS_DIR, start s, end s; 0 = to the end)
    label: str              # Spanish, for the page
    why: str                # Spanish, for the page


# Picked by measurement and transcript, not by ear (nobody here can listen): Thorsten's angry
# set is normalised, so the clips are ranked by pitch and brightness (a raised voice is higher
# and brighter) and kept only when Whisper wrote them as exclamations or orders; kurt's battle
# cries keep the long cries and the short barks whose decoded peak stays under REF_CLIP_DBFS;
# HaelDB's vocalist 3 is the most consistent in pitch of the four. The first 6 s matter most
# (Chatterbox conditions its speech model on them), so the hottest material goes first.
REFS: dict[str, Ref] = {
    "de_orders": Ref("de_orders", ("thorsten",), "de", (
        (THORSTEN_ANGRY + "f163672ff831b1954cf7e7b55f6a7791.wav", 0, 0),   # Nennen Sie Ihren Zielort!
        (THORSTEN_ANGRY + "584760ce7a02b570d6f9d7dfb887fe0d.wav", 0, 0),   # Reiß das Ding doch gleich ab!
        (THORSTEN_ANGRY + "1910c7ff4e2def4080401802af5b6575.wav", 0, 0),   # Dümmer geht's nicht mehr!
        (THORSTEN_ANGRY + "17a5a8163ef7fdc9272d621282b636b8.wav", 0, 0),   # Einheit Bravo an Zentrale! ...
        (THORSTEN_ANGRY + "03f5eea4317f51989cf09c5e9414dad1.wav", 0, 0),   # Beginnen Sie ... noch heute!
        (THORSTEN_ANGRY + "2e549180a9d7591a11d08112bf67f422.wav", 0, 0),   # Das ist ja alles verklebt!
    ), "Thorsten Müller, «angry» (alemán, CC0)",
        "frases leídas con enfado, no gritos de batalla: las órdenes y exclamaciones más agudas del conjunto "
        "(«Nennen Sie Ihren Zielort!», «Reiß das Ding doch gleich ab!», «Einheit Bravo an Zentrale!»…)"),
    "en_orders": Ref("en_orders", ("kurt_battle",), "en", (
        ("kurt/battlecries.ogg", 11.08, 13.14), ("kurt/battlecries.ogg", 14.0, 15.5),
        ("kurt/battlecries.ogg", 8.2, 10.12), ("kurt/battlecries.ogg", 16.7, 19.15),
        ("kurt/battlecries.ogg", 20.02, 21.25),
        ("kurt/battlecries.ogg", 0.92, 1.2), ("kurt/battlecries.ogg", 2.74, 2.96),
        ("kurt/battlecries.ogg", 3.33, 3.57), ("kurt/battlecries.ogg", 3.94, 4.19),
        ("kurt/battlecries.ogg", 5.32, 5.56), ("kurt/battlecries.ogg", 5.93, 6.18),
    ), "kurt, gritos de batalla (inglés, CC-BY 3.0)",
        "«For honor and glory… Forward we go… Defend yourselves!» y seis ladridos cortos"),
    "pain_haeldb": Ref("pain_haeldb", ("haeldb",), "-", tuple(
        (HAELDB_DIR + f"3yell{i}.wav", 0, 0) for i in (14, 1, 9, 2, 12, 15, 11, 10, 5, 13)),
        "HaelDB, vocalista 3: gritos de dolor sin palabras (CC0)",
        "gritos y quejidos sin palabras: sirven en cualquier idioma"),
    "pain_kurt": Ref("pain_kurt", ("kurt_wounded", "kurt_battle"), "en", (
        ("kurt/wounded.ogg", 0, 0), ("kurt/wounded.ogg", 0, 0),
        ("kurt/battlecries.ogg", 11.08, 13.14), ("kurt/battlecries.ogg", 16.7, 19.15),
        ("kurt/battlecries.ogg", 8.2, 10.12),
    ), "kurt, herido (inglés, CC-BY 3.0)",
        "sus 4 s de «¡Aaah!» dos veces delante (lo que más pesa) y tres gritos suyos detrás para llegar a 12 s: el mismo hombre"),
}


@dataclass(frozen=True)
class Take2:
    line: Line
    take: int
    ref: str            # REFS key
    exaggeration: float
    cfg_weight: float
    temperature: float
    text: str           # the script's words; only the punctuation may differ (an order ends in "!")
    lang: str


# Round-2 settings per delivery: one exaggeration per take (three seeds, a ladder, so one of
# them lands); cfg 0.3 for pace; shouts high, pain and death left to the reference.
DELIVERY2: dict[str, tuple[tuple[float, ...], float, float, str]] = {
    "idle": ((0.9, 1.1, 1.3), 0.3, 0.8, "orden seca y enfadada"),
    "shout": ((1.1, 1.3, 1.5), 0.3, 0.8, "grito"),
    "pain": ((0.6, 0.8, 1.0), 0.3, 0.8, "dolor: lo pone la referencia"),
    "death": ((0.5, 0.7, 0.9), 0.3, 0.8, "muerte: lo pone la referencia"),
    "calm": ((1.0, 1.2, 1.4), 0.3, 0.8, "el General: orden de mando"),
}
# Script text -> what round 2 sends (the same words: an order is read as one with "!").
TEXT2 = {"Stellung halten.": "Stellung halten!", "Augen auf.": "Augen auf!",
         "Ruhe da hinten.": "Ruhe da hinten!", "Engage.": "Engage!", "Vorwärts.": "Vorwärts!"}
# Extra takes from a second reference where round 1 was worst or the line matters most:
# (row, ref, exaggerations, cfg_weight).
ALT_TAKES = (("R09", "pain_kurt", (0.6, 0.8), 0.3), ("L08", "pain_haeldb", (0.7, 0.9), 0.3),
             ("G02", "de_orders", (1.0, 1.3), 0.3))
# Replacement takes, main reference, for rows the Whisper check left under three takes
# (2026-10-20: R03 t11/t12 lost "Ruhe", L04 t13 ran on): row -> how many; they reuse the
# middle and the low rung of the ladder with new seeds.
REPLACEMENT_TAKES = {"R03": 2, "L04": 1}
CROSS_LINGUAL_CFG = 0.0     # research §2: an English reference reading German, cfg 0 against the accent


def ref_of(line: Line) -> str:
    """The main reference of a round-2 line."""
    if line.delivery in ("pain", "death"):
        return "pain_kurt" if line.lang == "en" else "pain_haeldb"
    return "de_orders" if line.cls == "rifleman" else "en_orders"


def round2_lines() -> tuple[Line, ...]:
    """Every spoken line with no approved take (D91)."""
    return tuple(l for l in LINES if l.row not in APPROVED_ROWS)


def round2_takes() -> list[Take2]:
    out = []
    for l in round2_lines():
        exs, cfg, temp, _ = DELIVERY2[l.delivery]
        ref = ref_of(l)
        if REFS[ref].lang not in ("-", l.lang):
            cfg = CROSS_LINGUAL_CFG
        t = ROUND2_FIRST_TAKE
        for ex in exs:
            out.append(Take2(l, t, ref, ex, cfg, temp, TEXT2.get(l.text, l.text), l.lang))
            t += 1
        for row, alt, alt_exs, alt_cfg in ALT_TAKES:
            if row != l.row:
                continue
            for ex in alt_exs:
                c = alt_cfg if REFS[alt].lang in ("-", l.lang) else CROSS_LINGUAL_CFG
                out.append(Take2(l, t, alt, ex, c, temp, TEXT2.get(l.text, l.text), l.lang))
                t += 1
        for i in range(REPLACEMENT_TAKES.get(l.row, 0)):
            out.append(Take2(l, t, ref, (exs[1], exs[0])[i % 2], cfg, temp, TEXT2.get(l.text, l.text), l.lang))
            t += 1
    return out


# --- refs: cut, measure, register, upload ---

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def decode_mono(path: Path, rate: int = REF_SR) -> "np.ndarray":
    """ffmpeg -> float32 mono (channels averaged) at rate."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(rate),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def _frames(x: "np.ndarray", rate: int) -> tuple["np.ndarray", int]:
    n = max(1, int(round(0.01 * rate)))
    m = len(x) // n
    e = np.mean(x[:m * n].reshape(m, n) ** 2, axis=1) if m else np.zeros(0)
    return 10 * np.log10(np.maximum(e, 1e-12)), n


def tighten(x: "np.ndarray", rate: int = REF_SR) -> "np.ndarray":
    """Leading/trailing silence out, inner pauses longer than REF_MAX_PAUSE_S shortened to it."""
    db, n = _frames(x, rate)
    if db.size == 0:
        return x[:0]
    loud = db >= db.max() + REF_GATE_DB
    on = np.flatnonzero(loud)
    if on.size == 0:
        return x[:0]
    keep = np.zeros(db.size, dtype=bool)
    keep[on[0]:on[-1] + 1] = True
    cap = int(round(REF_MAX_PAUSE_S / 0.01))
    run = 0
    for i in range(on[0], on[-1] + 1):
        run = 0 if loud[i] else run + 1
        if run > cap:
            keep[i] = False
    idx = np.repeat(keep, n)
    y = x[:idx.size][idx]
    f = min(len(y) // 4, int(0.005 * rate))
    if f:
        y[:f] *= np.linspace(0, 1, f)
        y[-f:] *= np.linspace(1, 0, f)
    return y


def build_ref(ref: Ref, refs_dir: Path = REFS_DIR, rate: int = REF_SR) -> tuple["np.ndarray", list[dict]]:
    """-> (the reference, peak -2 dBFS; one dict per part with its measurements)."""
    gap = np.zeros(int(round(REF_GAP_S * rate)))
    pieces, info = [], []
    for path, a, b in ref.parts:
        x = decode_mono(refs_dir / path, rate)
        seg = x[int(a * rate): int(b * rate) if b else len(x)]
        y = tighten(seg, rate)
        pk = 20 * np.log10(np.max(np.abs(seg)) + 1e-12)
        info.append({"file": path, "start": a, "end": b, "seconds": round(len(y) / rate, 2),
                     "peak_dbfs": round(float(pk), 2)})
        pieces += [y, gap]
    x = np.concatenate(pieces[:-1])
    return x / np.max(np.abs(x)) * 10 ** (REF_PEAK_DBFS / 20), info


def wav16(x: "np.ndarray", rate: int = REF_SR) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.clip(np.round(x * 32767), -32767, 32767).astype("<i2").tobytes())
    return buf.getvalue()


def ref_filename(key: str, data: bytes) -> str:
    return f"sd_ref_{key}_{hashlib.sha256(data).hexdigest()[:8]}.wav"


def upload_reference(path: Path, server: str = SERVER) -> dict:
    boundary = "----sdref" + hashlib.sha256(path.name.encode()).hexdigest()[:16]
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(server + "/upload_reference", data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as r:
        return json.loads(r.read() or b"{}")


SOURCES_FIELDS = ("kind", "path", "sha256", "bytes", "licence", "author", "url", "note")


def sources_rows(built: dict[str, tuple[Path, list[dict]]], refs_dir: Path = REFS_DIR) -> list[dict]:
    rows = []
    for key, s in SOURCES.items():
        p = refs_dir / s.path
        rows.append({"kind": "download", "path": s.path, "sha256": sha256_of(p), "bytes": p.stat().st_size,
                     "licence": s.licence, "author": s.author, "url": s.url,
                     "note": s.title + (f"; credit: {s.credit}" if s.credit else "")})
    seen = set()
    for key, (wav, parts) in built.items():
        ref = REFS[key]
        src = SOURCES[ref.sources[0]]
        for part in parts:
            if part["file"] in seen or part["file"].endswith((".ogg",)):
                continue                       # the two kurt files are downloads, listed above
            seen.add(part["file"])
            p = refs_dir / part["file"]
            rows.append({"kind": "clip", "path": part["file"], "sha256": sha256_of(p), "bytes": p.stat().st_size,
                         "licence": src.licence, "author": src.author, "url": src.url,
                         "note": f"extracted from {src.path}; used in {key}"})
        rows.append({"kind": "reference", "path": wav.relative_to(refs_dir).as_posix(), "sha256": sha256_of(wav),
                     "bytes": wav.stat().st_size,
                     "licence": " + ".join(dict.fromkeys(SOURCES[s].licence for s in ref.sources)),
                     "author": SOURCES[ref.sources[0]].author, "url": SOURCES[ref.sources[0]].url,
                     "note": f"{key}: " + ", ".join(
                         f"{Path(q['file']).name}" + (f" {q['start']:g}-{q['end']:g} s" if q['end'] else "")
                         for q in parts)})
    return rows


def write_tsv(rows: list[dict], fields=SOURCES_FIELDS) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def ref_files(refs_dir: Path = REFS_DIR) -> dict[str, Path]:
    """REFS key -> its built WAV (the newest when a cut changed)."""
    out = {}
    for key in REFS:
        found = sorted(refs_dir.glob(f"sd_ref_{key}_*.wav"), key=lambda p: p.stat().st_mtime)
        if found:
            out[key] = found[-1]
    return out


def make_refs(refs_dir: Path = REFS_DIR, server: str | None = SERVER, log=print) -> dict[str, Path]:
    built = {}
    for key, ref in REFS.items():
        x, parts = build_ref(ref, refs_dir)
        data = wav16(x)
        wav = refs_dir / ref_filename(key, data)
        wav.write_bytes(data)
        s = len(x) / REF_SR
        lo, hi = REF_LEN_S
        log(f"  {wav.name}  {s:.2f} s  peak {20 * np.log10(np.max(np.abs(x))):.2f} dBFS"
            + ("" if lo <= s <= hi else f"  OUT OF {lo:g}-{hi:g} s"))
        for p in parts:
            if p["peak_dbfs"] > REF_CLIP_DBFS:
                log(f"    warning: {p['file']} {p['start']}-{p['end']} peaks at {p['peak_dbfs']} dBFS")
        built[key] = (wav, parts)
        if server:
            log(f"    upload: {upload_reference(wav, server)}")
    (refs_dir / SOURCES_TSV.name).write_text(write_tsv(sources_rows(built, refs_dir)), encoding="utf-8")
    (refs_dir / "REFS.json").write_text(json.dumps({k: {"file": w.name, "parts": p} for k, (w, p) in built.items()},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    return {k: w for k, (w, _) in built.items()}


# --- generate2 ---

def request_body2(t: Take2, ref_file: str) -> dict:
    return {"text": t.text, "voice_mode": "clone", "reference_audio_filename": ref_file,
            "output_format": "wav", "language": t.lang, "exaggeration": t.exaggeration,
            "cfg_weight": t.cfg_weight, "temperature": t.temperature, "seed": seed_of(t.line, t.take),
            "speed_factor": 1.0, "split_text": False}


# The fallback when the server cannot synthesise (2026-10-20: a runaway take overflowed
# S3Gen, a CUDA device-side assert left the server's GPU context unusable, and the server
# is not ours to restart). The same model through the chatterbox library, in the server's
# own Python, on the CPU (the GPU is held by the server), in a separate process. The speech
# tokens are capped so a runaway stops at LOCAL_MAX_TOKENS instead of overflowing.
CHATTERBOX_PY = Path("Z:/Chatterbox/Chatterbox-TTS-Server/python_embedded/python.exe")
CHATTERBOX_HF_HOME = Path("Z:/Chatterbox/hf_cache")
LOCAL_MAX_TOKENS = 300          # 25 tokens a second: 12 s, four times the longest line
LOCAL_SERVER_LABEL = "offline: chatterbox library in the server's Python, cpu, separate process"
LOCAL_MODEL_NAME = "ChatterboxMultilingualTTS (chatterbox-multilingual, 24 kHz, cpu, speech tokens capped at 300)"
LOCAL_WORKER = r"""
import json, os, random, sys, wave
import numpy as np, torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
cap = int(sys.argv[1])
m = ChatterboxMultilingualTTS.from_pretrained(device=torch.device("cpu"))
inference = m.t3.inference
def capped(*a, **k):
    k["max_new_tokens"] = min(int(k.get("max_new_tokens", cap)), cap)
    return inference(*a, **k)
m.t3.inference = capped
print(json.dumps({"ready": True}), flush=True)
for raw in sys.stdin:
    job = json.loads(raw)
    try:
        s = int(job["seed"])
        torch.manual_seed(s); random.seed(s); np.random.seed(s)   # the server's set_seed, cpu
        w = m.generate(job["text"], language_id=job["language"], audio_prompt_path=job["ref"],
                       exaggeration=job["exaggeration"], cfg_weight=job["cfg_weight"],
                       temperature=job["temperature"])
        x = np.clip(w.squeeze(0).numpy(), -1, 1)
        with wave.open(job["out"], "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(m.sr)
            f.writeframes((x * 32767).astype("<i2").tobytes())
        print(json.dumps({"ok": job["out"]}), flush=True)
    except Exception as e:
        print(json.dumps({"error": repr(e)}), flush=True)
"""


class LocalPoster:
    """A poster for generate2 that runs the model in a worker process (see LOCAL_WORKER)."""

    def __init__(self, refs_dir: Path = REFS_DIR, tmp_dir: Path = AGGR_RAW_DIR):
        env = dict(os.environ, HF_HOME=str(CHATTERBOX_HF_HOME), HF_HUB_OFFLINE="1", PYTHONIOENCODING="utf-8")
        self.refs_dir, self.tmp = refs_dir, tmp_dir / "_local.wav"
        self.p = subprocess.Popen([str(CHATTERBOX_PY), "-c", LOCAL_WORKER, str(LOCAL_MAX_TOKENS)],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
                                  encoding="utf-8", errors="replace")
        self._read()

    def _read(self) -> dict:
        while True:
            out = self.p.stdout.readline()
            if not out:
                raise RuntimeError("the chatterbox worker stopped")
            if out.startswith("{"):
                return json.loads(out)

    def __call__(self, body: dict, server: str = "") -> bytes:
        job = dict(body, ref=str(self.refs_dir / body["reference_audio_filename"]), out=str(self.tmp))
        self.p.stdin.write(json.dumps(job, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        r = self._read()
        if "error" in r:
            raise RuntimeError(r["error"])
        data = self.tmp.read_bytes()
        self.tmp.unlink()
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=60)


def generate2(day: str, refs: dict[str, Path], raw_dir: Path = AGGR_RAW_DIR, server: str = SERVER,
              rows=None, poster=post_tts, log=print, model: str = MODEL_NAME,
              endpoint: str = "/tts") -> list[Path]:
    """One request per take and per line (never several lines in one text). Kept takes stay."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for t in round2_takes():
        if rows and t.line.row not in rows:
            continue
        name = take_name(t.line, t.take, day)
        wav = raw_dir / f"{name}.wav"
        if wav.is_file():
            continue
        ref = refs[t.ref]
        body = request_body2(t, ref.name)
        try:
            data = poster(body, server)
        except Exception as e:  # one failed take must not stop the others; it is logged and skipped
            log(f"  {name}  FAILED: {e}")
            continue
        wav.write_bytes(data)
        r = REFS[t.ref]
        (raw_dir / f"{name}.json").write_text(json.dumps(
            {"file": wav.name, "date": f"{day[:4]}-{day[4:6]}-{day[6:]}", "server": server,
             "endpoint": endpoint, "model": model, "request": body,
             "reference": {"key": t.ref, "file": ref.name, "sha256": sha256_of(ref),
                           "sources": [{"title": SOURCES[s].title, "author": SOURCES[s].author,
                                        "licence": SOURCES[s].licence, "url": SOURCES[s].url,
                                        "credit": SOURCES[s].credit} for s in r.sources]}},
            ensure_ascii=False, indent=1), encoding="utf-8")
        made.append(wav)
        log(f"  {name}  {t.ref}  ex {t.exaggeration}  cfg {t.cfg_weight}  {len(data)} bytes")
    return made


# --- process2 and the Whisper check ---

DIGITS = {"4": "four"}


def words_of(s: str) -> list[str]:
    s = s.lower().replace("…", " ").replace("...", " ")
    return [DIGITS.get(w, w) for w in re.findall(r"[a-zäöüß0-9']+", s)]


INTERJECTION_RE = re.compile(r"^(a+h*|o+h*|u+h*|m+h*|h+m+|a+r+g+h*|u+g+h+|au+|e+h+|ä+h+)$")
JOINED_MATCH = 0.8              # Whisper glues ("dahinten") or splits ("Come in") words


def asr_check(heard: str | None, text: str, cries_ok: bool = False) -> tuple[str, str]:
    """-> ("ok" | "warn" | "reject", reason in Spanish). Words only; punctuation is not judged.

    Rejected: nothing heard, extra words (the model kept talking or mixed lines in) or fewer
    words (the line was cut). Same count but a different word is only a warning: Whisper
    mishears one-word shouts (round 1 heard "Feind" as "Bye") and the ear decides. On pain
    and death lines (cries_ok) a cry ("Ahhh", "Mmh") is the delivery, not an extra word.
    """
    if heard is None:
        return "ok", ""
    got, want = words_of(heard), words_of(text)
    if cries_ok:
        got = [w for w in got if not INTERJECTION_RE.match(w)]
    g, w = "".join(got), "".join(want)
    if got and len(g) <= len(w) + 1 and SequenceMatcher(None, g, w).ratio() >= JOINED_MATCH:
        return "ok", ""             # glued or split words ("dahinten", "Come in" for "Command")
    if not got:
        return ("warn", "Whisper solo oyó un grito") if cries_ok and words_of(heard) else             ("reject", "Whisper no oyó ninguna palabra")
    if len(got) > len(want):
        return "reject", f"palabras de más ({len(got)} en vez de {len(want)})"
    if len(got) < len(want):
        return "reject", f"frase cortada ({len(got)} de {len(want)} palabras)"
    off = [g for g, w in zip(got, want) if SequenceMatcher(None, g, w).ratio() < 0.5]
    return ("warn", "Whisper oyó otra palabra") if off else ("ok", "")


def process2(day: str, raw_dir: Path = AGGR_RAW_DIR, out_dir: Path = AGGR_DIR, log=print) -> list[Processed]:
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for t in round2_takes():
        name = take_name(t.line, t.take, day)
        wav = raw_dir / f"{name}.wav"
        if not wav.is_file():
            continue
        x = gws.decode(wav)
        y, cut, drive = process_wave(x, t.line)
        (out_dir / f"{name}.ogg").write_bytes(gws.ogg_bytes(gws.wav_bytes(y)))
        done.append(Processed(name, t.line, y, len(x) / gws.SR, cut, drive))
        log(f"  {name}  {len(y) / gws.SR:.2f} s  drive {drive:.2f}  cut {cut:.2f} s")
    return done


# --- the round-2 page ---

def page2_items(done: list[Processed], page: Path, day: str, asr: dict | None = None,
                refs: dict[str, Path] | None = None) -> list[dict]:
    asr = asr or {}
    refs = refs or {}
    items = page_items(done, page, AGGR_DIR, AGGR_RAW_DIR, asr)
    by_name = {take_name(t.line, t.take, day): t for t in round2_takes()}
    for it in items:
        t = by_name[it["id"]]
        d = DELIVERY2[t.line.delivery]
        it["ref"] = REFS[t.ref].label
        it["refKey"] = t.ref
        it["voice"] = "clon de referencia agresiva"
        it["set"] = (f"exaggeration {t.exaggeration:g} · cfg {t.cfg_weight:g} · temperatura {t.temperature:g}"
                     f" ({d[3]}) · texto «{t.text}»")
        verdict, why = asr_check(it["asr"], t.text, cries_ok=t.line.delivery in ("pain", "death"))
        it["verdict"], it["why"] = verdict, why
        it["asrWarn"] = why if verdict == "warn" else ""
    return items


def approved_items(page: Path, out_dir: Path = OUT_DIR) -> list[dict]:
    out = []
    for n in APPROVED:
        l = line_of(n)
        out.append({"id": n, "row": l.row, "text": l.text, "tr": l.translation, "voice": CAST[l.cls].name,
                    "src": _rel(out_dir / f"{n}.ogg", page)})
    return out


def refs_table_html(page: Path, refs: dict[str, Path]) -> str:
    rows = []
    for key, r in REFS.items():
        wav = refs.get(key)
        player = (f'<audio controls preload="none" src="{html.escape(_rel(wav, page))}"></audio>'
                  if wav else "—")
        secs = f"{len(decode_mono(wav)) / REF_SR:.1f} s" if wav and np is not None else "—"
        used = ", ".join(sorted({t.line.row for t in round2_takes() if t.ref == key}))
        lic = " · ".join(dict.fromkeys(f"{SOURCES[s].licence} — {SOURCES[s].author}" for s in r.sources))
        rows.append(f"<tr><td><b>{html.escape(r.label)}</b><br><span class=\"meta\">{html.escape(r.why)}</span></td>"
                    f"<td>{secs}</td><td>{html.escape(lic)}</td><td>{html.escape(used)}</td><td>{player}</td></tr>")
    return ("<table class=\"castt\"><thead><tr><th>Referencia</th><th>Duración</th><th>Licencia</th>"
            "<th>Frases</th><th>Escuchar</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


def static_rows_html(items: list[dict], title: str, note: str, key: str) -> str:
    if not items:
        return ""
    body = "".join(
        f'<div class="pl"><span><code>{html.escape(i["id"])}</code> «{html.escape(i["text"])}»'
        + (f' <span class="warn">{html.escape(i.get(key, ""))}</span>' if i.get(key) else "")
        + (f' · Whisper: «{html.escape(i["asr"])}»' if i.get("asr") else "")
        + (f' · {html.escape(i["ref"])}' if i.get("ref") else "")
        + f'</span><audio controls preload="none" src="{html.escape(i["src"])}"></audio></div>'
        for i in items)
    return (f'<details class="grp"{" open" if key == "" else ""}><summary>{html.escape(title)} '
            f'<span class="gcount">{len(items)}</span></summary><p class="meta">{html.escape(note)}</p>'
            f'<div class="line">{body}</div></details>')


def page2_html(done: list[Processed], page: Path, stamp: str, day: str, asr: dict | None = None,
               refs: dict[str, Path] | None = None) -> str:
    refs = refs or {}
    items = page2_items(done, page, day, asr, refs)
    keep = [i for i in items if i["verdict"] != "reject"]
    rejected = [i for i in items if i["verdict"] == "reject"]
    asr_model = next((v.get("model") for v in (asr or {}).values()), None)
    lines = round2_lines()
    data = json.dumps(keep, ensure_ascii=False).replace("</", "<\\/")
    classes = json.dumps(CLASS_LABEL, ensure_ascii=False)
    js = PAGE_JS.replace("__KEY__", PAGE_KEY_PREFIX + "aggr-" + stamp).replace("__STAMP__", stamp + ", referencias agresivas")
    credits = sorted({SOURCES[s].credit for r in REFS.values() for s in r.sources if SOURCES[s].credit})
    approved = static_rows_html(approved_items(page), "Ya aprobadas (D91), sin tocar: para comparar",
                                "Las 7 tomas que dijiste OK en la ronda anterior (voces predefinidas). No se votan aquí.", "")
    rej = static_rows_html(rejected, "Rechazadas automáticamente",
                           "Whisper oyó palabras de más, la frase cortada o nada. "
                           "No se votan; están por si quieres oírlas.", "why")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voces agresivas</title>
<style>{wa.PAGE_CSS}{PAGE_CSS_EXTRA}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Voces de enemigos: referencias agresivas</h1>
  <span class="prog">Juzgadas <b id="pDone">0</b> de <b>{len(keep)}</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> solo sin juzgar</label>
  <button class="primary" id="copyTop">Copiar resultado</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>Segunda ronda tras D91. Chatterbox copia la emoción del clip de referencia, así que esta vez cada voz se <b>clona de grabaciones gritadas</b> con licencia libre, en vez de las voces predefinidas (que son narración tranquila). Son las <b>{len(lines)} frases sin ninguna toma aprobada</b> ({html.escape(", ".join(l.row for l in lines))}), <b>una petición por toma y por frase</b> (nunca varias frases juntas), tomas <b>11 en adelante</b> para no confundirlas con la ronda anterior. Pulsa <b>OK</b>, <b>NO</b> o <b>?</b> y luego <b>Copiar resultado</b>. Nada entra en el juego hasta que lo apruebes.</p>
  {refs_table_html(page, refs)}
  <ul>
    <li><b>Qué referencia lleva cada frase:</b> el Fusilero del Reich, la de Thorsten (alemán); la Legión y el General, la de kurt (inglés; en «Vorwärts» el inglés lee alemán con cfg 0 para que no se pegue el acento, y dos tomas más con Thorsten); dolor y muerte, la de dolor (HaelDB sin palabras para «Sani…», kurt herido para «I'm hit!», y dos tomas de cada una con la otra).</li>
    <li><b>Ajustes:</b> tres semillas por frase con la exageración en escalera (los gritos 1,1 / 1,3 / 1,5; las órdenes 0,9-1,4; el dolor y la muerte más bajos, porque lo pone la referencia). Las órdenes se envían con «!» (mismas palabras del guion).</li>
    <li><b>Dónde se generó:</b> las primeras tomas en el servidor de Chatterbox (GPU); una toma de «Sani…» se desbocó, desbordó el modelo y dejó el servidor sin poder sintetizar, así que el resto salió del <b>mismo modelo</b> con la librería de Chatterbox en el procesador (CPU), con un tope de 12 s por toma. Cada toma dice cuál en <code>AI-LOG.csv</code>. Puede haber diferencias mínimas de timbre entre ambas.</li>
    <li><b>Procesado:</b> igual que la ronda anterior: silencio recortado, graves a {HIGH_PASS_HZ:.0f} Hz, color de radio suave en la Legión y el volumen del sonido de Freedoom que sustituiría.</li>
    <li><b>Nadie ha escuchado las referencias aquí:</b> las elegí midiendo (tono, brillo, picos sin saturar) y con lo que transcribió Whisper. Thorsten es enfado leído, no gritos de batalla: si el alemán sigue sonando educado, el arreglo real sigue siendo D85 (tus gritos).</li>
    {f'<li><b>Whisper entendió:</b> transcripción automática con <code>{html.escape(asr_model)}</code>. Una toma con palabras de más o con la frase cortada se rechaza sola (abajo); si oyó otra palabra solo se avisa: tu oído manda.</li>' if asr_model else ''}
    <li><b>Créditos que exigen las referencias:</b> {html.escape(" / ".join(credits) or "—")}. Registro por toma en <code>work/audio/voice_takes/AI-LOG.csv</code>; huellas SHA-256 y licencias en <code>work/audio/voice_refs/SOURCES.tsv</code>.</li>
  </ul>
</section>
{approved}
<main id="groups"></main>
{rej}
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Resultado para pegar en el chat</h2>
  <p class="meta">Se actualiza solo. Si el botón no copia (algunos navegadores lo bloquean en archivos locales), selecciona el texto y Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copiar resultado</button> <button id="reset">Borrar todas mis respuestas</button></p>
</section>
<footer>Generado {html.escape(stamp)} por sound-designer con <code>tools/audio/process_voice_takes.py</code> (refs, generate2, process2). Audio: <code>work/audio/voice_takes/aggressive/</code> (procesadas), <code>…/aggressive/raw/</code> (tal como salieron), <code>work/audio/voice_refs/</code> (referencias, no van a git). La página lee los archivos del repo por ruta relativa: no la muevas de <code>docs/art/previews/</code>.</footer>
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
    ap.add_argument("command", choices=("generate", "process", "list", "refs", "generate2", "process2"))
    ap.add_argument("--date", default=_date.today().strftime("%Y%m%d"), help="YYYYMMDD in the file names")
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--rows", nargs="*", help="only these rows (R04 L04 ...)")
    ap.add_argument("--page", type=Path, help="write the listening page here (process)")
    ap.add_argument("--stamp", help="the page's stamp (default: from the page name)")
    ap.add_argument("--no-upload", action="store_true", help="refs: build only, do not upload")
    ap.add_argument("--local", action="store_true",
                    help="generate2: the chatterbox library on the CPU instead of the server (LocalPoster)")
    a = ap.parse_args(argv)
    if a.command == "list":
        for l in LINES:
            print(f"{l.row} {l.lump} {l.lang} {CAST[l.cls].name:7s} {l.delivery:5s} {l.freedoom:9s} {l.text}")
        return 0
    if a.command == "refs":
        make_refs(server=None if a.no_upload else a.server)
        print(f"references and {SOURCES_TSV.name} in {REFS_DIR}")
        return 0
    if a.command == "generate2" and a.local:
        poster = LocalPoster()
        try:
            made = generate2(a.date, ref_files(), server=LOCAL_SERVER_LABEL, rows=a.rows, poster=poster,
                             model=LOCAL_MODEL_NAME, endpoint="ChatterboxMultilingualTTS.generate")
        finally:
            poster.close()
        print(f"{len(made)} new takes in {AGGR_RAW_DIR}")
    elif a.command == "generate2":
        made = generate2(a.date, ref_files(), server=a.server, rows=a.rows)
        print(f"{len(made)} new takes in {AGGR_RAW_DIR}")
    elif a.command == "process2":
        done = process2(a.date)
        (AGGR_DIR / "MANIFEST.txt").write_text(manifest_text(done), encoding="utf-8")
        print(f"{len(done)} takes processed into {AGGR_DIR}")
        if a.page:
            page = a.page if a.page.is_absolute() else PROJECT_ROOT / a.page
            stamp = a.stamp or page.stem.split("_P2")[0]
            page.write_text(page2_html(done, page, stamp, a.date, asr=load_asr(AGGR_ASR_PATH), refs=ref_files()),
                            encoding="utf-8")
            print(f"page: {page}")
    elif a.command == "generate":
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
    (OUT_DIR / "AI-LOG.csv").write_text(log_csv(log_rows() + log_rows(AGGR_RAW_DIR)), encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
