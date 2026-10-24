# World sounds: the player, doors, switches, pickups, lifts, teleporter

Living document, owner `sound-designer`. The sounds the player heard from
Freedoom until D125: the sergeant's voice, the doors, the switches, the
item, key, power-up and IZh-58 pickups, the lifts and moving floors, the
teleporter. Licence rows: `docs/art/LICENSES.md` § "World sounds".
Candidates and sources: `tools/audio/gen_world_sfx.py`,
`work/audio/sfx_sources/world/SOURCES.md` (not distributed).

## 1. Status (2026-10-23)

**Installed (D125), engine pass pending (D26).** 51 lumps in
`assets/sounds/world/`, packed as `sounds/<LUMP>.ogg`, wired in
`src/lumps/SNDINFO` (section "The player and the world"). Not committed
yet: the PM commits (D6).

| Sound (engine name) | Today | Freedoom's lump it replaces |
|---|---|---|
| player pain (`*pain100`, `*pain75`, `*pain50`, `*pain25`) | ours, 3 takes | `DSPLPAIN` |
| player death (`*death`) | ours, 2 takes | `DSPLDETH` |
| player violent death (`*xdeath`) | ours, 3 takes | `DSPDIEHI` |
| landing "oof" (`*grunt`, `*land`) | ours, 3 takes | `DSOOF` |
| use that does nothing (`*usefail`) | ours, 3 takes | `DSNOWAY` |
| door, open / close (`doors/dr1_open`, `doors/dr1_clos`) | ours, 3 + 3 | `DSDOROPN`, `DSDORCLS` |
| fast door, open / close (`doors/dr2_open`, `doors/dr2_clos`) | ours, 3 + 3 | `DSBDOPN`, `DSBDCLS` |
| switch, normal / exit (`switches/normbutn`, `switches/exitbutn`) | ours, 3 + 3 | `DSSWTCHN`, `DSSWTCHX` |
| item and key pickup (`misc/i_pkup`, `misc/k_pkup`) | ours, 3 | `DSITEMUP` |
| power-up pickup (`misc/p_pkup`) | ours, 3 | `DSGETPOW` |
| IZh-58 pickup (`sd/weapon/izh/pickup`) | ours, 2 | `DSWPNUP` (Doom's `misc/w_pkup`, D94) |
| lift start / stop (`plats/pt1_strt`, `plats/pt1_stop`) | ours, 3 + 3 | `DSPSTART`, `DSPSTOP` |
| moving floor or ceiling, loop (`plats/pt1_mid`) | ours, 3 | `DSSTNMOV` |
| teleporter (`misc/teleport`; also `brain/spawn`, gzdoom.pk3's alias of it) | ours, 2 | `DSTELEPT` |
| **jump** (`*jump`) | **Freedoom's `DSJUMP`** (D125: both takes NO) | |
| gibbed (`*gibbed`), fist (`*fist`) | Freedoom's `DSSLOP`, `DSPUNCH` (not in this round) | |

## 2. The CEO's verdict (D125)

On `work/audio/preview/world_sounds_listening.html` (56 candidates of
`tools/audio/gen_world_sfx.py`, 19 sounds), 56/56 judged, quoted as given:

> "OK (50): SDPLPAIN_w1, SDPLPAIN_w2, SDPLPAIN_w3, SDPLDETH_w1, SDPLDETH_w3, SDPLXDTH_w1, SDPLXDTH_w2, SDPLXDTH_w3, SDPLOOF_w2, SDPLOOF_w3, SDPLNOWY_w1, SDPLNOWY_w2, SDPLNOWY_w3, SDDOROPN_w1, SDDOROPN_w2, SDDOROPN_w3, SDDORCLS_w1, SDDORCLS_w2, SDDORCLS_w3, SDBDOPN_w1, SDBDOPN_w2, SDBDOPN_w3, SDBDCLS_w1, SDBDCLS_w2, SDBDCLS_w3, SDSWTCHN_w1, SDSWTCHN_w2, SDSWTCHN_w3, SDSWTCHX_w1, SDSWTCHX_w2, SDSWTCHX_w3, SDITEMUP_w1, SDITEMUP_w2, SDITEMUP_w3, SDGETPOW_w1, SDGETPOW_w2, SDGETPOW_w3, SDIZPKP_w1, SDIZPKP_w2, SDPSTART_w1, SDPSTART_w2, SDPSTART_w3, SDPSTOP_w1, SDPSTOP_w2, SDPSTOP_w3, SDPMOVE_w1, SDPMOVE_w2, SDPMOVE_w3, SDTELEPT_w1, SDTELEPT_w2 · NO (5): SDPLDETH_w2, SDPLJUMP_w1, SDPLJUMP_w2, SDIZPKP_w3, SDTELEPT_w3 · ? (1): SDPLOOF_w1 «El audio está bien pero no tiene el ruido, yo dejaría los 2 audios a la vez»"
> (CEO, on `SDPLOOF_w1`: "The audio is fine but it lacks the noise, I would leave both audios playing at once")

What the PM made of it: every OK is a take of a `$random` group, as the
enemy voices are; SDPLOOF_w1's voice is laid over SDPLOOF_w3's impact (both
layers at once) and joins the oof group; the jump keeps Freedoom's.

## 3. How they were installed

`tools/audio/master_world_sfx.py --install`, the way the D107 dogs were:

- **The 50 OKs ship byte for byte as the page's OGGs.** The candidates were
  already levelled with the mod's ruler (loudest 50 ms, A-weighted,
  `gen_weapon_alts.loud_a_db`, the same ruler as every weapon and enemy
  sound; the mod has no LUFS target) to the Freedoom lump each replaces,
  the IZh pickup at `DSWPNUP` - 3 dB (the weapon pickups' rule, D94), peak
  -1 dBFS through the look-ahead limiter, Vorbis q4. The pass re-checks each
  decoded OGG: peak under -0.1 dBFS (the highest is `SDIZPKP1`, -0.21),
  loudness within the target +-1.5 dB (the 1 dB window plus 0.5 dB for the
  codec), or at the shortfall the page already reported.
- **Four are short of their target, as the page said:** the exit switch's
  three (`SDSWTCX1`-`3`, 3.7, 2.3 and 1.7 dB under `DSSWTCHX`, an 8-bit
  clipped lump at -5 dB A that a clean transient does not reach) and
  `SDIZPKP1` (2.2 dB under its target). Pinned in `SHORT_OF_TARGET`.
- **`SDSGOOF1`**: SDPLOOF_w1's voice (the Chatterbox "Ух", 2 semitones down,
  as heard) over SDPLOOF_w3's impact (the boots and the kit on the concrete,
  rendered with w3's own seed, so it is the layer w3 had), in w3's recipe:
  the impact 2 dB under the voice, the voice 20 ms after it; levelled to
  `DSOOF` by the page's chain for a mix. The voice stays where w1 had it
  (-22.5 dB A); the impact sits 0.6 dB under its level in w3. WAV master in
  `work/audio/master_world/`.
- The moving floor's loop ships as the single 0.48 s cycle; the engine
  repeats it (`playrepeat` in SNDSEQ). Its loudness is measured repeated.

Names: the card's first seven letters and the candidate's number
(`SDDOROP1`); the two switch cards share seven letters and drop the H
(`SDSWTCN`, `SDSWTCX`); the player's cards begin with SDPL, the Panzermensch
shell's sprite prefix, so the sergeant's sounds are SD + SG (sergeant) + the
event's three letters (`SDSGPAI1`, `SDSGDET`, `SDSGXDT`, `SDSGOOF`, `SDSGNOW`).

| Lump | Candidate | Kind | Logical name | Target (dB A) | Loud (dB A) | Peak (dBFS) | OGG SHA-256 |
|---|---|---|---|---|---|---|---|
| `SDSGPAI1` | SDPLPAIN_w1 | recorded voice | `sd/player/pain/1` | DSPLPAIN -10.17 | -10.23 | -3.16 | `8524ef65537241887c8b600bc1f76f1c69969b3b4dcc58b439c99e36078ade20` |
| `SDSGPAI2` | SDPLPAIN_w2 | AI voice | `sd/player/pain/2` | DSPLPAIN -10.17 | -10.37 | -1.10 | `4bd04d987c02d8b372d3a53c6e9f325d7fd01498a55daf34c646ef19ca68666c` |
| `SDSGPAI3` | SDPLPAIN_w3 | recorded voice | `sd/player/pain/3` | DSPLPAIN -10.17 | -10.27 | -1.06 | `97d2c94e7a300844259a968fec29794f29de1518a20a1b33c0190d9ed6d939ac` |
| `SDSGDET1` | SDPLDETH_w1 | recorded voice | `sd/player/death/1` | DSPLDETH -8.44 | -8.53 | -0.29 | `7281e6af1aa8bcbcb3f2feae985a49859113c7937af3caab2fe9443c91bd029b` |
| `SDSGDET3` | SDPLDETH_w3 | mix | `sd/player/death/3` | DSPLDETH -8.44 | -8.75 | -0.32 | `2653aa253f9e3560778b5d9986e214263bbb26a329897fc5a573701f23377609` |
| `SDSGXDT1` | SDPLXDTH_w1 | mix | `sd/player/xdeath/1` | DSPDIEHI -8.58 | -8.59 | -1.18 | `ac193da4562ce75e65105026bed894e95fd03e73530e742fb8225cce5cd1724d` |
| `SDSGXDT2` | SDPLXDTH_w2 | AI voice | `sd/player/xdeath/2` | DSPDIEHI -8.58 | -8.64 | -0.79 | `e926366aef5b87f539f45cff6625ae9ba3623dd428d204a36d1f75ae7e1fc43a` |
| `SDSGXDT3` | SDPLXDTH_w3 | recorded voice | `sd/player/xdeath/3` | DSPDIEHI -8.58 | -8.48 | -2.13 | `0bf4901aeb2be96ef51db561105baec4394244763180b299d9a134546f6ae911` |
| `SDSGOOF1` | SDPLOOF_w1 + SDPLOOF_w3 | mix (AI voice + impact) | `sd/player/oof/1` | DSOOF -22.48 | -22.41 | -12.04 | `9c84029f52f272f24d9fe36ca567e62f599b09751e5df73dbc61a52de89db2c6` |
| `SDSGOOF2` | SDPLOOF_w2 | mix | `sd/player/oof/2` | DSOOF -22.48 | -22.47 | -1.10 | `c6989f365e7a3cd62b070c5eeb7d8add93a641b83fc46bc6a30ad5f009037b5b` |
| `SDSGOOF3` | SDPLOOF_w3 | mix | `sd/player/oof/3` | DSOOF -22.48 | -22.46 | -10.74 | `6f4e1888f4e7d30526b3a919a9bc9da5514e60545733be4caf2b156e14f277b1` |
| `SDSGNOW1` | SDPLNOWY_w1 | recording | `sd/player/usefail/1` | DSNOWAY -17.34 | -17.60 | -4.24 | `f49cf82dec1094ecd5aa3b1310e34741e0bb87e72b7e13f9a7ca33011bc3783e` |
| `SDSGNOW2` | SDPLNOWY_w2 | synthesis | `sd/player/usefail/2` | DSNOWAY -17.34 | -17.44 | -0.92 | `5c7042882d0485316b787f1c1cf5bb2e4c592bdce9a4035789400a0b3088ba10` |
| `SDSGNOW3` | SDPLNOWY_w3 | mix | `sd/player/usefail/3` | DSNOWAY -17.34 | -17.38 | -6.41 | `66eac5d626aff83913645919a15450df1944bf9e356355af21fa7c3c5b3985fa` |
| `SDDOROP1` | SDDOROPN_w1 | mix | `doors/dr1_open/1` | DSDOROPN -15.46 | -15.44 | -7.52 | `6ec79bace0446a780a9d045340bfa0c19d91ddbc0fab181b7d12498ae114687a` |
| `SDDOROP2` | SDDOROPN_w2 | synthesis | `doors/dr1_open/2` | DSDOROPN -15.46 | -15.66 | -0.72 | `146264777b6a0a8d645dfd370f57597c74aae17d46ef172694269a54285da499` |
| `SDDOROP3` | SDDOROPN_w3 | mix | `doors/dr1_open/3` | DSDOROPN -15.46 | -15.46 | -4.67 | `9b502f982762082d62c917cc3d831cb323318e34bf777de191c1d9d2ce8fc017` |
| `SDDORCL1` | SDDORCLS_w1 | mix | `doors/dr1_clos/1` | DSDORCLS -15.78 | -15.73 | -6.58 | `679cf4fdc0f89c031670c0fbc38e392d78b048d776a0bc81a5fab34bd3b0655f` |
| `SDDORCL2` | SDDORCLS_w2 | synthesis | `doors/dr1_clos/2` | DSDORCLS -15.78 | -15.86 | -0.60 | `70dcbf6e2a35ceb0bd7bdbcf537b367cc36e1b4786110d7f0f2983e2a6561b0e` |
| `SDDORCL3` | SDDORCLS_w3 | mix | `doors/dr1_clos/3` | DSDORCLS -15.78 | -15.76 | -1.10 | `e2530a3eeef1d6be0cfefddcbfef5f6f01c1ecb239ed60db2c82eb1f912b16e5` |
| `SDBDOPN1` | SDBDOPN_w1 | mix | `doors/dr2_open/1` | DSBDOPN -16.79 | -16.83 | -7.51 | `95d53e1c0818ba466b80b4ecfedacd800a9677e76af3bd0a43483fc41d0831c1` |
| `SDBDOPN2` | SDBDOPN_w2 | synthesis | `doors/dr2_open/2` | DSBDOPN -16.79 | -17.04 | -4.82 | `aa161b59af818025bca110e4022b1a9f847e24c3b45734b830feafb4fb3dbfb5` |
| `SDBDOPN3` | SDBDOPN_w3 | recording | `doors/dr2_open/3` | DSBDOPN -16.79 | -16.76 | -8.75 | `efa0ab9a0f937bde5b21506413509f62e11221b2d79c16e181b05ec0d37e6787` |
| `SDBDCLS1` | SDBDCLS_w1 | recording | `doors/dr2_clos/1` | DSBDCLS -17.04 | -17.11 | -5.67 | `f0b8a53ce0937f3672a418724c0893ec5d52fd52c86b9f8b41999093e051afd1` |
| `SDBDCLS2` | SDBDCLS_w2 | synthesis | `doors/dr2_clos/2` | DSBDCLS -17.04 | -17.38 | -0.96 | `9328aa6843751acc7708e064f4052ca60bd2103444f2f8c55faaa113f313e848` |
| `SDBDCLS3` | SDBDCLS_w3 | recording | `doors/dr2_clos/3` | DSBDCLS -17.04 | -17.32 | -4.78 | `ffd40b17963edddba163595615ec1bda7d87482d4253f39f99a869f698c564bc` |
| `SDSWTCN1` | SDSWTCHN_w1 | recording | `switches/normbutn/1` | DSSWTCHN -17.67 | -17.91 | -6.09 | `c9f3cbd0a87b2cde9200ae6f2665a9bdd81cb57ed33bee6a44760588f6ed617a` |
| `SDSWTCN2` | SDSWTCHN_w2 | mix | `switches/normbutn/2` | DSSWTCHN -17.67 | -17.71 | -0.48 | `1ddec71989b04196f6f9c7b7d48bc61b498af56e19e1839a4178f3c23192213a` |
| `SDSWTCN3` | SDSWTCHN_w3 | synthesis | `switches/normbutn/3` | DSSWTCHN -17.67 | -17.87 | -5.59 | `aa8a8721d5aabc189e4dec196520f1a1f4bf20607f289360154ebfe75d4dae9c` |
| `SDSWTCX1` | SDSWTCHX_w1 | synthesis | `switches/exitbutn/1` | DSSWTCHX -5.10 | -8.76 | -0.59 | `60483f6d07cd71e5d259c4fd4ae7fa8708acf965ac318eff5730ddd0ff9a81ba` |
| `SDSWTCX2` | SDSWTCHX_w2 | mix | `switches/exitbutn/2` | DSSWTCHX -5.10 | -7.40 | -0.68 | `d95732c9de475c491e04358def7abd69a9a0ee9b874f2fa342e40a4e02c24899` |
| `SDSWTCX3` | SDSWTCHX_w3 | recording | `switches/exitbutn/3` | DSSWTCHX -5.10 | -6.80 | -0.43 | `113549cbb9ba8d3976c26f56796d053bb00310502e99ab788aa6c0568e17dab9` |
| `SDITEMU1` | SDITEMUP_w1 | recording | `misc/i_pkup/1` | DSITEMUP -20.29 | -20.34 | -8.18 | `2f09aa2674a142237c10895bcc930b928ecd3449c6026cbca20ef800f4db4d20` |
| `SDITEMU2` | SDITEMUP_w2 | synthesis | `misc/i_pkup/2` | DSITEMUP -20.29 | -20.54 | -5.78 | `e6884b5c8770a4f5cb2dc69bbfff1cbd970aa97152be98a9cb6ba3f17d3999ca` |
| `SDITEMU3` | SDITEMUP_w3 | mix | `misc/i_pkup/3` | DSITEMUP -20.29 | -20.79 | -1.73 | `9e42b31bd41b13bafb8df097ff75492f9b90b780534578a96230d1dc25da6b43` |
| `SDGETPO1` | SDGETPOW_w1 | synthesis | `misc/p_pkup/1` | DSGETPOW -11.29 | -11.24 | -8.89 | `d06839142ca51ea8266671e8d5f7262b21a6fae02f513f41dbb6587858263b7f` |
| `SDGETPO2` | SDGETPOW_w2 | synthesis | `misc/p_pkup/2` | DSGETPOW -11.29 | -11.30 | -0.93 | `1e9ce7f1feaea0608b68493094b328f74c30ace9563e84fa094a4e97fee11570` |
| `SDGETPO3` | SDGETPOW_w3 | synthesis | `misc/p_pkup/3` | DSGETPOW -11.29 | -11.40 | -1.77 | `b628edbdc56b56f9c1051c94c489931cf947cd213c5701d10ffbf031abf66dd0` |
| `SDIZPKP1` | SDIZPKP_w1 | recording | `sd/weapon/izh/pickup/1` | DSWPNUP -3 = -8.20 | -10.44 | -0.21 | `49d3e28ef25b5df7bf5184d5753d64f55f5e480447d8a318d74f802441467f92` |
| `SDIZPKP2` | SDIZPKP_w2 | mix | `sd/weapon/izh/pickup/2` | DSWPNUP -3 = -8.20 | -8.44 | -0.74 | `e512452bc59c608f83eac54c252399bcae728340f26ce162ef40a0b9ae89cc5a` |
| `SDPSTAR1` | SDPSTART_w1 | synthesis | `plats/pt1_strt/1` | DSPSTART -15.02 | -15.06 | -0.76 | `26dc14e42151ead32470b5c1ba635ca92d59262a59cc9f494de3db53b608c2a5` |
| `SDPSTAR2` | SDPSTART_w2 | recording | `plats/pt1_strt/2` | DSPSTART -15.02 | -15.16 | -1.90 | `30283d60a6cbdb7f0a2749b0ed4790f76dbe90a6a1a5a3eb2afc6edfe662b0ac` |
| `SDPSTAR3` | SDPSTART_w3 | mix | `plats/pt1_strt/3` | DSPSTART -15.02 | -15.12 | -4.12 | `7d509960d769d7dcfc66e5d06cf304b96150552204e553f8df39541dac69ddab` |
| `SDPSTOP1` | SDPSTOP_w1 | synthesis | `plats/pt1_stop/1` | DSPSTOP -15.72 | -15.76 | -0.96 | `01efa324dce36c331b62e2e8bc611e234c390aeb75437b9a4541544797266785` |
| `SDPSTOP2` | SDPSTOP_w2 | recording | `plats/pt1_stop/2` | DSPSTOP -15.72 | -16.04 | -3.74 | `74660403b99fa5b00dbbb9b261d41ea5545d91529560e212c59584225d521322` |
| `SDPSTOP3` | SDPSTOP_w3 | mix | `plats/pt1_stop/3` | DSPSTOP -15.72 | -15.73 | -3.67 | `084e9a2adc8ab3fca2e4a2c18ba0365c0426cb9a7419ac572534cfd239c6240d` |
| `SDPMOVE1` | SDPMOVE_w1 | synthesis | `plats/pt1_mid/1` | DSSTNMOV -21.46 | -21.53 | -5.91 | `a7c078144ee4a572fef63d1294b9ceeb7baef5c198ef491c358ff6077fae03bf` |
| `SDPMOVE2` | SDPMOVE_w2 | recording | `plats/pt1_mid/2` | DSSTNMOV -21.46 | -21.56 | -9.21 | `b1db44f797981ab627cc5176b8b3bd661c5b9af8db400dba04ab62970fc94d41` |
| `SDPMOVE3` | SDPMOVE_w3 | recording | `plats/pt1_mid/3` | DSSTNMOV -21.46 | -21.59 | -8.71 | `c9949f25092b999225eeeb29fde7998ba180978be7e01c3cd8030ed07bcb944f` |
| `SDTELEP1` | SDTELEPT_w1 | synthesis | `misc/teleport/1` | DSTELEPT -11.80 | -11.94 | -0.38 | `57dd6584edcbd418797b9cea52f7a249525bf0bd2a0de11367fb599070362ffd` |
| `SDTELEP2` | SDTELEPT_w2 | mix | `misc/teleport/2` | DSTELEPT -11.80 | -11.78 | -0.98 | `3c1df4543a87f4215ed8ea5d00c911391d60c5b83a08132f244bf6871435507b` |

## 4. How the engine reaches them

From gzdoom.pk3 g4.14.2 (`sndinfo.txt`, `filter/game-doomchex/sndinfo.txt`,
`sndseq.txt`, read 2026-10-23):

- **World sounds:** a `$random` group on the engine's own logical name
  (`doors/dr1_open` ... `misc/teleport`), which redefines the IWAD's lump
  line; SNDSEQ's doors, lifts and floors and the items' default
  `PickupSound` keep asking for the same names. Redefining a name keeps
  gzdoom.pk3's `$limit 1` and `$pitchshift 0` on the pickups. Members are
  `<name>/<take>` (`doors/dr1_open/1`), the file's convention since D86.
  `misc/k_pkup` is a group of its own whose members point at the item's
  lumps (Doom plays `DSITEMUP` for keys too; a take is in one group only).
- **Player sounds:** `$random sd/player/<event>`, and `$playeralias` points
  the player sounds at it, for the three genders (the sergeant is one man).
  Doom makes `*pain75/50/25` and `*land` duplicates of `*pain100` and
  `*grunt`; they are aliased again, or they would keep Freedoom's lumps and a
  hard landing would play two oofs (GZDoom plays `*land` unless it resolves
  to the same sound as `*grunt`).
- **IZh-58:** `SD_Izh` has `Inventory.PickupSound "sd/weapon/izh/pickup"`
  (one line in `src/zscript/weapons/izh.zs`).

**NOT VERIFIED in the engine** (D26: agents do not start GZDoom). What the
PM's engine pass should check: the log has no SNDINFO error; pain, death,
a hard landing (one oof, not two), E on a wall, a door, a fast door, a
switch, the exit switch, an item, a key, a power-up, the IZh-58, a lift, a
moving floor (listen to the loop's seam) and a teleporter each play ours;
the jump still plays Freedoom's.

## 5. Not installed

- D125 NO: `SDPLDETH_w2`, `SDPLJUMP_w1`, `SDPLJUMP_w2`, `SDIZPKP_w3`,
  `SDTELEPT_w3`; SDPLOOF_w1 alone (it ships only layered, as `SDSGOOF1`).
- The jump: a new round only if the CEO asks for one.

## 6. Open points for the PM

- **AI disclosure.** Three installed takes carry Chatterbox output
  (`SDSGPAI2`, `SDSGXDT2`, and the voice inside `SDSGOOF1`), cloned from
  HaelDB's unnumbered vocalist (CC0). `tools/release.py`'s AI text says
  "some enemy voice lines"; it now undersells it (the player's voice has
  Chatterbox takes too). Not edited here: release tooling.
- **Freedoom-derived material.** `SDSGXDT1` and `SDSGXDT2` layer our gib
  `SDRRIXDT`, which edits Freedoom's `DSSLOP` (BSD-3): their licence rows
  carry `credit "Freedoom"`, as the gibs' do.
