"""
The Earth Information Jukebox - web page.

Run:   python app.py      then open http://127.0.0.1:5000
Left side:  the NASA image, and below it a description of the image.
Right side: the sound, and below it a description of the sound.
You can also upload your own image; the engine learns its colour scale automatically.
"""
import json
import os
import uuid

from flask import Flask, abort, jsonify, request, send_from_directory

import jukebox_engine as je

ROOT = os.path.dirname(os.path.abspath(__file__))
PACKS = os.path.join(ROOT, "packs")
UPLOADS = os.path.join(ROOT, "uploads")
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def ensure_built(track_dir):
    needed = ["track.json", "score.json", "grid.json", "sonified.wav"]
    prof = os.path.join(track_dir, "profile.json")
    newest_input = max(os.path.getmtime(prof), os.path.getmtime(je.__file__))
    if not all(os.path.exists(os.path.join(track_dir, f)) for f in needed) or \
            os.path.getmtime(os.path.join(track_dir, "track.json")) < newest_input:
        je.build_track(track_dir)


def track_payload(base_url, track_dir):
    with open(os.path.join(track_dir, "track.json"), encoding="utf-8") as fh:
        t = json.load(fh)
    t["image_url"] = f"{base_url}/{t['image']}"
    t["audio_url"] = f"{base_url}/sonified.wav"
    t["score_url"] = f"{base_url}/score.json"
    t["grid_url"] = f"{base_url}/grid.json"
    with open(os.path.join(track_dir, "profile.json"), encoding="utf-8") as fh:
        p = json.load(fh)
    t["instruments"] = instrument_legend(p)
    t["listen_for"] = p.get("listen_for", "")
    return t


def instrument_legend(p):
    if p["type"] == "categories":
        return [{"instrument": k["instrument"], "meaning": k["name"], "colour": k["colour"]} for k in p["classes"]]
    if p["type"] == "events":
        return [{"instrument": p.get("instrument", "bell"), "meaning": "lightning flashes (higher note = further north)"}]
    return [{"instrument": b["instrument"], "meaning": b["label"]} for b in p.get("bands", je.DEFAULT_BANDS)]


@app.get("/")
def index():
    return send_from_directory(os.path.join(ROOT, "static"), "index.html")


@app.get("/api/tracks")
def tracks():
    out = []
    for name in sorted(os.listdir(PACKS)):
        d = os.path.join(PACKS, name)
        if os.path.isfile(os.path.join(d, "profile.json")):
            ensure_built(d)
            with open(os.path.join(d, "profile.json"), encoding="utf-8") as fh:
                order = json.load(fh).get("order", 99)
            out.append((order, track_payload(f"/packs/{name}", d)))
    return jsonify([t for _, t in sorted(out, key=lambda x: x[0])])


@app.get("/packs/<name>/<path:filename>")
def pack_file(name, filename):
    return send_from_directory(os.path.join(PACKS, name), filename)


@app.get("/uploads/<name>/<path:filename>")
def upload_file(name, filename):
    return send_from_directory(os.path.join(UPLOADS, name), filename)


@app.post("/api/upload")
def upload():
    f = request.files.get("image")
    if f is None or not f.filename:
        abort(400, "No image sent")
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in je.IMAGE_EXT:
        return jsonify({"error": "The jukebox only takes images: jpg, png, tif, webp or bmp. Videos are not supported."}), 400
    tid = uuid.uuid4().hex[:10]
    d = os.path.join(UPLOADS, tid)
    os.makedirs(d, exist_ok=True)
    image_name = "image" + ext
    f.save(os.path.join(d, image_name))
    profile = je.auto_profile(title=os.path.splitext(os.path.basename(f.filename))[0])
    profile["id"] = tid
    profile["image"] = image_name
    with open(os.path.join(d, "profile.json"), "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=1)
    try:
        je.build_track(d)
    except ValueError as e:
        return jsonify({"error": f"Could not read this image: {e}"}), 400
    return jsonify(track_payload(f"/uploads/{tid}", d))


if __name__ == "__main__":
    os.makedirs(UPLOADS, exist_ok=True)
    print("The Earth Information Jukebox is running: open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
