"""Tests for tools/audio/process_voice_takes.py: the enemy voice drafts made with
the local Chatterbox server (D87) and their listening page.

What is tested:

- The script: every spoken row of docs/sound/VOICE-SCRIPT.md §1.1-§1.3 is a
  line here with the same lump, text and language; the six wordless rows are
  not; the Freedoom lump each line is levelled against is the one
  src/lumps/SNDINFO plays today for that sound (while it still points at
  Freedoom), and its level re-measured from the IWAD.
- The cast (D87): male-named predefined voices only, one distinct voice per
  speaking class, none of the dropped borderline voices.
- Requests and names: predefined mode, the line's language, no text
  splitting, shouts with high exaggeration and low cfg; seeds distinct and
  deterministic; names follow VOICE-SCRIPT §0.5 + _tNN; generate() keeps the
  WAV as returned, writes the request beside it, and never regenerates.
- AI-LOG.csv (VOICE-SCRIPT §0.7): the nine fields, one row per take.
- Processing on synthetic signals: silence trimmed, junk after a long gap
  cut, the end silent, the high-pass, the radio colour only on the Legion,
  the level on the ruler of gen_weapon_alts (peak -1 dBFS, loudest 50 ms
  A-weighted within 1 dB of the Freedoom sound) or the shortfall reported.
- The page: Spanish, OK/NO/? and "Copiar resultado", relative paths only,
  localStorage inside try/catch, every take, its text, language and
  Freedoom sound.

- Round 2 (after D91): the 7 approved takes and their rows left out; every
  other spoken line at least 3 takes from t11, seeds distinct from round 1;
  the reference per line (Reich orders: Thorsten, German; Legion and General:
  kurt, English, cfg 0 when it reads German; pain and death: a pain
  reference); the same words as the script, one line per clone request; the
  references one speaker each, CC0 or CC-BY with the credit; the Whisper
  check (extra words or a cut line reject, a different word only warns);
  generate2's sidecar and AI-LOG row carry the reference and its licence; a
  failed take does not stop the run; the reference cutter; the round-2 page
  (rejected takes out of the vote, the approved row, relative paths).

The server is never called (a fake poster stands in). Nothing is written
under work/ or docs/ except by the on-disk check, which only reads work/
and is skipped with SD_SKIP_SLOW_ART=1 (`verify.py fast`).

Run:  .venv/Scripts/python.exe -m unittest tests.test_process_voice_takes -v
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import process_voice_takes as pv  # noqa: E402  (its tables import without numpy)

try:
    import numpy as np
    import gen_weapon_alts as wa
    import gen_weapon_sfx as gws
except ImportError:                                    # pragma: no cover
    np = wa = gws = None

needs_numpy = unittest.skipIf(np is None or pv.np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the scan of work/audio/voice_takes/")

SCRIPT = PROJECT_ROOT / "docs" / "sound" / "VOICE-SCRIPT.md"
SNDINFO = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"
NAME_RE = re.compile(r"^[RLG]\d\d_SD[A-Z]{6}_ai_chatterbox_\d{8}_t\d\d$")
FEMALE = {"Abigail", "Alice", "Cora", "Elena", "Emily", "Gianna", "Jade", "Layla", "Olivia", "Taylor"}
SECTION_LANG = {"1.1": "de", "1.2": "en", "1.3": None}


def script_rows() -> dict[str, tuple[str, str, bool, str]]:
    """row -> (lump, line, spoken?, section) from VOICE-SCRIPT §1.1-§1.3."""
    rows, sec = {}, None
    for raw in SCRIPT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (1\.\d)", raw)
        if m:
            sec = m.group(1)
            continue
        if sec not in SECTION_LANG or not raw.startswith("| "):
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if not re.fullmatch(r"[RLG]\d\d", cells[0]):
            continue
        line = cells[3]
        rows[cells[0]] = (cells[1].strip("`"), line.replace("**", "").strip(),
                          not (line.startswith("*") and not line.startswith("**")), sec)
    return rows


def sndinfo_freedoom() -> dict[str, str]:
    """Our lump -> the Freedoom lump SNDINFO plays for it today ('// -> SDxxxx' comments)."""
    out = {}
    for raw in SNDINFO.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*sd/mon/\S+\s+(DS[A-Z0-9]+)\s*//\s*->\s*(SD[A-Z]{6})\b", raw)
        if m:
            out[m.group(2)] = m.group(1)
    return out


class ScriptTests(unittest.TestCase):

    def test_every_spoken_row_is_a_line_and_no_wordless_one(self):
        rows = script_rows()
        spoken = {r for r, (_, _, s, _) in rows.items() if s}
        self.assertEqual(len(spoken), 16, "VOICE-SCRIPT §1.5: 16 spoken lines")
        self.assertEqual({l.row for l in pv.LINES}, spoken)
        self.assertEqual(set(pv.WORDLESS_ROWS), set(rows) - spoken)

    def test_lump_text_and_language_match_the_script(self):
        rows = script_rows()
        for l in pv.LINES:
            lump, text, _, sec = rows[l.row]
            with self.subTest(row=l.row):
                self.assertEqual(l.lump, lump)
                self.assertEqual(l.text, text)
                want = SECTION_LANG[sec] or ("de" if l.text == "Vorwärts." else "en")
                self.assertEqual(l.lang, want)

    def test_freedoom_reference_is_what_sndinfo_plays_today(self):
        today = sndinfo_freedoom()
        for l in pv.LINES:
            if l.lump not in today:      # installed since: the comparison is the sheet's history
                continue
            with self.subTest(row=l.row):
                self.assertEqual(l.freedoom, today[l.lump])
        self.assertTrue(set(pv.FREEDOOM_LEVELS) >= {l.freedoom for l in pv.LINES})

    def test_moment_matches_the_lump(self):
        suffix = {"idle": "ACT", "alert": "SIT", "pain": "PAI", "death": "DTH", "summon": "SUM"}
        for l in pv.LINES:
            self.assertTrue(l.lump.endswith(suffix[l.moment]), l.row)


class CastTests(unittest.TestCase):

    def test_male_named_distinct_voices_one_per_class(self):
        names = [v.name for v in pv.CAST.values()]
        self.assertEqual(len(set(names)), len(names))
        self.assertEqual(set(pv.CAST), {l.cls for l in pv.LINES})
        for v in pv.CAST.values():
            self.assertIn(v.name, pv.MALE_VOICES)
            self.assertNotIn(v.name, FEMALE)
            self.assertNotIn(v.name, pv.DROPPED_VOICES)
            self.assertLessEqual(v.f0_hz, pv.MAX_MEDIAN_F0_HZ)
        self.assertFalse(FEMALE & set(pv.MALE_VOICES))

    def test_voices_differ_in_pitch_or_brightness(self):
        vs = list(pv.CAST.values())
        for i, a in enumerate(vs):
            for b in vs[i + 1:]:
                self.assertTrue(abs(a.f0_hz - b.f0_hz) >= 10 or abs(a.centroid_hz - b.centroid_hz) >= 300,
                                f"{a.name} vs {b.name}")


class RequestTests(unittest.TestCase):

    def test_request_body(self):
        for l in pv.LINES:
            b = pv.request_body(l, 1)
            self.assertEqual(b["voice_mode"], "predefined")
            self.assertEqual(b["predefined_voice_id"], pv.CAST[l.cls].name + ".wav")
            self.assertEqual(b["language"], l.lang)
            self.assertIs(b["split_text"], False)
            self.assertEqual(b["text"], l.text)
            if l.moment == "alert" and l.cls != "general":
                self.assertGreaterEqual(b["exaggeration"], 1.0)
                self.assertLessEqual(b["cfg_weight"], 0.35)
            if l.cls == "general":
                self.assertLessEqual(b["exaggeration"], 0.5, "he never shouts")

    def test_seeds_distinct_and_deterministic(self):
        seeds = [pv.seed_of(l, t) for l in pv.LINES for t in range(1, pv.takes_of(l) + 1)]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(pv.seed_of(pv.LINES[0], 1), pv.seed_of(pv.LINES[0], 1))

    def test_names_follow_the_script(self):
        for l in pv.LINES:
            for t in range(1, pv.takes_of(l) + 1):
                n = pv.take_name(l, t, "20261020")
                self.assertRegex(n, NAME_RE)
                self.assertIs(pv.line_of(n), l)

    def test_generate_keeps_the_wav_logs_and_never_regenerates(self):
        calls = []

        def fake(body, server):
            calls.append(body)
            return b"RIFF" + json.dumps(body).encode()

        with tempfile.TemporaryDirectory() as d:
            raw = Path(d)
            made = pv.generate("20261020", raw, rows=["R04", "G02"], poster=fake, log=lambda *_: None)
            want = pv.takes_of(pv.line_of("R04_")) + pv.takes_of(pv.line_of("G02_"))
            self.assertEqual(len(made), want)
            self.assertEqual(len(calls), want)
            w = made[0]
            self.assertEqual(w.read_bytes()[:4], b"RIFF")
            side = json.loads(w.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(side["request"], calls[0])
            self.assertEqual(pv.generate("20261020", raw, rows=["R04", "G02"], poster=fake,
                                         log=lambda *_: None), [])
            rows = pv.log_rows(raw)
            self.assertEqual(len(rows), want)
            text = pv.log_csv(rows)
            parsed = list(csv.DictReader(io.StringIO(text), delimiter=";"))
            self.assertEqual(tuple(parsed[0]), pv.LOG_FIELDS)
            r = next(x for x in parsed if x["fichero"].startswith("R04_"))
            self.assertIn("seed", r["ajustes"])
            self.assertIn("exaggeration", r["ajustes"])
            self.assertIn("Austin.wav", r["voz"])
            self.assertIn("MIT", r["licencia_de_uso"])
            self.assertTrue(r["fichero"].endswith(".wav"))


@needs_numpy
class ProcessTests(unittest.TestCase):

    def vowel(self, seconds, f0=120.0, amp=0.5):
        t = np.arange(int(seconds * gws.SR)) / gws.SR
        x = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 25))
        env = np.minimum(1, np.minimum(t, t[::-1]) / 0.02)
        return amp * x / np.max(np.abs(x)) * env

    def sil(self, seconds):
        return np.zeros(int(seconds * gws.SR))

    def test_trim_cuts_silence_and_junk_after_a_long_gap(self):
        x = np.concatenate([self.sil(0.5), self.vowel(0.4), self.sil(0.15), self.vowel(0.2),
                            self.sil(1.0), self.vowel(0.3, amp=0.3), self.sil(0.5)])
        y, cut = pv.trim(x, gws.SR)
        n = len(y) / gws.SR
        self.assertAlmostEqual(n, 0.75 + pv.PRE_ROLL_S + pv.POST_ROLL_S, delta=0.03)
        self.assertGreater(cut, 1.0)
        self.assertEqual(np.max(np.abs(y[-gws.n_of(pv.TAIL_SILENCE_S):])), 0.0)

    def test_trim_keeps_a_short_pause_inside_the_line(self):
        x = np.concatenate([self.sil(0.3), self.vowel(0.3), self.sil(0.3), self.vowel(0.3), self.sil(0.3)])
        y, cut = pv.trim(x, gws.SR)
        self.assertEqual(cut, 0.0)
        self.assertGreater(len(y) / gws.SR, 0.9)

    def test_high_pass_and_radio(self):
        t = np.arange(gws.SR) / gws.SR
        low = np.sin(2 * np.pi * 40 * t)
        self.assertLess(np.std(pv.high_pass(low)[gws.SR // 4:]), 0.25 * np.std(low))
        mid = np.sin(2 * np.pi * 1000 * t)
        self.assertGreater(np.std(pv.high_pass(mid)[gws.SR // 4:]), 0.9 * np.std(mid))
        r = pv.radio_colour(0.5 * low + 0.5 * mid)
        self.assertLessEqual(np.max(np.abs(r)), 1.0 + 1e-9)
        self.assertLess(wa.share_above(r, gws.SR, 100.0), 1.0)
        self.assertGreater(wa.share_above(r, gws.SR, 300.0), 0.9)

    def test_radio_only_on_the_legion(self):
        self.assertEqual({l.cls for l in pv.LINES if l.radio}, {"trooper"})

    def test_level_reaches_the_freedoom_sound(self):
        for ref, want_drive in (("DSPOSACT", False), ("DSCYBSIT", True)):   # gain down; saturation
            target = pv.FREEDOOM_LEVELS[ref][1]
            y, drive = pv.level(self.vowel(0.6), target)
            lv = wa.levels(y)
            with self.subTest(ref=ref):
                self.assertLessEqual(lv["peak"], pv.PEAK_DBFS + 0.05)
                self.assertAlmostEqual(lv["loud_a"], target, delta=pv.LOUDNESS_TOLERANCE_DB)
                self.assertEqual(drive > 0, want_drive)
                self.assertLess(drive, pv.MAX_VOICE_DRIVE)

    def test_level_within_tolerance_or_shortfall_reported(self):
        target = pv.FREEDOOM_LEVELS["DSPOSIT1"][1]
        y, drive = pv.level(self.vowel(0.6), target)
        loud = wa.loud_a_db(y)
        if abs(loud - target) > pv.LOUDNESS_TOLERANCE_DB:
            self.assertEqual(drive, pv.MAX_VOICE_DRIVE)
            self.assertGreater(pv.short_by(loud, pv.LINES[3]), 0.0)

    def test_level_reports_an_unreachable_target(self):
        y, drive = pv.level(self.vowel(0.6), 0.0)
        self.assertEqual(drive, pv.MAX_VOICE_DRIVE)
        self.assertGreater(pv.short_by(wa.loud_a_db(y), pv.LINES[3]), 0.0)

    def test_process_wave_end_to_end(self):
        x = np.concatenate([self.sil(0.3), self.vowel(0.4), self.sil(0.4)])
        for l in (pv.LINES[3], pv.LINES[10], pv.LINES[-1]):
            y, cut, drive = pv.process_wave(x, l)
            lv = wa.levels(y)
            with self.subTest(row=l.row):
                self.assertLessEqual(lv["peak"], pv.PEAK_DBFS + 0.05)
                self.assertEqual(y[-1], 0.0)
                self.assertLess(lv["length"], 0.6)

    def test_runaway(self):
        l = pv.LINES[10]            # L04, <= 0.6 s
        self.assertTrue(pv.is_runaway(9.3, l))
        self.assertFalse(pv.is_runaway(1.0, l))


@needs_numpy
class FreedoomLevelTests(unittest.TestCase):

    def test_freedoom_levels_re_measured_from_the_iwad(self):
        for name, (pk, loud, rms) in pv.FREEDOOM_LEVELS.items():
            wav = gws.placeholder_wav(name)
            if wav is None:
                self.skipTest("iwads/freedoom2.wad is not on this machine")
            x, rate = wa.read_wav(wav)
            lv = wa.levels(x, rate)
            with self.subTest(name=name):
                self.assertAlmostEqual(lv["peak"], pk, delta=pv.LEVEL_TOLERANCE_DB)
                self.assertAlmostEqual(lv["loud_a"], loud, delta=pv.LEVEL_TOLERANCE_DB)
                self.assertAlmostEqual(lv["rms"], rms, delta=pv.LEVEL_TOLERANCE_DB)


@needs_numpy
class PageTests(unittest.TestCase):

    def test_page(self):
        t = np.arange(int(0.5 * gws.SR)) / gws.SR
        x = 0.5 * np.sin(2 * np.pi * 200 * t)
        done = [pv.Processed(pv.take_name(l, 1, "20261020"), l, x, 1.0, 0.0, 0.0) for l in pv.LINES]
        page = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-20_0000_P2_voice-takes.html"
        asr = {done[0].name: {"text": "Stellung halten.", "model": "openai-whisper medium"}}
        h = pv.page_html(done, page, "2026-10-20_0000", asr=asr)
        self.assertIn('<html lang="es">', h)
        self.assertIn("Copiar resultado", h)
        for b in ('data-v="ok">OK', 'data-v="no">NO', 'data-v="q">?'):
            self.assertIn(b, h)
        for m in re.finditer(r"localStorage\.\w+", h):
            line = h[h.rfind("\n", 0, m.start()):m.start()]
            self.assertIn("try {", line)
        items = json.loads(re.search(r"const ITEMS = (\[.*?\]);\n", h, re.S).group(1).replace("<\\/", "</"))
        self.assertEqual(len(items), len(pv.LINES))
        for it, l in zip(items, pv.LINES):
            for key in ("src", "raw", "repSrc"):
                self.assertFalse(re.match(r"^([A-Za-z]:|/|file:)", it[key]), it[key])
                self.assertTrue(it[key].startswith("../../../work/audio/"), it[key])
            self.assertEqual(it["text"], l.text)
            self.assertEqual(it["rep"], l.freedoom)
            self.assertIn(it["lang"], ("alemán", "inglés"))
        self.assertEqual(items[0]["asr"], "Stellung halten.")
        self.assertIn("Whisper", h)
        for label in pv.CLASS_LABEL.values():
            self.assertIn(json.dumps(label, ensure_ascii=False)[1:-1], h)


@needs_numpy
@slow
class OnDiskTests(unittest.TestCase):
    """The drafts in work/ (gitignored): each OGG has its raw WAV, sidecar and log row."""

    def test_every_take_logged(self):
        oggs = sorted(pv.OUT_DIR.glob("*_ai_chatterbox_*_t*.ogg"))
        log = pv.OUT_DIR / "AI-LOG.csv"
        if not oggs or not log.is_file():
            self.skipTest("no voice drafts in work/audio/voice_takes/")
        logged = {r["fichero"] for r in csv.DictReader(io.StringIO(log.read_text(encoding="utf-8-sig")),
                                                       delimiter=";")}
        for o in oggs:
            with self.subTest(take=o.stem):
                self.assertRegex(o.stem, NAME_RE)
                self.assertTrue((pv.RAW_DIR / f"{o.stem}.wav").is_file())
                self.assertTrue((pv.RAW_DIR / f"{o.stem}.json").is_file())
                self.assertIn(f"{o.stem}.wav", logged)


ALLOWED_REF_LICENCES = ("CC0 1.0", "CC-BY 3.0")


class Round2PlanTests(unittest.TestCase):
    """Round 2 (after D91): clone mode from aggressive references, approved takes untouched."""

    def test_approved_takes_and_their_rows_are_left_out(self):
        self.assertEqual(len(pv.APPROVED), 7)
        for n in pv.APPROVED:
            self.assertRegex(n, NAME_RE)
        self.assertEqual(pv.APPROVED_ROWS, ("L01", "L02", "R06"))
        rows = [l.row for l in pv.round2_lines()]
        self.assertEqual(len(rows), len(pv.LINES) - 3)
        self.assertFalse(set(rows) & set(pv.APPROVED_ROWS))

    def test_every_line_three_takes_or_more_from_take_11(self):
        takes = pv.round2_takes()
        for l in pv.round2_lines():
            mine = [t for t in takes if t.line is l]
            self.assertGreaterEqual(len(mine), 3, l.row)
            self.assertEqual([t.take for t in mine], list(range(11, 11 + len(mine))))
            first = [t for t in mine if t.take <= 13]
            self.assertEqual(len({t.exaggeration for t in first}), 3, "a ladder, not one value")

    def test_seeds_distinct_from_each_other_and_from_round_1(self):
        r1 = {pv.seed_of(l, t) for l in pv.LINES for t in range(1, pv.takes_of(l) + 1)}
        r2 = [pv.seed_of(t.line, t.take) for t in pv.round2_takes()]
        self.assertEqual(len(r2), len(set(r2)))
        self.assertFalse(r1 & set(r2))

    def test_reference_per_line(self):
        for t in pv.round2_takes():
            l = t.line
            with self.subTest(row=l.row, take=t.take):
                main = pv.ref_of(l)
                if l.delivery in ("pain", "death"):
                    self.assertTrue(main.startswith("pain_"))
                elif l.cls == "rifleman":
                    self.assertEqual(main, "de_orders")
                else:
                    self.assertEqual(main, "en_orders")
                if t.take <= 13:
                    self.assertEqual(t.ref, main)
                if l.delivery == "shout":
                    self.assertGreaterEqual(t.exaggeration, 1.0)
                ref_lang = pv.REFS[t.ref].lang
                if ref_lang not in ("-", t.lang):
                    self.assertEqual(t.cfg_weight, pv.CROSS_LINGUAL_CFG)

    def test_same_words_as_the_script_one_line_per_request(self):
        for t in pv.round2_takes():
            self.assertEqual(pv.words_of(t.text), pv.words_of(t.line.text), t.line.row)
            b = pv.request_body2(t, "sd_ref_x_00000000.wav")
            self.assertEqual(b["voice_mode"], "clone")
            self.assertEqual(b["reference_audio_filename"], "sd_ref_x_00000000.wav")
            self.assertIs(b["split_text"], False)
            self.assertEqual(b["text"], t.text)
            self.assertEqual(b["language"], t.line.lang)
            self.assertEqual(b["seed"], pv.seed_of(t.line, t.take))

    def test_references_one_speaker_licence_clean_credited(self):
        for key, r in pv.REFS.items():
            with self.subTest(ref=key):
                self.assertEqual(len({pv.SOURCES[s].author for s in r.sources}), 1, "one speaker")
                for s in r.sources:
                    src = pv.SOURCES[s]
                    self.assertTrue(src.licence.startswith(ALLOWED_REF_LICENCES), src.licence)
                    if src.licence.startswith("CC-BY"):
                        self.assertIn(src.author, src.credit)
                    self.assertTrue(src.url.startswith("https://"))
                    self.assertFalse(src.path.startswith(("src/", "assets/")))
                for path, a, b in r.parts:
                    self.assertTrue(b == 0 or b > a)


class AsrCheckTests(unittest.TestCase):

    def test_verdicts(self):
        self.assertEqual(pv.asr_check(None, "Feind!")[0], "ok")
        self.assertEqual(pv.asr_check("Feind!", "Feind!")[0], "ok")
        self.assertEqual(pv.asr_check("Stellung halten.", "Stellung halten!")[0], "ok")
        self.assertEqual(pv.asr_check("Feind! Feind!", "Feind!")[0], "reject")
        self.assertEqual(pv.asr_check("Hostile.", "Hostile, front!")[0], "reject")
        self.assertEqual(pv.asr_check("", "Feind!")[0], "reject")
        self.assertEqual(pv.asr_check("...", "Feind!")[0], "reject")
        self.assertEqual(pv.asr_check("Bye.", "Feind!")[0], "warn")
        self.assertEqual(pv.asr_check("Sanni.", "Sani…")[0], "ok")
        self.assertEqual(pv.asr_check("Vorwärts!", "Vorwärts!")[0], "ok")
        self.assertEqual(pv.asr_check("Sector 4, clear.", "Sector four, clear.")[0], "ok")
        self.assertEqual(pv.asr_check("Ruhe dahinten!", "Ruhe da hinten!")[0], "ok")
        self.assertEqual(pv.asr_check("Come in, say again.", "Command, say again?")[0], "ok")
        self.assertEqual(pv.asr_check("Oder hinten.", "Ruhe da hinten!")[0], "reject")
        self.assertEqual(pv.asr_check("I'm hit! I'm hit!", "I'm hit!")[0], "reject")
        self.assertEqual(pv.asr_check("Vorwärts! Au!", "Vorwärts!")[0], "reject")
        self.assertEqual(pv.asr_check("Sani, ahhh!", "Sani…", cries_ok=True)[0], "ok")
        self.assertEqual(pv.asr_check("Sani, ahhh!", "Sani…")[0], "reject")
        self.assertEqual(pv.asr_check("Ah!", "Sani…", cries_ok=True)[0], "warn")
        self.assertEqual(pv.asr_check("Aaaaaaah, nee!", "Sani…", cries_ok=True)[0], "warn")


class Generate2Tests(unittest.TestCase):

    def test_generate2_one_request_per_take_logged_with_its_reference(self):
        calls = []

        def fake(body, server):
            calls.append(body)
            return b"RIFF" + json.dumps(body).encode()

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            refs = {}
            for key in pv.REFS:
                refs[key] = d / f"sd_ref_{key}_00000000.wav"
                refs[key].write_bytes(b"RIFF" + key.encode())
            raw = d / "raw"
            made = pv.generate2("20261020", refs, raw, rows=["R04", "L08"], poster=fake, log=lambda *_: None)
            want = [t for t in pv.round2_takes() if t.line.row in ("R04", "L08")]
            self.assertEqual(len(made), len(want))
            self.assertEqual(len(calls), len(want))
            self.assertEqual({c["text"] for c in calls}, {"Feind!", "I'm hit!"})
            side = json.loads((raw / f"{made[0].stem}.json").read_text(encoding="utf-8"))
            self.assertEqual(side["reference"]["key"], "de_orders")
            self.assertEqual(side["reference"]["sources"][0]["licence"], "CC0 1.0")
            self.assertEqual(pv.generate2("20261020", refs, raw, rows=["R04", "L08"], poster=fake,
                                          log=lambda *_: None), [])
            rows = pv.log_rows(raw)
            self.assertEqual(len(rows), len(want))
            l08 = next(r for r in rows if r["fichero"].startswith("L08_") and "_t11" in r["fichero"])
            self.assertIn("clone of sd_ref_pain_kurt_00000000.wav", l08["voz"])
            self.assertIn("CC-BY 3.0", l08["voz"])
            self.assertIn("credit: Voice reference: kurt", l08["voz"])
            self.assertIn("voice_mode clone", l08["ajustes"])

    def test_a_failed_take_does_not_stop_the_others(self):
        def flaky(body, server):
            if body["seed"] % 2:
                raise RuntimeError("boom")
            return b"RIFF"

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            refs = {k: d / f"sd_ref_{k}_0.wav" for k in pv.REFS}
            for p in refs.values():
                p.write_bytes(b"RIFF")
            made = pv.generate2("20261020", refs, d / "raw", rows=["R01"], poster=flaky, log=lambda *_: None)
            self.assertEqual(len(made), 1)          # seeds 11051, 11052, 11053: one even


@needs_numpy
class RefCutTests(unittest.TestCase):

    def test_tighten_trims_and_shortens_long_pauses(self):
        sr = pv.REF_SR
        tone = 0.5 * np.sin(2 * np.pi * 220 * np.arange(int(0.5 * sr)) / sr)
        x = np.concatenate([np.zeros(sr), tone, np.zeros(2 * sr), tone, np.zeros(sr)])
        y = pv.tighten(x, sr)
        self.assertLess(len(y) / sr, 1.0 + pv.REF_MAX_PAUSE_S + 0.05)
        self.assertGreater(len(y) / sr, 1.0)
        short = np.concatenate([tone, np.zeros(int(0.2 * sr)), tone])
        self.assertAlmostEqual(len(pv.tighten(short, sr)) / sr, len(short) / sr, delta=0.02)

    def test_wav16_round_trip(self):
        import wave
        x = 0.5 * np.sin(np.linspace(0, 100, 2400))
        with wave.open(io.BytesIO(pv.wav16(x)), "rb") as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, pv.REF_SR))
            self.assertEqual(w.getnframes(), 2400)


@needs_numpy
class Page2Tests(unittest.TestCase):

    def test_page2(self):
        t = np.arange(int(0.5 * gws.SR)) / gws.SR
        x = 0.5 * np.sin(2 * np.pi * 200 * t)
        takes = pv.round2_takes()
        done = [pv.Processed(pv.take_name(k.line, k.take, "20261020"), k.line, x, 1.0, 0.0, 0.0) for k in takes]
        page = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-20_0000_P2_voice-takes-aggressive.html"
        bad = done[0].name
        asr = {bad: {"text": "Stellung halten, Stellung halten.", "model": "openai-whisper medium"},
               done[1].name: {"text": "Stellung halten.", "model": "openai-whisper medium"}}
        h = pv.page2_html(done, page, "2026-10-20_0000", "20261020", asr=asr, refs={})
        self.assertIn('<html lang="es">', h)
        self.assertIn("Copiar resultado", h)
        items = json.loads(re.search(r"const ITEMS = (\[.*?\]);\n", h, re.S).group(1).replace("<\\/", "</"))
        self.assertEqual(len(items), len(takes) - 1)
        self.assertNotIn(bad, {i["id"] for i in items})
        self.assertIn("Rechazadas automáticamente", h)
        self.assertIn("palabras de más", h)
        for it in items:
            self.assertTrue(it["ref"])
            for key in ("src", "raw", "repSrc"):
                self.assertTrue(it[key].startswith("../../../work/audio/"), it[key])
        for n in pv.APPROVED:
            self.assertIn(n, h)
        self.assertIn("../../../work/audio/voice_takes/" + pv.APPROVED[0] + ".ogg", h)
        self.assertIn("kurt", h)


@needs_numpy
@slow
class OnDiskRound2Tests(unittest.TestCase):
    """The round-2 drafts and references in work/ (gitignored)."""

    def test_references_cut_to_spec(self):
        refs = pv.ref_files()
        if len(refs) < len(pv.REFS):
            self.skipTest("references not built in work/audio/voice_refs/")
        import wave
        for key, p in refs.items():
            with self.subTest(ref=key), wave.open(str(p), "rb") as w:
                self.assertEqual((w.getnchannels(), w.getframerate()), (1, pv.REF_SR))
                s = w.getnframes() / pv.REF_SR
                self.assertGreaterEqual(s, pv.REF_LEN_S[0])
                self.assertLessEqual(s, pv.REF_LEN_S[1])
                x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32767
                self.assertLessEqual(20 * np.log10(np.max(np.abs(x))), pv.REF_PEAK_DBFS + 0.01)
        tsv = pv.SOURCES_TSV.read_text(encoding="utf-8")
        for p in refs.values():
            self.assertIn(p.name, tsv)

    def test_every_round2_take_logged(self):
        oggs = sorted(pv.AGGR_DIR.glob("*_ai_chatterbox_*_t*.ogg"))
        log = pv.OUT_DIR / "AI-LOG.csv"
        if not oggs or not log.is_file():
            self.skipTest("no round-2 drafts in work/audio/voice_takes/aggressive/")
        logged = {r["fichero"] for r in csv.DictReader(io.StringIO(log.read_text(encoding="utf-8-sig")),
                                                       delimiter=";")}
        for o in oggs:
            with self.subTest(take=o.stem):
                self.assertRegex(o.stem, NAME_RE)
                self.assertGreaterEqual(int(o.stem[-2:]), pv.ROUND2_FIRST_TAKE)
                self.assertTrue((pv.AGGR_RAW_DIR / f"{o.stem}.json").is_file())
                self.assertIn(f"{o.stem}.wav", logged)


if __name__ == "__main__":
    unittest.main()
