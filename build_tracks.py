"""Builds every track in packs/ from its NASA image. Run:  python build_tracks.py"""
import os
import jukebox_engine as je

ROOT = os.path.dirname(os.path.abspath(__file__))
for name in sorted(os.listdir(os.path.join(ROOT, "packs"))):
    d = os.path.join(ROOT, "packs", name)
    if os.path.isfile(os.path.join(d, "profile.json")):
        r = je.build_track(d)
        print(f"built {name}: {len(r['notes'])} notes, {r['duration']:.0f} s")
