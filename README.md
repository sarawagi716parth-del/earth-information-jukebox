# The Earth Information Jukebox

NASA Space Apps Challenge 2026. NASA Earth images you can hear.

Pick a NASA image, press Play, and a line sweeps the picture from left to right while music plays what the
picture shows. The page shows the image with its description on the left, and the sound with its
description on the right. You can also click any spot on the image (or use the arrow keys) to hear and
hear spoken what is at that spot, and you can upload your own image.

## Team
- Parth Sarawagi:narrative lead, researcher [@sarawagi716parth-del](https://github.com/sarawagi716parth-del)
- Shivraj Tripathi: researcher, developer 
- Swayam Raj Gupta: researcher, prototype and video making
- AP: researcher, developer
- Arpit Maurya: prototype and video making, researcher

## How we built it
See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the real timeline: what we built on 14 and 15 November, what went wrong, what we changed and how we used AI. The demo video (29 seconds) and the 7-slide presentation (`CodeHub_Earth_Information_Jukebox.pptx`) are linked from our submission page.

## Two modes
- **Standard mode**: for sighted users. Click or drag on the picture to hear a spot. The place name, the value and
  the coordinates show under the picture.
- **Accessible mode** (press `A`, or use the switch at the top right): for blind and low-vision users. Everything is
  spoken aloud and works from the keyboard, with larger text and a black and white, high-contrast layout.

| Key (Accessible mode) | What it does |
| --- | --- |
| Space | Play or pause the sound |
| Arrow keys (Shift = bigger steps) | Move around the picture; hear a note, the place name and what is there |
| W | Where am I: place, value and coordinates |
| 1, 2, 3 | Choose a track |
| I / S | Describe the image / describe the sound |
| H | Hear the list of keys |
| V | Built-in voice off or on (turn it off if you use your own screen reader) |
| Esc | Stop talking |
| A | Back to Standard mode |

## Place names
When you explore a world map, the page says where you are, for example "Maharashtra, India" or "Arabian Sea", and
then what the picture shows there, for example "Lightning here, 8 flash pixels". The names come from
`static/places.json`, a quarter-degree lookup grid built from Natural Earth (public domain) by
`tools/build_places.py`. It covers the states and provinces of every country, plus oceans and seas.

## Run it (Windows)
Double-click `run_jukebox.bat`. It installs the packages, builds the tracks and opens http://127.0.0.1:5000.

Manual way:
```
pip install -r requirements.txt
python build_tracks.py
python app.py
```
Run the checks: `python tests/test_engine.py` (28 checks).

## The tracks (all images are official NASA files)
| Track | NASA page | How the colours are read |
| --- | --- | --- |
| Ocean currents coloured by sea surface temperature | https://svs.gsfc.nasa.gov/3912/ | NASA's colour bar file (0 to 32 degrees C) |
| Aerosols around the world, 19 August 2025 | https://svs.gsfc.nasa.gov/5669/ | NASA's legend file (sulfate, dust, black carbon, sea salt) |
| Lightning seen from the International Space Station | https://svs.gsfc.nasa.gov/5011/ | Yellow flash dots |
| Your own upload | - | Colour scale learned from the picture itself |

## How an image becomes music
1. **Read the meaning of the colours.** Either from NASA's colour bar or legend, from a colour bar drawn
   inside the picture, or, with no scale at all, learned from the picture: the engine finds the colours the
   picture uses, links colours that sit next to each other on the map, and takes the longest chain as the
   colour scale (the bluest end is "low"). On our 13 Nov 2026 test map this matched a hand-made scale with a
   rank agreement of 0.998.
2. **Sweep left to right** in 64 slices (8 seconds). Time = left to right, and the sound moves from the left
   ear to the right ear.
3. **Three bands, three instruments** (top, middle, bottom; on world maps: north, tropics, south). Never more
   than 3 notes at once, because listeners lose track beyond that.
4. **Higher value = higher note** on one pentatonic scale, so everything sounds good together.
5. **No data = silence**, so the silences draw the shape of the land, the empty sky or the storm-free ocean.
6. Three reading modes: `values` (numbers such as temperature), `categories` (kinds such as dust or smoke:
   kind = instrument, height = pitch, amount = loudness) and `events` (dots such as lightning flashes).

## Folder layout
```
app.py               web page server (Flask)
jukebox_engine.py    the engine: image in, notes + descriptions + audio out
build_tracks.py      builds every track in packs/
packs/<track>/       image + NASA colour bar + profile.json (settings), and the built
                     score.json, grid.json (Explore mode), track.json (texts), sonified.wav
static/              index.html, style.css, app.js
tests/test_engine.py checks
static/places.json   place-name lookup grid (Natural Earth)
tools/build_places.py  rebuilds static/places.json
```

## References
- NASA SVS 3912, Global Sea Surface Currents and Temperature (ECCO2 model, MIT/JPL): https://svs.gsfc.nasa.gov/3912/
- NASA SVS 5669, GEOS Aerosols (2025): https://svs.gsfc.nasa.gov/5669/
- NASA SVS 5011, ISS Lightning Imaging Sensor: https://svs.gsfc.nasa.gov/5011/
- Challenge: https://www.spaceappschallenge.org/2026/challenges/the-earth-information-jukebox/
- Natural Earth (public domain), admin-1 states and provinces and marine polygons, used for place names: https://www.naturalearthdata.com
- Libraries: Flask, OpenCV, NumPy, SciPy; browser Web Audio and Web Speech APIs.
- AI use: the engine, page and documentation were written with help from Claude (Anthropic). All data comes from the NASA files above.
