#!/usr/bin/env python3
"""The sergeant's wordless voice (v1.1 world sounds): raw Chatterbox takes. NOT INSTALLED.

The player is the one voice the CEO hears all game long, so it must not be a
clone of an enemy's: the riflemen clone HaelDB's vocalist 3 and the Legion and
the General clone kurt (D91, D96, D110). This round builds ONE new reference
from the same approved CC0 pack (HaelDB, "Male Grunt/Yelling sounds",
https://opengameart.org/content/male-gruntyelling-sounds, already on disk
under work/audio/voice_refs/haeldb/), from the vocalist whose files have no
number prefix (yell1..yell13), lowest voice first. Nothing is downloaded and
work/audio/voice_refs/ is only read.

Generation runs on the CPU in the Chatterbox server's own Python, in a separate
process, with the speech-token filter of work/audio/voice_takes/p2/gen_p2.py
(special tokens >= 6561 dropped before S3Gen) and the token cap of
process_voice_takes.LocalPoster. Kept takes are skipped on a rerun.

    .venv/Scripts/python.exe -I work/audio/candidates/world/voice/gen_player_voice.py ref
    .venv/Scripts/python.exe -I work/audio/candidates/world/voice/gen_player_voice.py generate
    .venv/Scripts/python.exe -I work/audio/candidates/world/voice/gen_player_voice.py log

Writes raw/<name>.wav + raw/<name>.json and AI-LOG.csv next to this file. The
processing (trim, level to the Freedoom lump, OGG) is tools/audio/gen_world_sfx.py's.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "tools" / "audio"))
import numpy as np  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")
import process_voice_takes as pvt  # noqa: E402

RAW = HERE / "raw"
REF_DIR = HERE / "ref"
DAY = "20261022"
HAELDB = "haeldb/unz/yelling sounds/"

# The unnumbered HaelDB vocalist, lowest median pitch first (measured 2026-10-22 by
# autocorrelation on the voiced 40 ms frames): the first 6 s weigh most in the clone.
PLAYER_REF = pvt.Ref(
    "player_haeldb", ("haeldb",), "-",
    tuple((HAELDB + f"yell{i}.wav", 0, 0) for i in (3, 6, 9, 11, 12, 1, 2, 8, 10, 7)),
    "HaelDB, el vocalista sin número (CC0): gritos sin palabras",
    "otra persona que los enemigos: el fusilero clona al vocalista 3 y la Legión y el General a kurt")

# (code, take, text, language, exaggeration). cfg 0.3, temperature 0.8 as D96/D110.
PLAN = [
    ("P", 1, "Agh!", "es", 0.6), ("P", 2, "Ngh!", "es", 0.7), ("P", 3, "Агх!", "ru", 0.8), ("P", 4, "Ugh!", "es", 0.5),
    ("D", 1, "Aaargh... ugh.", "es", 0.6), ("D", 2, "Аааа... кх.", "ru", 0.7),
    ("D", 3, "Aaaaah!", "es", 0.8), ("D", 4, "Argh... aah.", "es", 0.5),
    ("X", 1, "Aaaaaaargh!", "es", 0.9), ("X", 2, "Ааааргх!", "ru", 1.0), ("X", 3, "AAAAH!", "es", 0.8),
    ("O", 1, "Hmph.", "es", 0.4), ("O", 2, "Uff.", "es", 0.4), ("O", 3, "Ух.", "ru", 0.4),
]
LUMP = {"P": "SDPLPAIN", "D": "SDPLDETH", "X": "SDPLXDTH", "O": "SDPLOOF"}
SEED_BASE = {"P": 61050, "D": 62050, "X": 63050, "O": 64050}
CFG, TEMPERATURE = 0.3, 0.8

TOKEN_FILTER = r"""
import chatterbox.mtl_tts as _mt
_orig_drop = _mt.drop_invalid_tokens
def _drop(x):
    y = _orig_drop(x)
    return y[y < 6561]
_mt.drop_invalid_tokens = _drop
"""
WORKER = pvt.LOCAL_WORKER.replace("cap = int(sys.argv[1])", "cap = int(sys.argv[1])" + TOKEN_FILTER)
MODEL = pvt.LOCAL_MODEL_NAME.replace(")", ", special tokens >= 6561 dropped before S3Gen)")


def name_of(code: str, take: int) -> str:
    return f"PL{code}_{LUMP[code]}_ai_chatterbox_{DAY}_t{take:02d}"


def ref_path() -> Path:
    found = sorted(REF_DIR.glob("sd_ref_player_haeldb_*.wav"))
    if not found:
        raise SystemExit("no reference: run `ref` first")
    return found[-1]


def build_ref() -> Path:
    REF_DIR.mkdir(parents=True, exist_ok=True)
    x, parts = pvt.build_ref(PLAYER_REF, pvt.REFS_DIR)
    keep = [p for p in parts if p["peak_dbfs"] <= pvt.REF_CLIP_DBFS]
    if len(keep) != len(parts):                      # a clipped source clip clones its distortion
        ref = pvt.Ref(PLAYER_REF.key, PLAYER_REF.sources, PLAYER_REF.lang,
                      tuple(q for q, p in zip(PLAYER_REF.parts, parts) if p["peak_dbfs"] <= pvt.REF_CLIP_DBFS),
                      PLAYER_REF.label, PLAYER_REF.why)
        x, parts = pvt.build_ref(ref, pvt.REFS_DIR)
    data = pvt.wav16(x)
    wav = REF_DIR / pvt.ref_filename(PLAYER_REF.key, data)
    wav.write_bytes(data)
    src = pvt.SOURCES["haeldb"]
    rows = [{"file": p["file"], "seconds": p["seconds"], "peak_dbfs": p["peak_dbfs"],
             "sha256": pvt.sha256_of(pvt.REFS_DIR / p["file"])} for p in parts]
    (REF_DIR / "REF.json").write_text(json.dumps(
        {"file": wav.name, "sha256": pvt.sha256_of(wav), "seconds": round(len(x) / pvt.REF_SR, 2),
         "source": {"title": "Male Grunt/Yelling sounds, the unnumbered vocalist (yell*.wav)", "author": src.author, "licence": src.licence, "url": src.url},
         "parts": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{wav.name}  {len(x) / pvt.REF_SR:.2f} s  {len(parts)} clips")
    return wav


class Poster:
    def __init__(self):
        env = dict(os.environ, HF_HOME=str(pvt.CHATTERBOX_HF_HOME), HF_HUB_OFFLINE="1", PYTHONIOENCODING="utf-8")
        self.tmp = RAW / "_local.wav"
        self.p = subprocess.Popen([str(pvt.CHATTERBOX_PY), "-c", WORKER, str(pvt.LOCAL_MAX_TOKENS)],
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

    def __call__(self, job: dict) -> bytes:
        job = dict(job, out=str(self.tmp))
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


def generate(codes=None) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    ref = ref_path()
    todo = [p for p in PLAN if (not codes or p[0] in codes) and not (RAW / f"{name_of(p[0], p[1])}.wav").is_file()]
    if not todo:
        return
    poster = Poster()
    try:
        for code, take, text, lang, ex in todo:
            name = name_of(code, take)
            body = {"text": text, "voice_mode": "clone", "reference_audio_filename": ref.name,
                    "output_format": "wav", "language": lang, "exaggeration": ex, "cfg_weight": CFG,
                    "temperature": TEMPERATURE, "seed": SEED_BASE[code] + take, "speed_factor": 1.0,
                    "split_text": False}
            t0 = time.time()
            try:
                data = poster(dict(body, ref=str(ref)))
            except Exception as e:      # one bad take does not stop the round
                print(f"  {name} FAILED: {e!r}", flush=True)
                continue
            (RAW / f"{name}.wav").write_bytes(data)
            src = pvt.SOURCES["haeldb"]
            (RAW / f"{name}.json").write_text(json.dumps(
                {"file": f"{name}.wav", "date": "2026-10-22", "server": pvt.LOCAL_SERVER_LABEL,
                 "endpoint": "ChatterboxMultilingualTTS.generate", "model": MODEL, "request": body,
                 "reference": {"key": PLAYER_REF.key, "file": ref.name, "sha256": pvt.sha256_of(ref),
                               "sources": [{"title": "Male Grunt/Yelling sounds, the unnumbered vocalist (yell*.wav)", "author": src.author, "licence": src.licence,
                                            "url": src.url, "credit": src.credit}]}},
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {name}  {text}  ex {ex}  {len(data)} B  {time.time() - t0:.1f} s", flush=True)
    finally:
        poster.close()


def write_log() -> None:
    rows = pvt.log_rows(RAW)
    (HERE / "AI-LOG.csv").write_text(pvt.log_csv(rows), encoding="utf-8-sig")
    print(f"AI-LOG.csv: {len(rows)} rows")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if cmd == "ref":
        build_ref()
    elif cmd == "generate":
        generate(sys.argv[2:] or None)
        write_log()
    elif cmd == "log":
        write_log()
