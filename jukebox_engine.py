"""
jukebox_engine.py  (engine v3, images only)

Turns one NASA image into music that describes it.

How it works, in plain words:
  1. Read the picture and work out what each colour MEANS (a temperature, an aerosol type, a lightning flash).
  2. Sweep across the picture from left to right, like a radar line. Time = left to right, and the sound
     moves from your left ear to your right ear at the same time.
  3. The picture is cut into three horizontal bands (top, middle, bottom). Each band has its own instrument.
  4. Inside a band: higher value = higher note on one shared pentatonic scale. No data (land on an ocean
     map, empty sky, black space) = silence, so you can hear the shapes of the empty areas too.

Three ways to read a picture (the "type" in profile.json):
  * "values"     - colours stand for numbers (temperature, tree height). The colour scale comes from:
                   "palette" copied from NASA's colour bar file, or "box" = the colour bar drawn inside the
                   picture, or "auto" = the engine learns the colour ramp from the picture itself.
  * "categories" - colours stand for kinds of things (dust, smoke, sea salt, sulfate). Kind = instrument,
                   position = pitch, amount = loudness.
  * "events"     - bright dots stand for events (lightning flashes). Each cluster of dots = a note;
                   height = pitch, number of dots = loudness and speed. No dots = silence.

Outputs per track folder: score.json (notes), grid.json (Explore mode), track.json (texts for the page),
sonified.wav. Needs only: opencv-python, numpy, scipy.
"""
import json
import os

import cv2
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve
from scipy.sparse.csgraph import minimum_spanning_tree, shortest_path
from scipy.spatial import cKDTree

SR = 44100
STEPS_PER_SECOND = 8                 # one step = one 16th note at 120 bpm
WORK_W = 480                         # pictures are resized to this width (height keeps the aspect ratio)
PENTA = (0, 2, 4, 7, 9)              # C major pentatonic: C D E G A, so any notes together sound fine
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp")

DEFAULT_BANDS = [
    {"name": "top", "label": "top third", "top": 0.0, "bottom": 1 / 3, "instrument": "marimba", "every_steps": 2, "offset_steps": 0},
    {"name": "middle", "label": "middle third", "top": 1 / 3, "bottom": 2 / 3, "instrument": "strings", "every_steps": 4, "offset_steps": 0},
    {"name": "bottom", "label": "bottom third", "top": 2 / 3, "bottom": 1.0, "instrument": "pluck", "every_steps": 2, "offset_steps": 1},
]


# ---------------------------------------------------------------- small helpers
def scale_notes(lo_midi, hi_midi):
    return [m for m in range(lo_midi, hi_midi + 1) if m % 12 in PENTA]


def pick_note(notes, frac):
    frac = float(np.clip(frac, 0.0, 1.0))
    return notes[int(round(frac * (len(notes) - 1)))]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def hex_to_bgr(h):
    h = h.lstrip("#")
    return [int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)]


def load_image(path, work_w=WORK_W):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {path}")
    h, w = img.shape[:2]
    work_h = max(1, int(round(work_w * h / w)))
    return cv2.resize(img, (work_w, work_h), interpolation=cv2.INTER_AREA)


def box_px(box, shape):
    """Box given as fractions [x0, y0, x1, y1] of the picture -> pixel box."""
    H, W = shape[:2]
    x0, y0, x1, y1 = box
    return int(round(x0 * W)), int(round(y0 * H)), int(round(x1 * W)), int(round(y1 * H))


def hsv_full(px_bgr):
    """-> hue in degrees (0-360), saturation 0-1, brightness 0-255 for an (N,3) BGR array."""
    px = np.clip(px_bgr, 0, 255).astype(np.uint8).reshape(-1, 1, 3)
    hsv = cv2.cvtColor(px, cv2.COLOR_BGR2HSV_FULL)[:, 0, :].astype(np.float32)
    return hsv[:, 0] * 360.0 / 256.0, hsv[:, 1] / 255.0, hsv[:, 2]


def lon_of(frac):
    lon = -180 + frac * 360
    return f"{abs(lon):.0f} degrees {'west' if lon < 0 else 'east'}" if abs(lon) > 0.5 else "0 degrees"


# ---------------------------------------------------------------- colour scale (values)
class ColourScale:
    """Turns colours back into numbers.
    scale config options:
      {"palette": [[value, "#rrggbb"], ...]}   copied from the NASA colour bar file
      {"box": [x0,y0,x1,y1], "min": a, "max": b} the colour bar drawn inside the picture (left = min)
      {"auto": true}                             learn the colour ramp from the picture itself (relative 0-1)
    "match": "rgb" (flat maps) or "hue" (pictures where strokes are dimmed or see-through)."""

    def __init__(self, img, cfg):
        self.relative = False
        if "palette" in cfg:
            pts = sorted(cfg["palette"], key=lambda p: p[0])
            vals = np.array([p[0] for p in pts], dtype=np.float32)
            bgr = np.array([hex_to_bgr(h) for _, h in pts], dtype=np.float32)
            self.values = np.linspace(vals[0], vals[-1], 256)
            self.colours = np.stack([np.interp(self.values, vals, bgr[:, c]) for c in range(3)], axis=1)
        elif "box" in cfg:
            x0, y0, x1, y1 = box_px(cfg["box"], img.shape)
            strip = np.median(img[y0:y1, x0:x1].astype(np.float32), axis=0)
            # tick marks drawn on the bar show up as odd columns: replace them with the median of neighbours
            k = 7
            pad = np.pad(strip, ((k // 2, k // 2), (0, 0)), mode="edge")
            self.colours = np.stack([np.median(pad[i:i + k], axis=0) for i in range(len(strip))])
            self.values = np.linspace(cfg["min"], cfg["max"], len(self.colours))
        else:
            self.colours, self.values = learn_colour_ramp(img, cfg)
            self.relative = True
        self.vmin, self.vmax = float(self.values[0]), float(self.values[-1])
        self.match = cfg.get("match", "rgb")
        if self.match == "auto":
            # rainbow-style scales change hue steadily from end to end: then match by hue, which also reads
            # dim or see-through strokes. Scales that pass through white (blue-white-red) need full colour.
            h, sat, _ = hsv_full(self.colours)
            h = np.where(h > 300, h - 360, h)
            steady = np.all(np.diff(h) <= 2) or np.all(np.diff(h) >= -2)
            self.match = "hue" if steady and sat.min() > 0.4 else "rgb"
        self.max_dist = cfg.get("max_colour_distance", 60.0)
        self.min_saturation = cfg.get("min_saturation", 0.3)
        self.min_brightness = cfg.get("min_brightness", 40)
        if self.match == "hue":
            h, _, _ = hsv_full(self.colours)
            h = np.where(h > 300, h - 360, h)               # keep reds next to orange
            order = np.argsort(h)
            self.hues, self.hue_values = h[order], self.values[order]
        else:
            self.tree = cKDTree(self.colours)

    def decode(self, img):
        """-> (value per pixel, valid mask). Grey land, black background and text are not valid."""
        px = img.reshape(-1, 3).astype(np.float32)
        h, s, v = hsv_full(px)
        valid = (s >= self.min_saturation) & (v >= self.min_brightness)
        if self.match == "hue":
            h = np.where(h > 300, h - 360, h)
            vals = np.interp(h, self.hues, self.hue_values)
            valid &= (h > self.hues[0] - self.max_dist) & (h < self.hues[-1] + self.max_dist)
        else:
            dist, idx = self.tree.query(px)
            vals = self.values[idx]
            valid &= dist < self.max_dist
        return vals.reshape(img.shape[:2]), valid.reshape(img.shape[:2])


def learn_colour_ramp(img, cfg):
    """No colour bar? Learn it. Most science colour scales are one smooth line through colour space
    (dark blue -> light blue -> white -> red, or blue -> green -> yellow -> red). We find the colours the
    picture uses, connect them with the shortest tree, and take the longest path through that tree as the
    colour ramp. The end that is more blue is called 'low' (the usual convention for cold or small).
    Values are relative: 0 = one end of the ramp, 1 = the other end."""
    px = img.reshape(-1, 3).astype(np.float32)
    _, s, v = hsv_full(px)
    # only use calm pixels: edges between two colours (coastlines, text) make in-between colours
    # that are not on the colour scale, so drop pixels that differ a lot from their neighbours
    lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    blur = cv2.blur(lab_img, (5, 5))
    calm = (np.linalg.norm(lab_img - blur, axis=2) < cfg.get("calm_threshold", 6)).reshape(-1)
    keep = px[(s >= cfg.get("ramp_min_saturation", 0.25)) & (v >= cfg.get("min_brightness", 40)) & calm]
    if len(keep) < 50:
        raise ValueError("Not enough coloured pixels to learn a colour scale")
    rng = np.random.default_rng(0)
    keep = keep[rng.choice(len(keep), min(len(keep), 20000), replace=False)]
    lab = cv2.cvtColor(keep.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    k = int(cfg.get("ramp_colours", 24))
    _, labels, centres = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 3,
                                    cv2.KMEANS_PP_CENTERS)
    sizes = np.bincount(labels.reshape(-1), minlength=k) / len(labels)
    centres = centres[sizes >= 0.005]                     # ignore rare colours (labels, specks)
    # Which colours touch each other in the picture? Real data fields change smoothly, so colours that sit
    # next to each other on the map are next to each other on the colour scale.
    all_lab = lab_img.reshape(-1, 3)
    ok_px = (s >= cfg.get("ramp_min_saturation", 0.25)) & (v >= cfg.get("min_brightness", 40))
    dist_c, lab_idx = cKDTree(centres).query(all_lab)
    lab_idx[~ok_px | (dist_c > 25)] = -1
    L = lab_idx.reshape(img.shape[:2])
    n = len(centres)
    touch = np.zeros((n, n))
    pairs = []
    for off in (1, 2, 3):                                  # near neighbours, so thin white bands do not cut the scale
        pairs += [(L[:, :-off], L[:, off:]), (L[:-off, :], L[off:, :])]
    for a_, b_ in pairs:
        m = (a_ >= 0) & (b_ >= 0) & (a_ != b_)
        np.add.at(touch, (a_[m], b_[m]), 1)
    touch = touch + touch.T
    d = np.linalg.norm(centres[:, None, :] - centres[None, :, :], axis=2)
    cost = np.where(touch > 0, d / np.sqrt(touch + 1), 0)        # close in colour AND often touching = cheap
    tree = minimum_spanning_tree(cost).toarray()
    if (tree > 0).sum() < n - 1:                                   # some colours never touch: fall back to colour distance
        tree = minimum_spanning_tree(d).toarray()
    tree = (tree > 0) * d
    tree = tree + tree.T
    dist = shortest_path(tree, directed=False)
    a = int(np.argmax(dist[0])); b = int(np.argmax(dist[a]))          # two ends of the longest path
    _, pred = shortest_path(tree, directed=False, indices=a, return_predecessors=True)
    path = [b]
    while path[-1] != a:
        path.append(int(pred[path[-1]]))
    path = path[::-1]
    cen_bgr = cv2.cvtColor(centres.reshape(-1, 1, 3).clip(0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(-1, 3).astype(np.float32)
    ramp = cen_bgr[path]
    blueness = ramp[:, 0] - ramp[:, 2]                   # blue minus red
    if blueness[-1] > blueness[0]:
        ramp = ramp[::-1]; path = path[::-1]
    steps = np.r_[0, np.cumsum(np.linalg.norm(np.diff(centres[path], axis=0), axis=1))]
    pos = steps / max(steps[-1], 1e-6)
    values = np.linspace(0, 1, 256)
    colours = np.stack([np.interp(values, pos, ramp[:, c]) for c in range(3)], axis=1)
    return colours, values


# ---------------------------------------------------------------- the sweep
def band_rows(band, box, shape):
    x0, y0, x1, y1 = box_px(box, shape)
    return int(round(y0 + band["top"] * (y1 - y0))), int(round(y0 + band["bottom"] * (y1 - y0)))


def sweep_columns(profile, shape):
    x0, _, x1, _ = box_px(profile.get("map_box", [0, 0, 1, 1]), shape)
    n = profile.get("columns", 64)
    return [(x0 + int(c * (x1 - x0) / n), x0 + int((c + 1) * (x1 - x0) / n)) for c in range(n)]


def pan_of(c, n):
    return round(((c + 0.5) / n * 2 - 1) * 0.85, 2)


def ignore_mask(profile, shape):
    m = np.zeros(shape[:2], bool)
    for b in profile.get("ignore", []):
        x0, y0, x1, y1 = box_px(b, shape)
        m[y0:y1, x0:x1] = True
    return m


# ---------------------------------------------------------------- composer: values
def compose_values(img, profile):
    cfg = profile["scale"]
    scale = ColourScale(img, cfg)
    vals, valid = scale.decode(img)
    valid &= ~ignore_mask(profile, img.shape)
    box = profile.get("map_box", [0, 0, 1, 1])
    cols = sweep_columns(profile, img.shape)
    notes_scale = scale_notes(*profile.get("pitch_range_midi", [40, 88]))
    min_frac = profile.get("min_data_fraction", 0.3)
    bands = profile.get("bands", DEFAULT_BANDS)
    step_s = 1.0 / STEPS_PER_SECOND
    notes, cells = [], []
    for c, (x0, x1) in enumerate(cols):
        for b in bands:
            y0, y1 = band_rows(b, box, img.shape)
            ok = valid[y0:y1, x0:x1]
            frac = float(ok.mean())
            mean = float(vals[y0:y1, x0:x1][ok].mean()) if ok.any() else None
            cells.append({"col": c, "band": b["name"], "data_fraction": round(frac, 3),
                          "value": None if mean is None else round(mean, 2)})
            every, offset = b.get("every_steps", 2), b.get("offset_steps", 0)
            if (c - offset) % every != 0 or frac < min_frac:
                continue
            f01 = (mean - scale.vmin) / (scale.vmax - scale.vmin)
            notes.append({"t": round(c * step_s, 3), "col": c, "layer": b["name"], "instrument": b["instrument"],
                          "midi": pick_note(notes_scale, f01), "vel": round(0.55 + 0.45 * min(1.0, frac / 0.8), 2),
                          "pan": pan_of(c, len(cols)), "dur": round(every * step_s, 3), "value": round(mean, 2)})

    cell_min = profile.get("grid_min_fraction", min(0.4, profile.get("min_data_fraction", 0.3)))

    def cell_info(region_vals, region_ok, row_frac):
        if region_ok.mean() < cell_min:
            return None
        v = float(region_vals[region_ok].mean())
        return {"midi": pick_note(notes_scale, (v - scale.vmin) / (scale.vmax - scale.vmin)),
                "label": fmt_value(v, profile, scale), "instrument": "marimba"}

    grid = explore_grid(img, profile, lambda ys, ye, xs, xe, rf: cell_info(vals[ys:ye, xs:xe], valid[ys:ye, xs:xe], rf))
    meta = {"relative_scale": scale.relative, "vmin": scale.vmin, "vmax": scale.vmax}
    return notes, grid, cells, meta


def fmt_value(v, profile, scale):
    if scale.relative:
        return f"{round(v * 100)} percent of the way from the coolest colour to the warmest colour"
    unit = profile.get("unit", "")
    return f"{v:.1f} {unit}".strip()


# ---------------------------------------------------------------- composer: categories
def classify(img, classes, cfg):
    """-> (class index per pixel or -1, strength 0-1 per pixel). Matching is by hue so faint, see-through
    plumes still count; saturation and brightness thresholds come from each class."""
    px = img.reshape(-1, 3).astype(np.float32)
    h, s, v = hsv_full(px)
    best = np.full(len(px), -1); best_d = np.full(len(px), 1e9)
    for i, k in enumerate(classes):
        kh, ks, kv = hsv_full(np.array([hex_to_bgr(k["colour"])], np.float32))
        d = np.abs((h - kh[0] + 180) % 360 - 180)
        ok = (d <= k.get("hue_tolerance", 25)) & (s >= k.get("min_saturation", 0.25)) & (v >= k.get("min_brightness", 60))
        if "max_saturation" in k:
            ok &= s <= k["max_saturation"]
        take = ok & (d < best_d)
        best[take] = i; best_d[take] = d[take]
    strength = np.clip((v / 255.0) * np.clip(s * 2, 0, 1), 0, 1)
    return best.reshape(img.shape[:2]), np.where(best >= 0, strength, 0).reshape(img.shape[:2])


def compose_categories(img, profile):
    classes = profile["classes"]
    cls, strength = classify(img, classes, profile)
    cls[ignore_mask(profile, img.shape)] = -1
    box = profile.get("map_box", [0, 0, 1, 1])
    x0b, y0b, x1b, y1b = box_px(box, img.shape)
    cols = sweep_columns(profile, img.shape)
    notes_scale = scale_notes(*profile.get("pitch_range_midi", [48, 88]))
    max_voices = profile.get("max_voices", 2)
    min_cov = profile.get("min_coverage", 0.03)
    every = profile.get("every_steps", 2)
    step_s = 1.0 / STEPS_PER_SECOND
    notes, cells = [], []
    for c, (x0, x1) in enumerate(cols):
        col = cls[y0b:y1b, x0:x1]; st = strength[y0b:y1b, x0:x1]
        found = []
        for i, k in enumerate(classes):
            m = col == i
            cov = float((st * m).sum() / m.size)
            if m.any():
                rows = np.nonzero(m)[0]; w = st[m]
                yc = float(np.average(rows, weights=w + 1e-6)) / max(1, (y1b - y0b))
            else:
                yc = None
            cells.append({"col": c, "class": k["name"], "coverage": round(cov, 4), "height": None if yc is None else round(1 - yc, 3)})
            if cov >= min_cov:
                found.append((cov, i, yc))
        if c % every:
            continue
        for cov, i, yc in sorted(found, reverse=True)[:max_voices]:
            k = classes[i]
            notes.append({"t": round(c * step_s, 3), "col": c, "layer": k["name"], "instrument": k["instrument"],
                          "midi": pick_note(notes_scale, 1 - yc), "vel": round(float(np.clip(0.45 + cov * 3, 0.45, 1.0)), 2),
                          "pan": pan_of(c, len(cols)), "dur": round(every * step_s, 3), "value": round(cov, 4)})

    def cell_info(ys, ye, xs, xe, row_frac):
        region = cls[ys:ye, xs:xe]; st = strength[ys:ye, xs:xe]
        scores = [float((st * (region == i)).sum()) for i in range(len(classes))]
        if max(scores) < 0.08 * region.size:
            return None
        i = int(np.argmax(scores))
        phrase = profile.get("category_phrase")
        label = phrase.format(name=classes[i]["name"].lower()) if phrase else classes[i]["name"]
        return {"midi": pick_note(notes_scale, 1 - row_frac), "label": label, "instrument": classes[i]["instrument"]}

    grid = explore_grid(img, profile, cell_info)
    return notes, grid, cells, {}


# ---------------------------------------------------------------- composer: events
def compose_events(img, profile):
    m = profile["match"]
    px = img.reshape(-1, 3).astype(np.float32)
    h, s, v = hsv_full(px)
    lo, hi = m["hue_degrees"]
    dots = ((h >= lo) & (h <= hi) & (s >= m["min_saturation"]) & (v >= m["min_brightness"])).reshape(img.shape[:2])
    dots &= ~ignore_mask(profile, img.shape)
    box = profile.get("map_box", [0, 0, 1, 1])
    x0b, y0b, x1b, y1b = box_px(box, img.shape)
    cols = sweep_columns(profile, img.shape)
    n_bins = profile.get("height_bins", 12)
    notes_scale = scale_notes(*profile.get("pitch_range_midi", [55, 91]))
    max_voices = profile.get("max_voices", 3)
    min_px = profile.get("min_pixels", 2)
    step_s = 1.0 / STEPS_PER_SECOND
    counts = np.zeros((len(cols), n_bins))
    edges = np.linspace(y0b, y1b, n_bins + 1).astype(int)
    for c, (x0, x1) in enumerate(cols):
        for j in range(n_bins):
            counts[c, j] = dots[edges[j]:edges[j + 1], x0:x1].sum()
    p90 = np.percentile(counts[counts >= min_px], 90) if (counts >= min_px).any() else 1.0
    notes, cells = [], []
    for c in range(len(cols)):
        busy = [(counts[c, j], j) for j in range(n_bins) if counts[c, j] >= min_px]
        cells.append({"col": c, "dots": int(counts[c].sum()), "bins": [int(x) for x in counts[c]]})
        for cnt, j in sorted(busy, reverse=True)[:max_voices]:
            level = min(1.0, cnt / p90)
            every = 1 if level >= 0.6 else 2                   # busy storms repeat faster
            if c % every:
                continue
            height = 1 - (j + 0.5) / n_bins
            notes.append({"t": round(c * step_s, 3), "col": c, "layer": "flashes", "instrument": profile.get("instrument", "bell"),
                          "midi": pick_note(notes_scale, height), "vel": round(float(np.clip(np.sqrt(level), 0.3, 1.0)), 2),
                          "pan": pan_of(c, len(cols)), "dur": 0.25, "value": int(cnt)})

    def cell_info(ys, ye, xs, xe, row_frac):
        n = int(dots[ys:ye, xs:xe].sum())
        if n < 1:
            return None
        return {"midi": pick_note(notes_scale, 1 - row_frac), "label": f"Lightning here, {n} flash pixel{'s' if n != 1 else ''}", "instrument": "bell"}

    grid = explore_grid(img, profile, cell_info)
    return notes, grid, cells, {"p90": float(p90)}


# ---------------------------------------------------------------- Explore grid (detail on demand in the page)
def explore_grid(img, profile, cell_fn):
    box = profile.get("map_box", [0, 0, 1, 1])
    x0b, y0b, x1b, y1b = box_px(box, img.shape)
    gc = profile.get("grid_cols", 48)
    gr = profile.get("grid_rows", max(8, int(round(gc * (y1b - y0b) / max(1, (x1b - x0b))))))
    rows = []
    for r in range(gr):
        ys, ye = y0b + r * (y1b - y0b) // gr, y0b + (r + 1) * (y1b - y0b) // gr
        row = []
        for c in range(gc):
            xs, xe = x0b + c * (x1b - x0b) // gc, x0b + (c + 1) * (x1b - x0b) // gc
            row.append(cell_fn(ys, max(ye, ys + 1), xs, max(xe, xs + 1), (r + 0.5) / gr))
        rows.append(row)
    return {"cols": gc, "rows": gr, "box": box, "cells": rows}


# ---------------------------------------------------------------- spoken / written description of the audio
def verb(instrument, singular, plural):
    return plural if instrument == "strings" else singular


def describe_audio(profile, notes, cells, meta, duration):
    n_cols = profile.get("columns", 64)
    equirect = profile.get("projection") == "equirect"
    t_of = lambda c: c / STEPS_PER_SECOND

    def where(c):
        return lon_of((c + 0.5) / n_cols) if equirect else ["the left edge", "the left side", "the centre", "the right side", "the right edge"][min(4, int((c + 0.5) / n_cols * 5))]

    def spans(cols_list):
        """group consecutive columns -> list of (start, end)"""
        out = []
        for c in sorted(cols_list):
            if out and c <= out[-1][1] + 2:
                out[-1][1] = c
            else:
                out.append([c, c])
        return out

    def spans_strict(cols_list):
        out = []
        for c in sorted(cols_list):
            if out and c == out[-1][1] + 1:
                out[-1][1] = c
            else:
                out.append([c, c])
        return out

    lines = [f"The sweep lasts {duration:.0f} seconds and moves from the left edge of the picture to the right edge. "
             "The sound moves from your left ear to your right ear with it." +
             (" On this world map, the left edge is 180 degrees west, in the middle of the Pacific Ocean, and the right edge is back at the same place, 180 degrees east." if equirect else "")]
    t = profile["type"]
    if t == "values":
        unit = "" if meta.get("relative_scale") else profile.get("unit", "")
        lines.append("Higher notes mean " + profile.get("high_means", "higher values") + ". Silence means " + profile.get("silence_means", "no data") + ".")
        for b in profile.get("bands", DEFAULT_BANDS):
            bc = [x for x in cells if x["band"] == b["name"]]
            bn = [n for n in notes if n["layer"] == b["name"]]
            if not bn:
                lines.append(f"The {b['instrument']} ({b['label']}) {verb(b['instrument'], 'stays', 'stay')} silent the whole time.")
                continue
            hi = max(bn, key=lambda n: n["value"]); lo = min(bn, key=lambda n: n["value"])
            fmt = (lambda v: f"{v:.0f} {unit}".strip()) if unit else (lambda v: f"{round(v * 100)} percent")
            s = (f"The {b['instrument']} {verb(b['instrument'], 'plays', 'play')} the {b['label']}. {'Their' if b['instrument'] == 'strings' else 'Its'} highest note comes at about {hi['t']:.1f} seconds, "
                 f"near {where(hi['col'])} ({fmt(hi['value'])}), and {'their' if b['instrument'] == 'strings' else 'its'} lowest at about {lo['t']:.1f} seconds, near {where(lo['col'])} ({fmt(lo['value'])}).")
            gaps = [sp for sp in spans([x["col"] for x in bc if x["data_fraction"] < profile.get("min_data_fraction", 0.3)]) if sp[1] - sp[0] >= 2]
            if gaps:
                s += f" {'They go' if b['instrument'] == 'strings' else 'It goes'} quiet " + "; ".join(f"from {t_of(a):.1f} to {t_of(b2 + 1):.1f} seconds ({where(a)} to {where(b2)})" for a, b2 in gaps[:4]) + \
                     f", where there is {profile.get('silence_means', 'no data')}."
            lines.append(s)
    elif t == "categories":
        lines.append("Each kind has its own instrument: " + ", ".join(f"{k['name']} is the {k['instrument']}" for k in profile["classes"]) +
                     ". Higher notes mean the colour sits higher up in the picture" + (" (further north)" if equirect else "") +
                     ". Louder means more of it. Only the two biggest kinds in each slice play, so the sound stays clear.")
        for k in profile["classes"]:
            kn = [n for n in notes if n["layer"] == k["name"]]
            if not kn:
                lines.append(f"{k['name']}: not heard.")
                continue
            sp = sorted(spans([n["col"] for n in kn]), key=lambda s: s[1] - s[0], reverse=True)[:3]
            sp = [x for x in sp if x[1] > x[0]] or sp[:1]
            lines.append(f"{k['name']} ({k['instrument']}) is heard most " +
                         "; ".join(f"from {t_of(a):.1f} to {t_of(b2 + 1):.1f} seconds ({where(a)} to {where(b2)})" for a, b2 in sorted(sp)) + ".")
    else:
        lines.append("Each bell note is a cluster of flashes. Higher notes mean the flashes are higher up in the picture"
                     + (" (further north)" if equirect else "") + ". Louder and faster means more flashes. Silence means no lightning.")
        dots = np.array([x["dots"] for x in cells], float)
        smooth = np.convolve(dots, np.ones(5) / 5, mode="same")
        peaks = []
        for c in np.argsort(-smooth):
            if smooth[c] <= 0 or len(peaks) == 3:
                break
            if all(abs(c - p) >= 8 for p in peaks):
                peaks.append(int(c))
        lines.append("The busiest moments are " + "; ".join(
            f"around {t_of(c):.1f} seconds ({where(c)})" for c in sorted(peaks)) + ".")
        quiet = [s for s in spans_strict([i for i, d in enumerate(dots) if d == 0]) if s[1] - s[0] >= 1]
        if quiet:
            lines.append("Silences, where there is no lightning: " + "; ".join(
                f"{t_of(a):.1f} to {t_of(b2 + 1):.1f} seconds ({where(a)} to {where(b2)})" for a, b2 in quiet[:5]) + ".")
    return "\n".join(lines)


# ---------------------------------------------------------------- instruments
def _env(n, attack, tau):
    t = np.arange(n) / SR
    e = np.exp(-t / tau)
    a = max(1, int(attack * SR))
    e[:a] *= np.linspace(0, 1, a)
    return e


def _marimba(f, dur):
    n = int(1.3 * SR); t = np.arange(n) / SR
    tau = 0.30 * (220.0 / f) ** 0.35
    return np.sin(2 * np.pi * f * t) * _env(n, 0.002, tau) + 0.3 * np.sin(2 * np.pi * 3.93 * f * t) * _env(n, 0.001, tau * 0.22)


def _bell(f, dur):
    n = int(2.0 * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for ratio, amp, life in ((1.0, 1.0, 0.8), (2.76, 0.4, 0.4), (5.4, 0.2, 0.22)):
        x += amp * np.sin(2 * np.pi * f * ratio * t) * _env(n, 0.001, life)
    return x * 0.6


def _pluck(f, dur):
    n = int(1.0 * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, 8):
        if f * k > 8000:
            break
        x += (1.0 / k) * np.sin(2 * np.pi * f * k * t) * _env(n, 0.003, 0.42 / (1 + 0.7 * k))
    return x * 0.8


def _strings(f, dur):
    n = int((dur + 0.35) * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    x *= 1 + 0.004 * np.sin(2 * np.pi * 5 * t)
    e = np.ones(n)
    a, r = int(0.08 * SR), int(0.35 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] = np.linspace(1, 0, r)
    return x * e * 0.45


def _flute(f, dur):
    n = int((dur + 0.25) * SR); t = np.arange(n) / SR
    breath = np.random.default_rng(int(f)).standard_normal(n) * 0.04
    x = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(4 * np.pi * f * t) + breath
    e = np.ones(n); a, r = int(0.05 * SR), int(0.2 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] = np.linspace(1, 0, r)
    return x * e * 0.5


def _drum(f, dur):
    n = int(0.6 * SR); t = np.arange(n) / SR
    sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    x = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * _env(n, 0.001, 0.14)
    noise = np.random.default_rng(int(f)).standard_normal(n) * _env(n, 0.001, 0.03) * 0.25
    return x + noise


INSTRUMENTS = {"marimba": _marimba, "bell": _bell, "pluck": _pluck, "strings": _strings, "flute": _flute, "drum": _drum}
GAINS = {"marimba": 0.50, "bell": 0.30, "pluck": 0.42, "strings": 0.34, "flute": 0.40, "drum": 0.55}


def render(notes, duration, tail=2.0):
    out = np.zeros((int((duration + tail) * SR), 2))
    for q in notes:
        sig = INSTRUMENTS[q["instrument"]](hz(q["midi"]), q["dur"]) * GAINS[q["instrument"]] * q["vel"]
        s = int(q["t"] * SR); e = min(len(out), s + len(sig))
        th = (q["pan"] + 1) * np.pi / 4                     # equal-power pan: left ear -> right ear
        out[s:e, 0] += sig[:e - s] * np.cos(th)
        out[s:e, 1] += sig[:e - s] * np.sin(th)
    # soft tick at the start and end of the sweep so listeners know where the picture begins and ends
    for t0 in (0.0, duration):
        s = int(t0 * SR); n = int(0.03 * SR)
        tick = np.sin(2 * np.pi * 2000 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.006 * SR)) * 0.15
        side = 0 if t0 == 0 else 1
        if s + n <= len(out):
            out[s:s + n, side] += tick
    rng = np.random.default_rng(7)
    n_ir = int(1.6 * SR)
    ir = rng.standard_normal(n_ir) * np.exp(-np.arange(n_ir) / SR / 0.4)
    ir = np.convolve(ir, np.ones(12) / 12, mode="same"); ir /= np.sqrt(np.sum(ir ** 2))
    wet = np.stack([fftconvolve(out[:, c], np.roll(ir, c * 37))[:len(out)] for c in range(2)], axis=1)
    mix = out + 0.18 * wet
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = np.tanh(1.2 * mix / peak) / np.tanh(1.2) * 0.89     # about -1 dBFS
    return mix


# ---------------------------------------------------------------- build one track
COMPOSERS = {"values": compose_values, "categories": compose_categories, "events": compose_events}


def sonify_image(img, profile):
    notes, grid, cells, meta = COMPOSERS[profile["type"]](img, profile)
    duration = profile.get("columns", 64) / STEPS_PER_SECOND
    return notes, grid, cells, meta, duration


def build_track(track_dir):
    """Reads <track_dir>/profile.json + its image, writes score.json, grid.json, track.json, sonified.wav."""
    with open(os.path.join(track_dir, "profile.json"), encoding="utf-8") as fh:
        profile = json.load(fh)
    path = os.path.join(track_dir, profile["image"])
    if os.path.splitext(path)[1].lower() not in IMAGE_EXT:
        raise ValueError("The jukebox only takes images (jpg, png, tif, webp, bmp)")
    img = load_image(path, profile.get("work_width", WORK_W))
    notes, grid, cells, meta, duration = sonify_image(img, profile)
    audio = render(notes, duration)
    write_outputs(track_dir, profile, notes, grid, cells, meta, duration, audio)
    return {"notes": notes, "grid": grid, "cells": cells, "meta": meta, "audio": audio, "duration": duration,
            "profile": profile, "image": img}


def write_outputs(track_dir, profile, notes, grid, cells, meta, duration, audio):
    score = {"bpm": 120, "step_seconds": 1.0 / STEPS_PER_SECOND, "duration": duration, "notes": notes}
    track = {"id": profile["id"], "title": profile["title"], "source": profile.get("nasa_source", ""),
             "image": profile["image"], "projection": profile.get("projection", "none"), "map_box": profile.get("map_box", [0, 0, 1, 1]), "duration": duration,
             "image_description": profile.get("image_description", ""),
             "audio_description": describe_audio(profile, notes, cells, meta, duration),
             "how_to_listen": profile.get("how_to_listen", ""), "credit": profile.get("credit", ""),
             "empty_label": profile.get("empty_label", "Nothing here, no data"),
             "empty_label_land": profile.get("empty_label_land", "")}

    def dump(name, obj):
        with open(os.path.join(track_dir, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, separators=(",", ":"))

    dump("score.json", score); dump("grid.json", grid); dump("track.json", track)
    wavfile.write(os.path.join(track_dir, "sonified.wav"), SR, (audio * 32767).astype(np.int16))


def auto_profile(title="Your image"):
    """Profile for an uploaded picture with no settings: learn the colour scale from the picture."""
    return {"id": "upload", "title": title, "type": "values", "image": "image.png", "columns": 64,
            "scale": {"auto": True, "match": "auto", "max_colour_distance": 45, "min_saturation": 0.25, "min_brightness": 40},
            "min_data_fraction": 0.25, "bands": DEFAULT_BANDS, "pitch_range_midi": [40, 88],
            "empty_label": "No colour data at this spot",
            "high_means": "colours closer to the warm or bright end of the picture's colour scale",
            "silence_means": "grey, black or white areas with no colour data",
            "image_description": "Uploaded picture. The jukebox found its colour scale automatically: it treats the bluest end of the "
                                 "picture's colours as low and the other end as high. Without the picture's colour bar the numbers are "
                                 "relative, not real units."}


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs")
    for dirpath, _, files in os.walk(root):
        if "profile.json" in files:
            res = build_track(dirpath)
            print(f"built {dirpath}: {len(res['notes'])} notes, {res['duration']:.1f} s")
