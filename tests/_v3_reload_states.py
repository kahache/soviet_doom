"""The weapon-state edits of the V3 reloads experiment (D132, ADR 014).

Several suites pin the weapons' States blocks line for line as they stood
before a cosmetic install (tests/test_weapon_sprites.py, test_tt33_sprites.py,
test_ppsh_sprites.py, test_akm_sprites.py, test_gemini_weapons_install.py)
so that a sprite swap can never move a tic. The reloads are not cosmetic in
that sense: they add a 0-tic guard to Fire (two in the PPSh-41's) and two
labels, Reload and ReloadLoop. This table is the whole of that change,
applied to the "before" rows (after N9's, tests/_n9_sound_hooks.py), so
those suites keep pinning every other line. The guards are 0 tics, so the
Fire totals stay theirs to check; the new labels' totals are pinned by
tests/test_reloads.py. Design: docs/engine/2026-10-25_V3_reloads.md.

Rows are (label, sprite, frames, tics, rest); label rows (sprite ":") and
flow rows (sprite "->") are produced only for suites whose rows carry them.
Each guard must match exactly one row. Stdlib only.
"""

from __future__ import annotations

# zs file -> (magazine constant, constant prefix, sound weapon name).
GUNS: dict[str, tuple[str, str, str]] = {
    "tokarev.zs": ("SD_TT_MAGAZINE", "SD_TT", "tokarev"),
    "ppsh.zs": ("SD_PPSH_MAGAZINE", "SD_PPSH", "ppsh"),
    "akm.zs": ("SD_AKM_MAGAZINE", "SD_AKM", "akm"),
    "roks3.zs": ("SD_ROKS3_TANK", "SD_ROKS3", "roks3"),
}

# zs file -> the guards: (label, frames, tics, rest) of the row the guard
# goes BEFORE, and the guard's own frame letter.
GUARDS: dict[str, tuple[tuple[str, str, int, str, str], ...]] = {
    "tokarev.zs": (("Fire", "A", 4, "", "A"),),
    "ppsh.zs": (("Fire", "A", 0, "A_GunFlash", "A"), ("Fire", "B", 0, "A_GunFlash", "B")),
    "akm.zs": (("Fire", "B", 0, "A_GunFlash", "A"),),
    "roks3.zs": (("Fire", "A", 0, "A_GunFlash", "A"),),
}


def guard_rest(zs_file: str) -> str:
    const = GUNS[zs_file][0]
    return f'A_JumpIf(invoker.SD_MagazineDry({const}), "Reload")'


def reload_rows(zs_file: str, sprite: str, with_labels: bool) -> list[tuple]:
    """The Reload and ReloadLoop states of `zs_file`, drawn with `sprite`."""
    const, prefix, weapon = GUNS[zs_file]
    rows = [
        ("Reload", ":", "", 0, ""),
        ("Reload", sprite, "A", 0, f'A_JumpIf(!invoker.SD_CanReload({const}), "Ready")'),
        ("Reload", sprite, "A", 0, "A_SD_BeginReload"),
        ("ReloadLoop", ":", "", 0, ""),
        ("ReloadLoop", sprite, "A", 1,
         f'A_SD_ReloadTick({const}, {prefix}_RELOAD_TICS, {prefix}_RELOAD_DROP, '
         f'{prefix}_RELOAD_SOUND_TIC, "sd/weapon/{weapon}/reload")'),
        ("ReloadLoop", sprite, "A", 0, f'A_JumpIf(invoker.sdReloadTic < {prefix}_RELOAD_TICS, "ReloadLoop")'),
        ("ReloadLoop", "->", "Goto Ready", 0, ""),
    ]
    return rows if with_labels else [r for r in rows if r[1] != ":"]


def frame_count(zs_file: str) -> int:
    """How many frame rows (not labels, not flow) the reloads add."""
    if zs_file not in GUNS:
        return 0
    return len(GUARDS[zs_file]) + sum(1 for r in reload_rows(zs_file, "XXXX", False) if r[1] != "->")


def with_reloads(zs_file: str, rows) -> list[tuple]:
    """`rows` (the pinned "before" States) with the V3 reload edits."""
    out = list(rows)
    if zs_file not in GUNS:
        return out
    with_labels = any(r[1] == ":" for r in out)
    for label, frames, tics, rest, letter in GUARDS[zs_file]:
        hits = [k for k, r in enumerate(out)
                if r[1] not in (":", "->") and r[0] == label and r[2] == frames
                and r[3] == tics and r[4] == rest]
        if len(hits) != 1:
            raise AssertionError(f"{zs_file}: V3 guard before {label} {frames} {tics} {rest!r} "
                                 f"matches {len(hits)} rows, not 1")
        k = hits[0]
        out.insert(k, (label, out[k][1], letter, 0, guard_rest(zs_file)))
    ready = [r for r in out if r[0] == "Ready" and r[1] not in (":", "->")]
    if not ready:
        raise AssertionError(f"{zs_file}: no Ready frame to draw the reload with")
    flash = [k for k, r in enumerate(out) if r[0] == "Flash"]
    if not flash:
        raise AssertionError(f"{zs_file}: no Flash state to put the reload before")
    k = flash[0]
    out[k:k] = reload_rows(zs_file, ready[0][1], with_labels)
    return out
