"""The weapon-state edits of backlog N9 (D74: the approved weapon sounds).

Two suites pin the weapons' States blocks line for line as they stood before
a cosmetic install (tests/test_weapon_sprites.py, pre-D48; and
tests/test_tt33_sprites.py, pre-N17) so that a sprite swap can never move a
tic. N9 then added the sound hooks, which are not cosmetic in that sense:
an action on a frame that had none, A_WeaponReady wrapped to add the empty
click, and the RPG-7's 14-tic launch frame split 4 + 10. This table is the
whole of that change, applied to the "before" rows, so those suites keep
pinning every other line and the per-label tic totals stay theirs to check.
What each hook does: docs/sound/WEAPON-SOUNDS.md section 6 and 10,
docs/engine/MOD-SPEC.md section 6.2.

Rows are (label, sprite, frames, tics, rest); label rows (sprite ":") and
flow rows (sprite "->") pass through. Each edit must match exactly one row.
Stdlib only.
"""

from __future__ import annotations

READY = ("rest", "Ready", "A", 1, "A_WeaponReady", "A_SD_WeaponReady")
RPG7_LAUNCH = 'A_FireProjectile("SD_Pg7Grenade")'

# zs file -> edits. ("rest", label, frames, tics, old rest, new rest) or
# ("split", label, frames, tics, old rest, ((tics, rest), ...)).
N9_HOOKS: dict[str, tuple[tuple, ...]] = {
    "ice_axe.zs": (
        ("rest", "Fire", "B", 5, "", 'A_StartSound("sd/weapon/iceaxe/swing", CHAN_WEAPON)'),
    ),
    "tokarev.zs": (READY,),
    "izh.zs": (READY,),
    "ppsh.zs": (READY,),
    "rpg7.zs": (
        READY,
        ("split", "Fire", "B", 14, RPG7_LAUNCH,
         ((4, RPG7_LAUNCH), (10, 'A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON)'))),
    ),
    "roks3.zs": (READY,),
}


def with_sound_hooks(zs_file: str, rows) -> list[tuple]:
    """`rows` (the pinned "before" States) with N9's edits for `zs_file`."""
    out = list(rows)
    for kind, label, frames, tics, old, new in N9_HOOKS.get(zs_file, ()):
        hits = [k for k, r in enumerate(out)
                if r[1] not in (":", "->") and r[0] == label and r[2] == frames
                and r[3] == tics and r[4] == old]
        if len(hits) != 1:
            raise AssertionError(f"{zs_file}: N9 edit {kind} {label} {frames} {tics} {old!r} "
                                 f"matches {len(hits)} rows, not 1")
        k = hits[0]
        lb, sprite, fr = out[k][0], out[k][1], out[k][2]
        if kind == "rest":
            out[k] = (lb, sprite, fr, tics, new)
        else:
            out[k:k + 1] = [(lb, sprite, fr, t, rest) for t, rest in new]
    return out
