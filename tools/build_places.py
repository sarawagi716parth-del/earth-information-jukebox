"""
Builds static/places.json: a world lookup grid (quarter-degree cells) that gives the name of the place at any
latitude and longitude, for example "Maharashtra, India" on land or "Arabian Sea" on water.
The web page uses it to say where you are when you explore a picture.

Data: Natural Earth (public domain), https://www.naturalearthdata.com
  admin1.geojson  = ne_10m_admin_1_states_provinces.geojson   (states and provinces of every country)
  marine.geojson  = ne_10m_geography_marine_polys.geojson     (oceans, seas, bays and gulfs)
Both come from https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
Put them in tools/ne/ under the short names above, then run:   python tools/build_places.py
The finished static/places.json is already in the project, so you only need this to rebuild it.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ne")
OUT = os.path.join(os.path.dirname(HERE), "static", "places.json")
COLS, ROWS, SHIFT = 1440, 720, 4            # 0.25 degree cells; SHIFT = sub-pixel accuracy for OpenCV


def rings(geom):
    if not geom:
        return
    if geom["type"] == "Polygon":
        yield geom["coordinates"][0]
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            yield poly[0]


def to_px(ring):
    a = np.asarray(ring, dtype=np.float64)[:, :2]
    x = (a[:, 0] + 180.0) / 360.0 * COLS
    y = (90.0 - a[:, 1]) / 180.0 * ROWS
    return np.round(np.stack([x, y], axis=1) * (1 << SHIFT)).astype(np.int32)


def area(ring):
    a = np.asarray(ring, dtype=np.float64)
    x, y = a[:, 0], a[:, 1]
    return abs(float(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))) / 2


def nice(name):
    name = (name or "").strip()
    return name.title() if name.isupper() else name


names, index = ["Open ocean"], {}


def name_id(n):
    if n not in index:
        index[n] = len(names)
        names.append(n)
    return index[n]


shapes = []                                  # (layer, area, id, ring): layer 0 = water, 1 = land
with open(os.path.join(SRC, "marine.geojson"), encoding="utf-8") as fh:
    for f in json.load(fh)["features"]:
        p = f["properties"]
        n = nice(p.get("name_en") or p.get("name"))
        if n:
            for r in rings(f["geometry"]):
                shapes.append((0, area(r), name_id(n), r))
water_max = len(names) - 1                   # every id up to here is water

with open(os.path.join(SRC, "admin1.geojson"), encoding="utf-8") as fh:
    for f in json.load(fh)["features"]:
        p = f["properties"]
        state, country = nice(p.get("name_en") or p.get("name")), nice(p.get("admin"))
        label = f"{state}, {country}" if state and state != country else (country or state)
        if label:
            for r in rings(f["geometry"]):
                shapes.append((1, area(r), name_id(label), r))

grid = np.zeros((ROWS, COLS), np.int32)
# water first, then land on top; inside each layer big shapes first so small ones stay visible
for layer, a, i, r in sorted(shapes, key=lambda s: (s[0], -s[1])):
    cv2.fillPoly(grid, [to_px(r)], int(i), shift=SHIFT)

flat = grid.reshape(-1)
starts = np.r_[0, np.flatnonzero(np.diff(flat)) + 1]
lens = np.diff(np.r_[starts, flat.size])
rle = np.stack([flat[starts], lens], axis=1).reshape(-1).tolist()
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"cols": COLS, "rows": ROWS, "water_max": water_max, "names": names, "rle": rle,
               "source": "Natural Earth 10m admin-1 states and provinces + marine polygons (public domain)"},
              fh, ensure_ascii=False, separators=(",", ":"))
np.save(os.path.join(HERE, "ne", "grid.npy"), grid)


def lookup(lat, lon):
    return names[grid[min(ROWS - 1, int((90 - lat) / 180 * ROWS)), min(COLS - 1, int((lon + 180) / 360 * COLS))]]


if __name__ == "__main__":
    print(f"{len(names)} names, {len(rle) // 2} runs, {os.path.getsize(OUT) / 1024:.0f} KB, water ids up to {water_max}")
    for lat, lon in [(19.7, 75.7), (28.6, 77.2), (15.4, 74.0), (40.7, -74.0), (0, -140), (15, 65), (-3, -60),
                     (-75, 0), (51.5, -0.1), (35.7, 139.7), (-2, 23), (14, 88), (30, -40)]:
        print(lat, lon, "->", lookup(lat, lon))
