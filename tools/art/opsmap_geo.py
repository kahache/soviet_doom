"""Geography of the operations map (V3 B1, ADR 013): the USSR as the mod
draws it, in degrees, and the projection that puts it on the 320x200
intermission screen.

Hand-traced from general knowledge of the 1970s borders, simplified to a
few hundred vertices: it is a stylised theatre map, not a survey. No data
was downloaded and nothing here is copied from a map product; the outline
is our own approximation (docs/art/LICENSES.md, "own work").

Coordinates: (longitude east, latitude north). Longitudes past 180 continue
eastwards (Cape Dezhnev is 190.2 rather than -169.8) so every ring is a
plain polygon.

Projection: Lambert conformal conic, the projection of the Soviet school
atlases for the whole country (standard parallels STD_PARALLELS, central
meridian CENTRAL_MERIDIAN), then scaled and placed by gen_ops_map.
"""

from __future__ import annotations

import math

# ------------------------------------------------------------- projection
CENTRAL_MERIDIAN = 100.0          # deg E: the middle of the USSR's span
STD_PARALLELS = (50.0, 70.0)      # deg N: the two parallels kept true
ORIGIN_LAT = 60.0                 # deg N: the projection's y origin


def _lcc_constants():
    p1, p2 = (math.radians(p) for p in STD_PARALLELS)
    n = math.log(math.cos(p1) / math.cos(p2)) / math.log(
        math.tan(math.pi / 4 + p2 / 2) / math.tan(math.pi / 4 + p1 / 2))
    f = math.cos(p1) * math.tan(math.pi / 4 + p1 / 2) ** n / n
    rho0 = f / math.tan(math.pi / 4 + math.radians(ORIGIN_LAT) / 2) ** n
    return n, f, rho0


_N, _F, _RHO0 = _lcc_constants()


def project(lon: float, lat: float) -> tuple[float, float]:
    """(lon, lat) in degrees -> (x, y) in projection units, y pointing UP."""
    rho = _F / math.tan(math.pi / 4 + math.radians(lat) / 2) ** _N
    theta = _N * math.radians(lon - CENTRAL_MERIDIAN)
    return rho * math.sin(theta), _RHO0 - rho * math.cos(theta)


# ------------------------------------------------------------ the outline
# Clockwise from the Norwegian border on the Barents coast: the Arctic coast
# east to Cape Dezhnev, the Pacific coast south to the Korean border, the
# land border west (China, Mongolia, Afghanistan, Iran), the Caspian's three
# Soviet shores, Turkey, the Black Sea, the western border and the Baltic.
USSR = [
    # Kola and the White Sea
    (31.0, 69.8), (33.0, 69.4), (36.0, 69.1), (39.7, 68.1), (41.2, 67.2),
    (41.4, 66.2), (38.5, 66.1), (34.8, 66.6), (34.6, 65.0), (34.8, 64.4),
    (36.5, 64.0), (38.0, 64.3), (39.8, 64.6), (41.0, 65.2), (43.5, 66.2),
    (44.2, 67.8), (43.3, 68.6), (46.0, 68.0), (49.0, 68.0), (53.5, 68.4),
    (57.0, 68.6), (60.5, 69.8), (64.5, 69.4), (66.8, 69.3),
    # Yamal, the Gulf of Ob, Gydan, Taimyr
    (68.5, 71.5), (70.0, 73.5), (71.5, 72.8), (72.6, 71.0), (72.5, 68.0),
    (73.5, 66.6), (74.8, 67.5), (75.0, 69.5), (74.0, 71.3), (78.5, 72.4),
    (80.6, 73.6), (87.0, 74.0), (95.0, 75.9), (104.3, 77.7), (107.0, 76.6),
    (113.5, 75.9), (113.0, 73.7), (119.0, 73.0),
    # Lena delta to Chukotka
    (126.5, 73.5), (129.0, 71.5), (131.5, 71.0), (139.0, 72.0), (146.0, 72.3),
    (150.0, 71.3), (155.0, 71.0), (160.0, 70.0), (161.5, 69.5), (167.0, 69.8),
    (170.5, 70.1), (176.0, 69.8), (180.0, 68.8), (184.0, 67.5), (188.0, 67.0),
    (190.2, 66.1),
    # the Bering coast, Kamchatka, the Sea of Okhotsk
    (187.5, 65.5), (186.0, 64.4), (182.5, 65.2), (181.0, 64.5), (178.5, 64.6),
    (177.5, 62.6), (174.0, 61.8), (170.5, 60.0), (166.0, 60.3), (163.5, 59.9),
    (163.0, 58.0), (162.5, 56.2), (159.5, 53.5), (156.7, 51.0), (156.0, 53.0),
    (155.6, 56.0), (157.0, 57.8), (160.0, 60.6), (163.0, 62.3), (159.0, 61.8),
    (156.5, 61.6), (154.0, 59.5), (150.8, 59.5), (147.5, 59.3), (143.0, 59.3),
    (140.5, 58.0), (137.5, 54.0), (141.0, 53.0), (140.4, 50.0), (140.0, 48.0),
    (138.5, 46.8), (135.5, 43.8), (133.0, 42.8), (132.0, 43.2), (130.7, 42.3),
    # the land border westwards: China, Mongolia
    (130.5, 42.9), (131.2, 44.9), (133.0, 45.4), (134.7, 48.4), (131.0, 47.7),
    (127.6, 49.6), (125.6, 53.0), (121.0, 53.3), (119.5, 52.6), (117.8, 49.6),
    (116.0, 50.0), (114.0, 50.2), (108.0, 49.5), (103.0, 50.2), (98.0, 50.5),
    (94.0, 50.0), (90.0, 50.7), (87.8, 49.2),
    # Kazakhstan's and Central Asia's borders
    (85.5, 47.0), (83.0, 47.2), (82.5, 45.4), (80.2, 45.0), (80.3, 42.8),
    (77.0, 41.0), (74.0, 40.0), (73.6, 39.3), (74.9, 37.4), (73.0, 37.4),
    (71.5, 36.8), (68.2, 37.1), (66.5, 37.4), (64.5, 36.2), (62.3, 35.2),
    (61.0, 36.6), (59.5, 37.5), (57.0, 38.2), (54.8, 37.6), (53.9, 37.3),
    # the Caspian: east, north and west shores
    (53.8, 39.0), (53.0, 40.0), (52.8, 41.4), (52.6, 42.7), (50.5, 44.5),
    (51.3, 45.3), (53.0, 46.4), (51.5, 47.0), (49.5, 46.6), (48.0, 45.8),
    (47.5, 44.5), (47.4, 43.0), (48.8, 41.6), (49.5, 40.4), (50.3, 40.3),
    (49.1, 39.2), (48.9, 38.4),
    # Iran and Turkey to the Black Sea
    (48.0, 39.3), (46.5, 38.9), (44.8, 39.7), (43.4, 41.1), (42.5, 41.4),
    (41.5, 41.5),
    # the Black Sea coast and Crimea
    (41.6, 42.6), (40.0, 43.4), (38.5, 44.3), (37.3, 44.7), (36.6, 45.3),
    (35.4, 45.0), (33.5, 44.5), (32.6, 45.4), (33.6, 46.0), (32.0, 46.5),
    (30.7, 46.5), (30.0, 45.8), (29.6, 45.3), (28.2, 45.5),
    # Romania, Hungary, Czechoslovakia, Poland
    (28.0, 46.5), (26.6, 48.3), (24.0, 47.9), (22.9, 47.9), (22.2, 48.4),
    (22.6, 49.1), (24.1, 50.8), (23.7, 52.1), (23.5, 53.9), (22.8, 54.4),
    # Kaliningrad and the Baltic coast
    (19.6, 54.4), (20.0, 54.9), (21.1, 55.7), (21.0, 56.5), (21.6, 57.4),
    (22.6, 57.75), (24.1, 57.0), (24.3, 58.4), (23.4, 59.0), (24.7, 59.45),
    (28.0, 59.5), (29.5, 59.9), (30.3, 59.95), (29.0, 60.2), (27.8, 60.6),
    # the Finnish border north
    (29.8, 61.5), (31.6, 62.9), (29.7, 63.8), (30.1, 65.7), (29.1, 66.9),
    (28.5, 68.5), (28.7, 69.0),
]

ISLANDS = {
    "Novaya Zemlya": [
        (51.8, 71.5), (52.5, 72.4), (54.5, 73.6), (56.0, 74.6), (58.5, 75.6),
        (62.0, 76.3), (66.0, 76.9), (68.8, 77.0), (68.5, 76.4), (64.0, 75.7),
        (60.5, 75.0), (58.4, 74.0), (57.0, 73.2), (56.2, 72.3), (57.5, 71.2),
        (56.3, 70.6), (53.5, 70.7)],
    "Vaygach": [(58.6, 70.3), (60.2, 70.0), (60.6, 69.6), (59.2, 69.8)],
    "Kolguyev": [(48.2, 69.4), (49.6, 69.5), (49.9, 69.0), (48.6, 68.9)],
    "Franz Josef Land": [
        (47.0, 80.5), (52.0, 81.6), (60.0, 81.4), (64.0, 80.6), (58.0, 80.0),
        (50.0, 80.1)],
    "Severnaya Zemlya": [
        (91.5, 79.5), (95.0, 81.0), (100.0, 80.8), (104.0, 79.8), (100.0, 78.6),
        (96.0, 78.6)],
    "New Siberian Islands": [
        (136.0, 75.5), (140.0, 76.2), (146.0, 75.6), (150.0, 75.2), (147.0, 74.6),
        (141.0, 74.4), (137.0, 74.6)],
    "Wrangel": [(178.5, 71.5), (181.5, 71.6), (182.4, 71.0), (179.0, 70.9)],
    "Sakhalin": [
        (142.0, 54.3), (143.2, 53.2), (143.3, 50.5), (144.5, 49.0), (143.2, 47.0),
        (142.0, 46.0), (141.8, 47.5), (142.2, 50.0), (141.6, 52.5)],
}

# Inner water: drawn over the land in the sea colour.
LAKES = {
    "Aral": [(58.3, 45.5), (59.5, 46.7), (61.2, 46.5), (61.6, 45.0), (60.5, 43.8),
             (59.0, 43.6)],
    "Balkhash": [(73.5, 46.4), (75.0, 46.8), (77.0, 46.6), (79.0, 46.6), (78.8, 46.2),
                 (76.0, 45.9), (74.3, 45.0)],
    "Baikal": [(104.0, 51.6), (106.0, 52.2), (108.5, 53.4), (109.8, 55.6), (109.3, 55.8),
               (107.8, 54.0), (105.5, 52.8), (103.7, 51.8)],
    "Ladoga": [(30.5, 60.2), (31.8, 60.0), (32.9, 60.8), (32.3, 61.7), (30.9, 61.4)],
    "Onega": [(34.4, 61.0), (35.7, 61.3), (36.2, 62.4), (35.0, 62.8), (34.6, 61.9)],
}

# Rivers and the railway as polylines (thin strokes).
RIVERS = {
    "Volga": [(34.3, 56.3), (35.9, 56.86), (39.9, 57.6), (44.0, 56.3), (49.1, 55.8),
              (48.4, 54.3), (49.5, 53.5), (50.1, 53.2), (46.0, 51.5), (44.5, 48.7),
              (48.0, 46.3), (48.5, 45.8)],
    "Ob": [(83.8, 53.3), (82.9, 55.0), (84.5, 58.0), (76.5, 61.0), (69.0, 61.0),
           (66.0, 64.0), (66.6, 66.5), (69.0, 66.7)],
    "Yenisei": [(92.8, 56.0), (92.0, 60.0), (88.0, 64.0), (86.2, 69.4), (82.5, 71.7)],
    "Podkamennaya Tunguska": [(92.2, 61.6), (96.0, 61.4), (100.5, 61.0), (104.0, 61.6)],
    "Lena": [(105.7, 56.8), (108.1, 57.8), (120.4, 60.4), (129.7, 62.0), (127.0, 66.7),
             (126.5, 72.5)],
}

TRANS_SIBERIAN = [
    (37.6, 55.75), (39.9, 57.6), (49.7, 58.6), (56.2, 58.0), (60.6, 56.84),
    (65.5, 57.15), (73.4, 55.0), (82.9, 55.0), (92.9, 56.0), (104.3, 52.3),
    (107.6, 51.8), (113.5, 52.0), (123.9, 54.0), (135.1, 48.5), (131.9, 43.1),
]

# ------------------------------------------------------- the nine operations
# Where each map is, in degrees. MAP01 and MAP02 are fictional places
# (LORE: a cosmodrome with a metro line under it, whose westbound tunnel
# comes out at Tankograd): the cosmodrome is put in the steppe east of
# Chelyabinsk, the metro-bunker between the two.
OPERATIONS = (
    ("MAP01", "Zarya-7 cosmodrome (fictional)", 67.5, 53.6),
    ("MAP02", "the metro-bunker (fictional)", 64.4, 54.4),
    ("MAP03", "Tankograd (Chelyabinsk)", 61.4, 55.15),
    ("MAP04", "the Trans-Siberian yard at Sverdlovsk", 60.6, 56.84),
    ("MAP05", "the Volga dam at Zhiguli", 49.5, 53.45),
    ("MAP06", "Red Square, Moscow", 37.6, 55.75),
    ("MAP07", "the radar on Novaya Zemlya", 54.5, 73.2),
    ("MAP08", "Severomorsk", 33.4, 69.07),
    ("MAP09", "Tunguska", 101.9, 60.9),
)
