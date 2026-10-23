#!/usr/bin/env python3
"""V3 B5: propaganda radio drafts (Chatterbox, Russian). NOT INSTALLED: the CEO listens first.

Sixteen short 1970s Radio-Moscow-style lines in Russian, two announcers:
  M = male, cloned from Thorsten Müller's *neutral* read speech (Thorsten-Voice
      emotional v02, CC0 1.0, https://zenodo.org/records/5525023). The archive was
      already on disk (work/audio/voice_refs/thorsten/, downloaded for D96); only its
      neutral/ folder is unpacked into src/. Nothing is downloaded.
  F = female, Chatterbox-TTS-Server's predefined voice Elena.wav (the D87 route:
      predefined voices shipped with the server, origin not documented, R1). There is
      no CC0/CC-BY female voice on disk and no download permission: flagged for the CEO.

Generation: the chatterbox library in the server's own Python, in a worker process,
GPU first (CPU if CUDA fails), special speech tokens >= 6561 dropped before S3Gen (the
gen_p2.py filter), token cap 400 (16 s). The Russian text is sent with hand-placed stress
marks (U+0301): the model's own stresser package is not installed and nothing may be
downloaded; the vocabulary has the mark, which is what the stresser would have added.

Processing: period radio. Band 300-3400 Hz (4th order), tanh saturation, a small
speaker resonance, valve hum + hiss + sparse crackle, a slow fade wobble, a short
tune-in (static and a heterodyne whistle) before the voice. The station jingle is our
own synthesis (original bell motifs, NOT the real interval signal of Radio Moscow,
which is a protected song) and is rendered separately; so is the 6-pip time signal.

    .venv/Scripts/python.exe -I work/audio/candidates/radio/gen_radio.py ref
    .venv/Scripts/python.exe -I work/audio/candidates/radio/gen_radio.py generate
    .venv/Scripts/python.exe -I work/audio/candidates/radio/gen_radio.py process
    .venv/Scripts/python.exe -I work/audio/candidates/radio/gen_radio.py page
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "audio"))
import numpy as np  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")
import process_voice_takes as pvt  # noqa: E402
import gen_weapon_sfx as gws  # noqa: E402
import gen_weapon_alts as wa  # noqa: E402

RAW = HERE / "raw"
OUT = HERE                      # processed OGGs next to this file
REF_DIR = HERE / "ref"
SRC = HERE / "src"
PAGE = ROOT / "work" / "audio" / "preview" / "radio_listening.html"
DAY = "20261023"
SR = gws.SR                     # 44100: gws.filt works at this rate

THORSTEN_NEUTRAL = "thorsten-emotional_v02/neutral/"
THORSTEN_META = SRC / "thorsten-emotional_v02" / "thorsten-emotional-metadata.csv"
ELENA = Path("Z:/Chatterbox/Chatterbox-TTS-Server/voices/Elena.wav")

pvt.SOURCES["thorsten_neutral"] = pvt.Source(
    "thorsten/thorsten-emotional_v02.tgz", "Thorsten-Voice Dataset 2021.06 emotional v02, style neutral",
    "Thorsten Müller (voice), Dominik Kreutz (audio)", "CC0 1.0", "https://zenodo.org/records/5525023", "")

VOICE = {
    "M": {"label": "Locutor (hombre): clon de Thorsten Müller, lectura neutra (alemán, CC0 1.0)",
          "lic": "CC0 1.0, Thorsten Müller (voz) y Dominik Kreutz (audio), https://zenodo.org/records/5525023"},
    "F": {"label": "Locutora (mujer): voz predefinida «Elena» de Chatterbox-TTS-Server (inglés)",
          "lic": "voz predefinida del servidor, origen no documentado (la vía de D87, R1); "
                 "no hay voz femenina CC0/CC-BY en disco y no hay permiso de descarga: decide el CEO"},
}


@dataclass(frozen=True)
class Line:
    n: int
    voice: str          # "M" / "F"
    kind: str           # Spanish
    ru: str             # as shown
    ru_stress: str      # as sent: ' after the stressed vowel becomes U+0301
    en: str
    es: str

    @property
    def code(self) -> str:
        return f"RAD{self.n:02d}"

    @property
    def lump(self) -> str:
        return f"SDRAD{self.n:02d}"

    def sent(self) -> str:
        return self.ru_stress.replace("'", "\u0301")


LINES: tuple[Line, ...] = (
    Line(1, "M", "parte de guerra",
         "Передаём сводку с фронта. Наши части отбросили захватчиков за Уральский хребет.",
         "Передаём сво'дку с фро'нта. На'ши ча'сти отбро'сили захва'тчиков за Ура'льский хребе'т.",
         "Here is the report from the front. Our units have driven the invaders back beyond the Ural range.",
         "Transmitimos el parte del frente. Nuestras unidades han rechazado a los invasores más allá de los Urales."),
    Line(2, "M", "parte de guerra",
         "На Волге, у Жигулёвской плотины, наши части уничтожили крупную группировку противника.",
         "На Во'лге, у Жигулёвской плоти'ны, на'ши ча'сти уничто'жили кру'пную группиро'вку проти'вника.",
         "On the Volga, at the Zhiguli dam, our units have destroyed a large enemy force.",
         "En el Volga, junto a la presa de Zhiguli, nuestras unidades han destruido una gran agrupación enemiga."),
    Line(3, "F", "defensa civil",
         "Внимание, граждане! Объявлена воздушная тревога. Немедленно пройдите в ближайшее убежище.",
         "Внима'ние, гра'ждане! Объя'влена возду'шная трево'га. Неме'дленно пройди'те в ближа'йшее убе'жище.",
         "Attention, citizens! An air-raid alert has been declared. Go to the nearest shelter at once.",
         "¡Atención, ciudadanos! Se ha declarado la alerta aérea. Diríjanse de inmediato al refugio más cercano."),
    Line(4, "F", "defensa civil",
         "Не подходите к упавшим предметам. О любых находках сообщайте в штаб гражданской обороны.",
         "Не подходи'те к упа'вшим предме'там. О любы'х нахо'дках сообща'йте в штаб гражда'нской оборо'ны.",
         "Do not approach fallen objects. Report any finds to the civil defence headquarters.",
         "No se acerquen a los objetos caídos. Comuniquen cualquier hallazgo al cuartel de defensa civil."),
    Line(5, "M", "consigna",
         "Враг силён, но народ сильнее. Все на защиту Родины!",
         "Враг силён, но наро'д сильне'е. Все на защи'ту Ро'дины!",
         "The enemy is strong, but the people are stronger. Everyone to the defence of the Motherland!",
         "El enemigo es fuerte, pero el pueblo lo es más. ¡Todos a defender la Patria!"),
    Line(6, "F", "consigna",
         "Товарищи рабочие! План пятилетки будет выполнен — несмотря ни на что.",
         "Това'рищи рабо'чие! План пятиле'тки бу'дет вы'полнен — несмотря' ни на что'.",
         "Comrade workers! The five-year plan will be fulfilled, whatever happens.",
         "¡Camaradas obreros! El plan quinquenal se cumplirá, pase lo que pase."),
    Line(7, "M", "consigna",
         "Захватчики воюют за прибыль. Мы воюем за всех.",
         "Захва'тчики вою'ют за при'быль. Мы вою'ем за всех.",
         "The invaders fight for profit. We fight for everyone.",
         "Los invasores luchan por el beneficio. Nosotros luchamos por todos."),
    Line(8, "F", "defensa civil, irónica",
         "Сообщение гражданской обороны: водопроводная вода безопасна. Перед употреблением кипятить сорок минут.",
         "Сообще'ние гражда'нской оборо'ны: водопрово'дная вода' безопа'сна. Пе'ред употребле'нием кипяти'ть со'рок мину'т.",
         "A civil defence announcement: tap water is safe. Boil for forty minutes before use.",
         "Aviso de la defensa civil: el agua del grifo es segura. Hiérvase cuarenta minutos antes de consumirla."),
    Line(9, "M", "noticia, irónica",
         "Парад в честь шестидесятой годовщины Великого Октября состоится в назначенный срок. Парад не отменяется.",
         "Пара'д в честь шестидеся'той годовщи'ны Вели'кого Октября' состои'тся в назна'ченный срок. Пара'д не отменя'ется.",
         "The parade for the sixtieth anniversary of the Great October will take place as scheduled. The parade is not cancelled.",
         "El desfile del sexagésimo aniversario de la Gran Revolución de Octubre se celebrará en la fecha prevista. El desfile no se suspende."),
    Line(10, "F", "parte meteorológico, irónico",
         "Прогноз погоды. На Урале облачно, местами осадки. Местами — падение посторонних предметов с неба.",
         "Прогно'з пого'ды. На Ура'ле о'блачно, места'ми оса'дки. Места'ми — паде'ние посторо'нних предме'тов с не'ба.",
         "The weather forecast. Cloudy over the Urals, with rain in places. In places, foreign objects falling from the sky.",
         "El parte del tiempo. Nuboso en los Urales, con precipitaciones locales. Localmente, caída de objetos extraños del cielo."),
    Line(11, "M", "parte de guerra",
         "Гарнизон космодрома «Заря-7» продолжает удерживать позиции. Слава его защитникам!",
         "Гарнизо'н космодро'ма «Заря'-Семь» продолжа'ет уде'рживать пози'ции. Сла'ва его' защи'тникам!",
         "The garrison of the Zarya-7 cosmodrome is still holding its positions. Glory to its defenders!",
         "La guarnición del cosmódromo Zariá-7 sigue manteniendo sus posiciones. ¡Gloria a sus defensores!"),
    Line(12, "F", "defensa civil, irónica",
         "Если вы встретили существо в каске, не вступайте с ним в разговор. Сообщите в милицию.",
         "Е'сли вы встре'тили существо' в ка'ске, не вступа'йте с ним в разгово'р. Сообщи'те в мили'цию.",
         "If you meet a creature wearing a helmet, do not enter into conversation with it. Inform the militia.",
         "Si se encuentra con una criatura con casco, no entable conversación con ella. Avise a la milicia."),
    Line(13, "M", "consigna",
         "Каждый завод — крепость. Каждый дом — рубеж обороны.",
         "Ка'ждый заво'д — кре'пость. Ка'ждый дом — рубе'ж оборо'ны.",
         "Every factory a fortress. Every house a line of defence.",
         "Cada fábrica, una fortaleza. Cada casa, una línea de defensa."),
    Line(14, "F", "llamamiento",
         "Товарищи! Фронту нужна ваша кровь. Пункты сдачи крови работают круглосуточно.",
         "Това'рищи! Фро'нту нужна' ва'ша кровь. Пу'нкты сда'чи кро'ви рабо'тают круглосу'точно.",
         "Comrades! The front needs your blood. Blood donation points are open around the clock.",
         "¡Camaradas! El frente necesita vuestra sangre. Los puntos de donación funcionan las veinticuatro horas."),
    Line(15, "M", "noticia",
         "Танкоград выполнил месячный план за одну ночь. Новые машины уже на фронте.",
         "Танкогра'д вы'полнил ме'сячный план за одну' ночь. Но'вые маши'ны уже' на фро'нте.",
         "Tankograd fulfilled its monthly plan in a single night. The new machines are already at the front.",
         "Tankogrado ha cumplido el plan mensual en una sola noche. Las nuevas máquinas ya están en el frente."),
    Line(16, "M", "señal horaria",
         "Московское время — двадцать часов. Передаём последние известия.",
         "Моско'вское вре'мя — два'дцать часо'в. Передаём после'дние изве'стия.",
         "Moscow time: twenty hundred hours. Here is the latest news.",
         "Hora de Moscú: las veinte horas. Transmitimos las últimas noticias."),
)

# (take, exaggeration, cfg_weight, temperature). cfg 0 is research §2's cure for a
# cross-lingual accent (neither reference is Russian); 0.3-0.5 keeps the pacing.
TAKES = ((1, 0.5, 0.5, 0.7), (2, 0.6, 0.3, 0.75), (3, 0.45, 0.0, 0.7))
MAX_TOKENS = 400
SEED_BASE = 77000


def name_of(line: Line, take: int) -> str:
    return f"{line.code}_{line.lump}_ai_chatterbox_{DAY}_t{take:02d}"


def seed_of(line: Line, take: int) -> int:
    return SEED_BASE + 10 * line.n + take


VOWELS = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")


def expected_s(line: Line) -> float:
    """Announcer pace: ~5.2 syllables a second, plus a breath at each stop or dash."""
    syl = sum(c in VOWELS for c in line.ru)
    stops = len(re.findall(r"[.!?:—]", line.ru))
    return syl / 5.2 + 0.32 * stops


# ---------------------------------------------------------------- reference

def build_ref() -> Path:
    REF_DIR.mkdir(parents=True, exist_ok=True)
    meta = {}
    for row in THORSTEN_META.read_text(encoding="utf-8").splitlines():
        if "|" in row:
            k, t = row.split("|", 1)
            meta[k] = t.strip()
    cands = []
    for k, t in meta.items():
        p = SRC / THORSTEN_NEUTRAL / f"{k}.wav"
        if not p.is_file() or not t.endswith("."):          # statements, not questions or cries
            continue
        x = pvt.decode_mono(p, pvt.REF_SR)
        pk = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        if pk > pvt.REF_CLIP_DBFS:
            continue
        cands.append((len(x) / pvt.REF_SR, k, t))
    cands.sort(reverse=True)                                   # long, calm sentences first
    picked, total = [], 0.0
    for dur, k, t in cands:
        if total >= 14.0:
            break
        picked.append((k, t))
        total += dur + pvt.REF_GAP_S
    ref = pvt.Ref("radio_m_thorsten_neutral", ("thorsten_neutral",), "de",
                  tuple((THORSTEN_NEUTRAL + f"{k}.wav", 0, 0) for k, _ in picked),
                  VOICE["M"]["label"], "las frases neutras más largas del conjunto (afirmaciones, no preguntas)")
    x, parts = pvt.build_ref(ref, SRC)
    data = pvt.wav16(x)
    wav = REF_DIR / pvt.ref_filename(ref.key, data)
    for old in REF_DIR.glob("sd_ref_radio_m_*.wav"):
        old.unlink()
    wav.write_bytes(data)
    shutil.copyfile(ELENA, REF_DIR / "Elena.wav")
    rows = [{"file": p["file"], "text": t, "seconds": p["seconds"], "peak_dbfs": p["peak_dbfs"],
             "sha256": pvt.sha256_of(SRC / p["file"])} for p, (_, t) in zip(parts, picked)]
    (REF_DIR / "REF.json").write_text(json.dumps({
        "M": {"file": wav.name, "sha256": pvt.sha256_of(wav), "seconds": round(len(x) / pvt.REF_SR, 2),
              "source": {"title": pvt.SOURCES["thorsten_neutral"].title, "author": pvt.SOURCES["thorsten_neutral"].author,
                         "licence": "CC0 1.0", "url": "https://zenodo.org/records/5525023",
                         "archive_on_disk": "work/audio/voice_refs/thorsten/thorsten-emotional_v02.tgz (D96 download)"},
              "parts": rows},
        "F": {"file": "Elena.wav", "sha256": pvt.sha256_of(ELENA), "copied_from": str(ELENA),
              "source": "predefined voice shipped with Chatterbox-TTS-Server 2.0.2, origin not documented (D87, R1)"},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{wav.name}  {len(x) / pvt.REF_SR:.2f} s  {len(parts)} clips")
    for p, (_, t) in zip(parts, picked):
        print(f"   {p['seconds']:5.2f} s  {t}")
    return wav


def ref_m() -> Path:
    found = sorted(REF_DIR.glob("sd_ref_radio_m_*.wav"))
    if not found:
        raise SystemExit("no reference: run `ref` first")
    return found[-1]


def ref_for(line: Line) -> Path:
    return ref_m() if line.voice == "M" else REF_DIR / "Elena.wav"


# ---------------------------------------------------------------- generation

WORKER = r"""
import json, random, sys, wave
import numpy as np, torch
import chatterbox.mtl_tts as _mt
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
_orig_drop = _mt.drop_invalid_tokens
def _drop(x):
    y = _orig_drop(x)
    return y[y < 6561]
_mt.drop_invalid_tokens = _drop
cap = int(sys.argv[1]); want = sys.argv[2]
dev = "cpu"
if want == "cuda":
    try:
        m = ChatterboxMultilingualTTS.from_pretrained(device=torch.device("cuda")); dev = "cuda"
    except Exception as e:
        print(json.dumps({"note": "cuda failed: " + repr(e)}), flush=True); m = None
if dev == "cpu":
    m = ChatterboxMultilingualTTS.from_pretrained(device=torch.device("cpu"))
inference = m.t3.inference
def capped(*a, **k):
    k["max_new_tokens"] = min(int(k.get("max_new_tokens", cap)), cap)
    return inference(*a, **k)
m.t3.inference = capped
print(json.dumps({"ready": True, "device": dev}), flush=True)
for raw in sys.stdin:
    job = json.loads(raw)
    try:
        s = int(job["seed"])
        torch.manual_seed(s); random.seed(s); np.random.seed(s)
        w = m.generate(job["text"], language_id=job["language"], audio_prompt_path=job["ref"],
                       exaggeration=job["exaggeration"], cfg_weight=job["cfg_weight"],
                       temperature=job["temperature"])
        x = np.clip(w.squeeze(0).cpu().numpy(), -1, 1)
        with wave.open(job["out"], "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(m.sr)
            f.writeframes((x * 32767).astype("<i2").tobytes())
        print(json.dumps({"ok": job["out"], "device": dev}), flush=True)
    except Exception as e:
        print(json.dumps({"error": repr(e)}), flush=True)
"""


class Worker:
    def __init__(self, device: str = "cuda"):
        env = dict(os.environ, HF_HOME=str(pvt.CHATTERBOX_HF_HOME), HF_HUB_OFFLINE="1", PYTHONIOENCODING="utf-8")
        self.tmp = RAW / "_local.wav"
        self.p = subprocess.Popen([str(pvt.CHATTERBOX_PY), "-c", WORKER, str(MAX_TOKENS), device],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
                                  encoding="utf-8", errors="replace")
        r = self._read()
        self.device = r.get("device", "?")

    def _read(self) -> dict:
        while True:
            out = self.p.stdout.readline()
            if not out:
                raise RuntimeError("the chatterbox worker stopped")
            if out.startswith("{"):
                r = json.loads(out)
                if "note" in r:
                    print("  worker:", r["note"], flush=True)
                    continue
                return r

    def __call__(self, job: dict) -> bytes:
        job = dict(job, out=str(self.tmp))
        self.p.stdin.write(json.dumps(job, ensure_ascii=True) + "\n")   # ASCII: no pipe encoding can mangle it
        self.p.stdin.flush()
        r = self._read()
        if "error" in r:
            raise RuntimeError(r["error"])
        data = self.tmp.read_bytes()
        self.tmp.unlink()
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=120)


def model_label(device: str) -> str:
    return (f"ChatterboxMultilingualTTS (chatterbox-multilingual, 24 kHz, {device}, speech tokens capped at "
            f"{MAX_TOKENS}, special tokens >= 6561 dropped before S3Gen)")


def generate(only=None) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    todo = [(l, t) for l in LINES for t in TAKES
            if (not only or l.code in only) and not (RAW / f"{name_of(l, t[0])}.wav").is_file()]
    if not todo:
        print("nothing to do")
        return
    w = Worker("cuda")
    print(f"worker on {w.device}", flush=True)
    refs = json.loads((REF_DIR / "REF.json").read_text(encoding="utf-8"))
    try:
        for line, (take, ex, cfg, temp) in todo:
            name = name_of(line, take)
            ref = ref_for(line)
            body = {"text": line.sent(), "voice_mode": "clone", "reference_audio_filename": ref.name,
                    "output_format": "wav", "language": "ru", "exaggeration": ex, "cfg_weight": cfg,
                    "temperature": temp, "seed": seed_of(line, take), "speed_factor": 1.0, "split_text": False}
            t0 = time.time()
            try:
                data = w(dict(body, ref=str(ref)))
            except Exception as e:
                print(f"  {name} FAILED: {e!r}", flush=True)
                continue
            (RAW / f"{name}.wav").write_bytes(data)
            if line.voice == "M":
                src = [{"title": pvt.SOURCES["thorsten_neutral"].title, "author": pvt.SOURCES["thorsten_neutral"].author,
                        "licence": "CC0 1.0", "url": "https://zenodo.org/records/5525023", "credit": ""}]
                refmeta = {"key": "radio_m_thorsten_neutral", "file": ref.name, "sha256": refs["M"]["sha256"], "sources": src}
            else:
                refmeta = {"key": "radio_f_elena", "file": "Elena.wav", "sha256": refs["F"]["sha256"],
                           "sources": [{"title": "Elena.wav, predefined voice of Chatterbox-TTS-Server 2.0.2",
                                        "author": "not documented", "licence": "origin not documented (D87, R1)",
                                        "url": "https://github.com/devnen/Chatterbox-TTS-Server", "credit": ""}]}
            (RAW / f"{name}.json").write_text(json.dumps(
                {"file": f"{name}.wav", "date": "2026-10-23",
                 "server": f"offline: chatterbox library in the server's Python, {w.device}, separate process",
                 "endpoint": "ChatterboxMultilingualTTS.generate", "model": model_label(w.device), "request": body,
                 "shown_text": line.ru, "reference": refmeta}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {name}  ex {ex} cfg {cfg}  {len(data)} B  {time.time() - t0:.1f} s", flush=True)
    finally:
        w.close()
    write_log()


def write_log() -> None:
    rows = pvt.log_rows(RAW)
    for r in rows:
        r["texto"] = r["texto"].replace("\u0301", "")          # the log shows the plain text; the JSON keeps the sent one
    (HERE / "AI-LOG.csv").write_text(pvt.log_csv(rows), encoding="utf-8-sig")
    print(f"AI-LOG.csv: {len(rows)} rows")


# ---------------------------------------------------------------- radio chain

BAND = (300.0, 3400.0)
DRIVE = 2.2
VOICE_LOUD_DB = -14.0           # loudest 50 ms, A-weighted (wa.loud_a_db): all takes alike on the page
PEAK = 10 ** (-1.0 / 20)


def radio_band(x: np.ndarray, order: int = 4) -> np.ndarray:
    return gws.filt(x, lambda f: gws.butter(f, lo=BAND[0], hi=BAND[1], order=order) * gws.bump(f, 1400, 1.4, 3.0))


def saturate(x: np.ndarray, drive: float = DRIVE) -> np.ndarray:
    p = np.max(np.abs(x)) or 1.0
    return np.tanh(drive * x / p) / np.tanh(drive)


def valve_bed(n: int, seed: int) -> np.ndarray:
    """Hum (50 Hz and its odd harmonics), hiss and sparse crackle, before the band: the set itself."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * 50 * k * t + rng.uniform(0, 6.28))
              for k, a in ((1, 1.0), (3, 0.5), (5, 0.3), (7, 0.18), (9, 0.1)))
    hum *= 0.016
    hiss = rng.standard_normal(n) * 0.010
    crack = np.zeros(n)
    for _ in range(int(n / SR * 2.5)):                      # ~2.5 crackles a second
        i = int(rng.integers(0, max(1, n - 40)))
        k = int(rng.integers(3, 30))
        crack[i:i + k] += rng.uniform(-1, 1) * rng.uniform(0.02, 0.09) * np.exp(-np.arange(k) / 6)
    return hum + hiss + crack


def wobble(n: int, seed: int) -> np.ndarray:
    """A slow +-1 dB fade of shortwave reception."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    return 10 ** ((0.6 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6.28))
                   + 0.4 * np.sin(2 * np.pi * 0.61 * t + rng.uniform(0, 6.28))) / 20)


def tune_in(seed: int, dur: float = 0.55) -> np.ndarray:
    """Static that clears while a heterodyne whistle glides down to zero beat."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.linspace(1, 0, n) ** 1.5
    f = 2600 * (1 - t / dur) ** 2 + 40
    whistle = 0.07 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    static = rng.standard_normal(n) * 0.08 * env
    return whistle + static


def trim_raw(x: np.ndarray, rate: int) -> tuple[np.ndarray, float, float]:
    """Leading/trailing silence out (keeps inner pauses). -> (y, longest inner gap s, tail cut s)."""
    db, n = pvt._frames(x, rate)
    if db.size == 0:
        return x, 0.0, 0.0
    loud = db >= db.max() - 40.0
    on = np.flatnonzero(loud)
    a, b = on[0], on[-1] + 1
    gaps, run = [], 0
    for i in range(a, b):
        run = 0 if loud[i] else run + 1
        gaps.append(run)
    gap = max(gaps) * 0.01 if gaps else 0.0
    a = max(0, a * n - int(0.03 * rate))
    b = min(len(x), b * n + int(0.12 * rate))
    y = x[a:b].copy()
    f = int(0.02 * rate)
    y[-f:] *= np.linspace(1, 0, f)
    return y, gap, (len(x) - b) / rate


def at_loudness(v: np.ndarray, target: float = VOICE_LOUD_DB) -> np.ndarray:
    for _ in range(6):
        d = target - wa.loud_a_db(v, SR)
        v = v * 10 ** (d / 20)
        if abs(d) < 0.1:
            break
    return v


def limit(x: np.ndarray) -> np.ndarray:
    p = np.max(np.abs(x))
    return x if p <= PEAK else x / p * PEAK


def broadcast(voice: np.ndarray, seed: int, lead: np.ndarray | None = None, tail_s: float = 0.35) -> np.ndarray:
    """voice (already band-limited) -> tune-in + [lead] + voice + static tail, over the valve bed, all through the set."""
    parts = [tune_in(seed)]
    if lead is not None:
        parts += [lead, np.zeros(int(0.25 * SR))]
    parts += [np.zeros(int(0.08 * SR)), voice, np.zeros(int(tail_s * SR))]
    body = np.concatenate(parts)
    bed = valve_bed(len(body), seed + 1)
    mix = radio_band(body * wobble(len(body), seed + 2) + bed, order=3)
    f = int(0.05 * SR)
    mix[-f:] *= np.linspace(1, 0, f)
    g = int(0.004 * SR)
    mix[:g] *= np.linspace(0, 1, g)
    return limit(mix)


def voice_chain(x: np.ndarray) -> np.ndarray:
    v = radio_band(x)
    v = saturate(v)
    v = radio_band(v, order=2)                     # the speaker cone after the output valve
    return at_loudness(v)


# --- station jingle and time signal: our own synthesis

def bell(freq: float, dur: float, amp: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    mod = 1.6 * np.exp(-t / 0.25) * np.sin(2 * np.pi * freq * 3.5 * t)      # inharmonic: a celesta/glock
    car = np.sin(2 * np.pi * freq * t + mod)
    body = 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t / 0.18)
    env = np.exp(-t / 0.55) * np.minimum(1, t / 0.003)
    return amp * (car + body) * env


JINGLES = {
    # name, notes as (semitones from A4, start s), length s. Original motifs: none quotes a real interval signal.
    "J1": ("Campanas, 5 notas en Re mayor, ascendente",
           ((-7, 0.0), (0, 0.32), (-7, 0.64), (-3, 0.96), (0, 1.28), (5, 1.28)), 2.6),
    "J2": ("Campanas, 4 notas en Re menor, solemne",
           ((5, 0.0), (0, 0.42), (1, 0.84), (-7, 1.26), (-14, 1.26)), 2.8),
    "J3": ("Campanas, 3 notas en quintas y octava (corta)",
           ((-7, 0.0), (0, 0.3), (5, 0.6), (-19, 0.6)), 1.9),
}


def jingle(key: str) -> np.ndarray:
    _, notes, length = JINGLES[key]
    out = np.zeros(int(length * SR))
    for semi, start in notes:
        f = 440.0 * 2 ** (semi / 12)
        b = bell(f, length - start, 0.5 if f < 200 else 1.0)
        i = int(start * SR)
        out[i:i + len(b)] += b[:len(out) - i]
    return at_loudness(saturate(radio_band(out), 1.2), VOICE_LOUD_DB - 2)


def pips() -> np.ndarray:
    """Six 1 kHz pips one second apart, the last one long: a technical time signal, no author."""
    out = np.zeros(int(5.6 * SR))
    for k in range(6):
        d = 0.5 if k == 5 else 0.1
        n = int(d * SR)
        t = np.arange(n) / SR
        e = np.minimum(1, np.minimum(t, d - t) / 0.004)
        i = int(k * SR)
        out[i:i + n] += 0.8 * np.sin(2 * np.pi * 1000 * t) * e
    return at_loudness(radio_band(out), VOICE_LOUD_DB - 3)


def ogg(x: np.ndarray, path: Path) -> None:
    data = gws.ogg_bytes(gws.wav_bytes(x, SR))
    if data is None:
        raise SystemExit("ffmpeg missing")
    path.write_bytes(data)


def process() -> None:
    ms = []
    by_line = {}
    for line in LINES:
        for take, ex, cfg, temp in TAKES:
            name = name_of(line, take)
            raw = RAW / f"{name}.wav"
            if not raw.is_file():
                continue
            x = pvt.decode_mono(raw, SR)
            raw_s = len(x) / SR
            clip_raw = int(np.sum(np.abs(x) >= 0.999))
            y, gap, tail_cut = trim_raw(x, SR)
            v = voice_chain(gws.filt(y, lambda f: gws.butter(f, lo=90, order=2)))
            seed = seed_of(line, take)
            out = broadcast(v, seed)
            ogg(out, OUT / f"{name}.ogg")
            length = len(y) / SR
            exp = expected_s(line)
            db, _ = pvt._frames(y, SR)
            silence = float(np.mean(db < db.max() - 35)) if db.size else 0.0
            m = {"name": name, "code": line.code, "take": take, "ex": ex, "cfg": cfg, "temp": temp, "seed": seed,
                 "voice": line.voice, "raw_s": round(raw_s, 2), "length": round(length, 2), "expected": round(exp, 2),
                 "ratio": round(length / exp, 2), "gap": round(gap, 2), "silence": round(silence, 3),
                 "clip_raw": clip_raw, "hit_cap": bool(raw_s >= MAX_TOKENS / 25 - 0.3), "out_s": round(len(out) / SR, 2)}
            # a take far longer than the script ran away or babbled; far shorter dropped words
            m["runaway"] = bool(m["ratio"] > 1.6 or m["hit_cap"])
            m["short"] = bool(m["ratio"] < 0.65)
            m["score"] = round(float(abs(np.log(max(m["ratio"], 1e-3))) * 3 + max(0.0, gap - 0.7) * 2 + silence
                                     + (5 if m["runaway"] else 0) + (3 if m["short"] else 0) + (0.5 if clip_raw else 0)), 3)
            ms.append(m)
            by_line.setdefault(line.code, []).append(m)
            print(f"  {name}  {length:.2f} s (expected {exp:.2f})  gap {gap:.2f}  score {m['score']}", flush=True)
    for lst in by_line.values():
        for r, m in enumerate(sorted(lst, key=lambda m: m["score"]), 1):
            m["rank"] = r
    for k in JINGLES:
        ogg(broadcast(jingle(k), 5000 + int(k[1]), tail_s=0.2), OUT / f"RADJ_{k}_synth_{DAY}.ogg")
    best = {c: min(lst, key=lambda m: m["score"]) for c, lst in by_line.items()}
    if "RAD16" in best:
        v16 = pvt.decode_mono(RAW / f"{best['RAD16']['name']}.wav", SR)
        ogg(broadcast(voice_chain(trim_raw(v16, SR)[0]), 6016, lead=pips()), OUT / f"RAD16_pips_demo_{DAY}.ogg")
    demo = [c for c in ("RAD01", "RAD03", "RAD07", "RAD10") if c in best]
    if demo:
        pieces = [jingle("J1"), np.zeros(int(0.3 * SR))]
        for c in demo:
            pieces += [voice_chain(trim_raw(pvt.decode_mono(RAW / f"{best[c]['name']}.wav", SR), SR)[0]),
                       np.zeros(int(0.7 * SR))]
        ogg(broadcast(np.concatenate(pieces), 7000), OUT / f"RAD_demo_broadcast_{DAY}.ogg")
    (HERE / "METRICS.json").write_text(json.dumps(ms, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"processed {len(ms)} takes")


# ---------------------------------------------------------------- page

def es(s: str) -> str:
    return s.replace(".", ",")


def page() -> None:
    ms = json.loads((HERE / "METRICS.json").read_text(encoding="utf-8"))
    rel = lambda p: pvt._rel(p, PAGE)  # noqa: E731
    refs = {"M": rel(ref_m()), "F": rel(REF_DIR / "Elena.wav")}
    groups = []
    for line in LINES:
        rs = sorted((m for m in ms if m["code"] == line.code), key=lambda m: m["rank"])
        groups.append({
            "row": line.code, "lump": line.lump, "kind": line.kind, "voice": line.voice,
            "ru": line.ru, "en": line.en, "es": line.es, "vlabel": VOICE[line.voice]["label"],
            "target": es(f"{expected_s(line):.1f} s"),
            "cands": [{
                "id": m["name"], "take": m["take"], "rec": m["rank"] == 1 and not m["runaway"],
                "src": rel(OUT / f"{m['name']}.ogg"), "raw": rel(RAW / f"{m['name']}.wav"), "refSrc": refs[line.voice],
                "lic": VOICE[line.voice]["lic"],
                "set": es(f"exaggeration {m['ex']:g} · cfg {m['cfg']:g} · temperatura {m['temp']:g} · semilla {m['seed']}"),
                "lvl": es(f"voz {m['length']:.2f} s (esperado ~{m['expected']:.1f} s) · bruto {m['raw_s']:.2f} s · "
                          f"pausa más larga {m['gap']:.2f} s · huecos {round(100 * m['silence'])} % · emisión {m['out_s']:.2f} s")
                       + (" · OJO: mucho más larga de lo esperado (¿balbucea o repite?)" if m["runaway"] else "")
                       + (" · OJO: más corta de lo esperado (¿se come palabras?)" if m["short"] else "")
                       + (f" · {m['clip_raw']} muestras saturadas en bruto" if m["clip_raw"] else ""),
            } for m in rs],
        })
    jing = [{"id": f"RADJ_{k}", "label": v[0], "src": rel(OUT / f"RADJ_{k}_synth_{DAY}.ogg")} for k, v in JINGLES.items()]
    data = json.dumps({"groups": groups, "jingles": jing}, ensure_ascii=False).replace("</", "<\\/")
    n = sum(len(g["cands"]) for g in groups) + len(jing)
    demo = OUT / f"RAD_demo_broadcast_{DAY}.ogg"
    pipsf = OUT / f"RAD16_pips_demo_{DAY}.ogg"
    out = (PAGE_TPL.replace("__CSS__", wa.PAGE_CSS + pvt.PAGE_CSS_EXTRA + CSS_EXTRA)
           .replace("__N__", str(n)).replace("__NL__", str(len(LINES)))
           .replace("__NT__", str(sum(len(g["cands"]) for g in groups)))
           .replace("__DEMO__", html.escape(rel(demo))).replace("__PIPS__", html.escape(rel(pipsf)))
           .replace("__REFM__", html.escape(refs["M"])).replace("__REFF__", html.escape(refs["F"]))
           .replace("__STAMP__", "2026-10-23").replace("__DATA__", data))
    PAGE.write_text(out, encoding="utf-8-sig")                 # BOM: the CEO's phone showed the accents broken (D110)
    print(f"page: {PAGE}  ({n} items)")


CSS_EXTRA = """
.rec{display:inline-block;font-size:11px;font-weight:700;border-radius:10px;padding:1px 8px;margin-left:6px;background:var(--ok);color:#fff}
.row.isrec{background:color-mix(in srgb,var(--ok) 8%,transparent)}
.cur{padding:8px 12px;border-top:1px solid var(--line)}
.ru{font-size:17px;font-weight:600;margin:2px 0}
.tr{font-size:13px;color:var(--mute);margin:1px 0}
.lic{font-size:12px;color:var(--mute);overflow-wrap:anywhere}
.vM{border-left:4px solid #3b6ea8;padding-left:8px}.vF{border-left:4px solid #a83b78;padding-left:8px}
"""

PAGE_TPL = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radio de propaganda</title>
<style>__CSS__</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Radio de propaganda (V3 · B5)</h1>
  <span class="prog">Juzgadas <b id="pDone">0</b> de <b>__N__</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <button class="primary" id="copyTop">Copiar resultado</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>Borradores de la <b>radio de ambiente</b>: altavoces en algunas salas que suenan cuando te acercas. <b>__NL__ frases</b> en ruso, estilo locutor de Radio Moscú de los 70 (partes de guerra, consignas, defensa civil y alguna ironía), con traducción. <b>__NT__ tomas</b> (3 por frase) y <b>3 sintonías</b>. La <span class="rec">recomendada</span> va primero en cada frase. Pulsa <b>OK</b>, <b>NO</b> o <b>?</b> y luego <b>Copiar resultado</b>. Nada entra en el juego hasta que lo apruebes.</p>
  <ul>
    <li><b>Voces:</b> <span class="vM">hombre</span> = clon de la lectura <b>neutra</b> de Thorsten Müller (CC0, el mismo conjunto de datos de las voces alemanas; ya estaba en disco). <span class="vF">mujer</span> = la voz predefinida <b>«Elena»</b> de Chatterbox (la vía que aceptaste en D87 para las voces predefinidas). <b>Ojo:</b> no hay ninguna voz femenina CC0/CC-BY en disco y no había permiso de descarga; si prefieres otra voz de mujer con licencia limpia, hace falta una descarga.</li>
    <li><b>Acento:</b> ninguna de las dos referencias habla ruso (una alemana, otra inglesa). Por eso cada frase tiene una toma con <code>cfg 0</code> (t03), que según la documentación reduce el acento de la referencia, y dos con más control del ritmo (t01, t02). El texto se envía con las <b>marcas de acento ruso</b> puestas a mano (el acentuador automático del modelo no está instalado).</li>
    <li><b>Procesado de radio de época:</b> banda 300-3400 Hz, saturación de válvula, zumbido de 50 Hz, soplido y chasquidos suaves, un vaivén lento de la señal y un golpe corto de sintonía (estática y silbido) al empezar. La <b>sintonía</b> de campanas es nuestra (síntesis, motivo original: no es la sintonía real de Radio Moscú, que es una canción con derechos).</li>
    <li><b>Cómo se eligieron:</b> nadie las ha escuchado aquí. Se ordenaron por medidas: duración frente a la esperada para un locutor (~5 sílabas por segundo), pausas largas dentro, huecos y saturación. Tu oído manda.</li>
    <li>Registro por toma: <code>work/audio/candidates/radio/AI-LOG.csv</code> y <code>radio/raw/*.json</code>; medidas en <code>radio/METRICS.json</code>; script <code>radio/gen_radio.py</code>.</li>
  </ul>
  <details class="extra" open><summary>Para hacerse una idea (solo para oír, no se juzga)</summary>
    <div class="pl"><span>Emisión de ejemplo: sintonía J1 + frases 1, 3, 7 y 10 (las recomendadas)</span><audio controls preload="none" src="__DEMO__"></audio></div>
    <div class="pl"><span>Señal horaria (6 pitidos) + frase 16, «Московское время — двадцать часов…»</span><audio controls preload="none" src="__PIPS__"></audio></div>
  </details>
  <table class="castt"><thead><tr><th>Referencia (no se distribuye)</th><th>Licencia</th><th>Escuchar</th></tr></thead><tbody>
    <tr><td><b>Hombre:</b> Thorsten Müller, frases neutras (alemán)</td><td>CC0 1.0, https://zenodo.org/records/5525023</td><td><audio controls preload="none" src="__REFM__"></audio></td></tr>
    <tr><td><b>Mujer:</b> «Elena», voz predefinida de Chatterbox-TTS-Server (inglés)</td><td>origen no documentado (D87, R1)</td><td><audio controls preload="none" src="__REFF__"></audio></td></tr>
  </tbody></table>
</section>
<main id="groups"></main>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Resultado para pegar en el chat</h2>
  <p class="meta">Se actualiza solo. Si el botón no copia, selecciona el texto y Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copiar resultado</button> <button id="reset">Borrar todas mis respuestas</button></p>
</section>
<footer>Generado __STAMP__ por sound-designer con <code>work/audio/candidates/radio/gen_radio.py</code>. Audio: <code>work/audio/candidates/radio/</code> (procesadas), <code>radio/raw/</code> (tal como salieron de Chatterbox). La página lee por ruta relativa: no la muevas de <code>work/audio/preview/</code>.</footer>
</div>
<script>
const D = __DATA__, G = D.groups, J = D.jingles;
const KEY = "sd-v3-radio-b5-__STAMP__";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const audio = src => `<audio controls preload="none" src="${esc(src)}"></audio>`;
const ALL = G.flatMap(g => g.cands).concat(J);
const vote = id => `<div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
  <textarea class="note" placeholder="Nota (opcional)">${esc(st(id).n || "")}</textarea></div>`;
function build(){
  let h = `<details class="grp" open><summary>Sintonía de la emisora (síntesis propia)<span class="gcount" data-g="JING"></span></summary>
    <div class="cur"><div class="meta">Suena una vez al activarse el altavoz, antes de la primera frase. Elige una o varias.</div></div>`;
  for (const j of J) h += `<div class="row" id="r-${esc(j.id)}" data-id="${esc(j.id)}"><div><div class="name"><code>${esc(j.id)}</code></div><div class="what">${esc(j.label)}</div></div>
    <div class="players"><div class="pl main"><span>Por la radio</span>${audio(j.src)}</div></div>${vote(j.id)}</div>`;
  h += `</details>`;
  for (const g of G) {
    h += `<details class="grp" open><summary><code>${esc(g.row)}</code> ${g.voice === "M" ? "hombre" : "mujer"} · ${esc(g.kind)} · <code>${esc(g.lump)}</code><span class="gcount" data-g="${esc(g.row)}"></span></summary>
      <div class="cur v${esc(g.voice)}"><div class="ru">${esc(g.ru)}</div><div class="tr">EN: ${esc(g.en)}</div><div class="tr">ES: ${esc(g.es)}</div>
      <div class="meta">${esc(g.vlabel)} · duración esperada ~${esc(g.target)}</div></div>`;
    for (const c of g.cands) {
      h += `<div class="row${c.rec ? " isrec" : ""}" id="r-${esc(c.id)}" data-id="${esc(c.id)}">
        <div><div class="name"><code>${esc(c.id)}</code>${c.rec ? '<span class="rec">recomendada</span>' : ""}</div>
          <div class="meta">${esc(c.set)}</div>
          <div class="meta"><b>Medidas:</b> ${esc(c.lvl)}</div>
          <div class="lic">Referencia: ${esc(c.lic)}</div></div>
        <div class="players"><div class="pl main"><span>Toma ${c.take} por la radio</span>${audio(c.src)}</div>
          <div class="pl"><span>Tal como salió de Chatterbox (sin radio)</span>${audio(c.raw)}</div>
          <div class="pl"><span>Su referencia</span>${audio(c.refSrc)}</div></div>
        ${vote(c.id)}</div>`;
    }
    h += `</details>`;
  }
  document.getElementById("groups").innerHTML = h;
  ALL.forEach(c => paint(c.id));
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
}
function summary(){
  const done = ALL.filter(c => st(c.id).v).length;
  document.getElementById("pDone").textContent = done;
  document.getElementById("pBar").style.width = (100 * done / ALL.length) + "%";
  const L = [`Radio de propaganda V3 B5 (__STAMP__): ${done}/${ALL.length} juzgadas`];
  const jp = v => J.filter(j => st(j.id).v === v).map(j => j.id.slice(5)).join(", ") || "—";
  L.push(`Sintonía: OK ${jp("ok")} · NO ${jp("no")} · ? ${jp("q")}`);
  const je = document.querySelector('.gcount[data-g="JING"]'); if (je) je.textContent = `${J.filter(j => st(j.id).v).length} / ${J.length}`;
  for (const g of G) {
    const el = document.querySelector(`.gcount[data-g="${g.row}"]`);
    if (el) el.textContent = `${g.cands.filter(c => st(c.id).v).length} / ${g.cands.length}`;
    const part = v => g.cands.filter(c => st(c.id).v === v).map(c => "t" + String(c.take).padStart(2, "0")).join(", ") || "—";
    L.push(`${g.row} ${g.lump}: OK ${part("ok")} · NO ${part("no")} · ? ${part("q")}`);
  }
  const notes = ALL.filter(c => (st(c.id).n || "").trim()).map(c => `${c.id}: «${st(c.id).n.trim().replace(/\s+/g, " ")}»`);
  L.push(`notas: ${notes.join(" / ") || "—"}`);
  document.getElementById("result").value = L.join("\n");
}
function copy(){
  const t = document.getElementById("result"), msg = document.getElementById("copied");
  summary();
  const ok = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fb = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(ok, fb); else fb(); } catch (e) { fb(); }
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
document.getElementById("copyTop").addEventListener("click", copy);
document.getElementById("copyBottom").addEventListener("click", copy);
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar todas las respuestas y notas de esta hoja?")) { S = {}; save(); build(); summary(); } });
build(); summary();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if cmd == "ref":
        build_ref()
    elif cmd == "generate":
        generate(sys.argv[2:] or None)
    elif cmd == "process":
        process()
    elif cmd == "page":
        page()
    elif cmd == "log":
        write_log()
