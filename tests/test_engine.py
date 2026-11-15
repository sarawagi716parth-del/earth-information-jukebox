"""
Checks for the image-only jukebox engine. Run:  python tests/test_engine.py
1. Known-answer picture made in memory (never saved, never shown in the app): a left-to-right colour ramp
   with a grey "land" block. Notes must rise left to right, the land block must be silent, and the
   auto colour-scale learner must recover the right order without being told the scale.
2. Every NASA track in packs/: files written, audio level sane, notes on the pentatonic scale, no more
   than 3 notes at the same moment, and track-specific science checks.
3. Videos are refused.
"""
import json, os, sys, tempfile
import cv2
import numpy as np
from scipy.io import wavfile
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import jukebox_engine as je

results = []
def check(name, ok, info=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  ({info})" if info else ""))

# ---------- 1. known answer
W, H = 480, 240
ramp_bgr = np.array([je.hex_to_bgr(h) for h in ["#08306b", "#2171b5", "#6baed6", "#fdd49e", "#ef6548", "#990000"]], np.float32)
xs = np.linspace(0, 1, W)
pos = np.linspace(0, 1, len(ramp_bgr))
row = np.stack([np.interp(xs, pos, ramp_bgr[:, c]) for c in range(3)], axis=1)
img = np.tile(row[None], (H, 1, 1)).astype(np.uint8)
img[:, 200:280] = (100, 100, 100)                     # grey land block in the middle
palette = [[i / 5, h] for i, h in enumerate(["#08306b", "#2171b5", "#6baed6", "#fdd49e", "#ef6548", "#990000"])]
prof = {"id": "t", "title": "t", "type": "values", "image": "x.png", "columns": 64,
        "scale": {"palette": palette, "match": "rgb", "max_colour_distance": 40, "min_saturation": 0.15, "min_brightness": 30},
        "min_data_fraction": 0.3}
notes, grid, cells, meta, dur = je.sonify_image(img, prof)
mid = [n for n in notes if n["layer"] == "middle"]
check("known answer: notes rise from left to right", spearmanr([n["col"] for n in mid], [n["midi"] for n in mid])[0] > 0.9)
land_cols = [c for c in range(64) if 200 <= (c + 0.5) * W / 64 < 280]
check("known answer: grey block is silent", not any(n["col"] in land_cols[1:-1] for n in notes))
check("known answer: sound pans left to right", notes[0]["pan"] < 0 < notes[-1]["pan"])
auto = je.ColourScale(img, {"auto": True, "match": "rgb", "max_colour_distance": 45, "min_saturation": 0.15, "min_brightness": 30})
va, ok = auto.decode(img)
check("auto colour scale recovers the order without a colour bar", spearmanr(va[ok], np.tile(xs, (H, 1))[ok])[0] > 0.95)

# ---------- 2. NASA tracks
for name in sorted(os.listdir(os.path.join(ROOT, "packs"))):
    d = os.path.join(ROOT, "packs", name)
    if not os.path.isfile(os.path.join(d, "profile.json")):
        continue
    r = je.build_track(d)
    files_ok = all(os.path.exists(os.path.join(d, f)) for f in ["score.json", "grid.json", "track.json", "sonified.wav"])
    check(f"{name}: files written", files_ok)
    _, a = wavfile.read(os.path.join(d, "sonified.wav"))
    a = a.astype(np.float32) / 32767
    rms_db = 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
    check(f"{name}: peak below 0.9 and loudness sensible", np.max(np.abs(a)) <= 0.9 and -30 < rms_db < -8, f"peak {np.max(np.abs(a)):.2f}, {rms_db:.1f} dBFS")
    check(f"{name}: every note on the pentatonic scale", all(n["midi"] % 12 in je.PENTA for n in r["notes"]))
    per_step = {}
    for n in r["notes"]:
        per_step[n["t"]] = per_step.get(n["t"], 0) + 1
    check(f"{name}: never more than 3 notes at once", max(per_step.values()) <= 3, f"max {max(per_step.values())}")
    t = json.load(open(os.path.join(d, "track.json"), encoding="utf-8"))
    check(f"{name}: image and audio descriptions present", len(t["image_description"]) > 200 and len(t["audio_description"]) > 200)
    p = r["profile"]
    if p["type"] == "values":
        check(f"{name}: pitch follows the value", spearmanr([n["value"] for n in r["notes"]], [n["midi"] for n in r["notes"]])[0] > 0.95)
    if name == "sea_surface_temperature":
        img = r["image"]; sc = je.ColourScale(img, p["scale"]); vals, valid = sc.decode(img)
        zon = {}
        for lat in (60, 30, 0, -30, -60):
            y0 = int((90 - lat - 5) / 180 * img.shape[0]); y1 = int((90 - lat + 5) / 180 * img.shape[0])
            zon[lat] = float(vals[y0:y1][valid[y0:y1]].mean())
        # published annual zonal-mean sea surface temperatures are roughly: 60N 5-9, 30N 21-24, equator 26-29, 30S 18-21, 60S 0-3 C
        ok = 5 <= zon[60] <= 10 and 20 <= zon[30] <= 25 and 26 <= zon[0] <= 30 and 17 <= zon[-30] <= 22 and -1 <= zon[-60] <= 4
        check("sea_surface_temperature: decoded temperatures match known ocean averages", ok, ", ".join(f"{k}: {v:.1f}" for k, v in zon.items()))
        land = (r["image"].max(2) - r["image"].min(2) < 12) & (r["image"].max(2) > 35)
        check("sea_surface_temperature: no notes over land", not any(
            land[int(b["top"] * img.shape[0]):int(b["bottom"] * img.shape[0]), int(n["col"] * img.shape[1] / 64):int((n["col"] + 1) * img.shape[1] / 64)].mean() > 0.9
            for n in r["notes"] for b in p["bands"] if b["name"] == n["layer"]))
    if name == "geos_aerosols_2025":
        dust = [n["col"] for n in r["notes"] if n["layer"] == "Dust"]
        # the Saharan dust plume spans roughly 70 W to 40 E, columns 19 to 39
        check("geos_aerosols_2025: dust is heard over the Saharan plume", len(dust) >= 5 and all(17 <= c <= 42 for c in dust), str(dust))
    if name == "iss_lightning":
        south = sum(1 for n in r["notes"] if n["midi"] <= 72); north = sum(1 for n in r["notes"] if n["midi"] >= 79)
        check("iss_lightning: most lightning heard south of the equator (lower notes)", south > 3 * north, f"low {south}, high {north}")

# ---------- place names (static/places.json, built from Natural Earth)
pl = json.load(open(os.path.join(ROOT, "static", "places.json"), encoding="utf-8"))
ids = np.repeat(np.array(pl["rle"][0::2]), np.array(pl["rle"][1::2])).reshape(pl["rows"], pl["cols"])
def place(lat, lon):
    return pl["names"][ids[int((90 - lat) / 180 * pl["rows"]), int((lon + 180) / 360 * pl["cols"])]]
check("place names: 19.7 N, 75.7 E is Maharashtra, India", place(19.7, 75.7) == "Maharashtra, India", place(19.7, 75.7))
check("place names: 15 N, 65 E is the Arabian Sea", place(15, 65) == "Arabian Sea", place(15, 65))
check("place names: 40.7 N, 74 W is in New York", "New York" in place(40.7, -74.0), place(40.7, -74.0))

# ---------- 3. videos refused
with tempfile.TemporaryDirectory() as d:
    json.dump({"id": "v", "title": "v", "type": "values", "image": "clip.mp4", "scale": {"auto": True}}, open(os.path.join(d, "profile.json"), "w"))
    open(os.path.join(d, "clip.mp4"), "wb").write(b"0")
    try:
        je.build_track(d); refused = False
    except ValueError:
        refused = True
    check("videos are refused", refused)

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
