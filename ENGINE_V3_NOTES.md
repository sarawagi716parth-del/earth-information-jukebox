# Engine v3 notes (15 Nov 2026)

## What changed
- Images only. Videos are refused (`build_track` raises an error, the upload page rejects them).
- Colour scale: NASA colour bar file, a bar drawn in the picture, or learned automatically from the picture.
- Three reading modes: values, categories, events.
- New Flask page: image and its description on the left, sound and its description on the right, Explore
  mode (click or arrow keys, spoken values), upload your own image, read-aloud button.
- The written description of the sound is generated from the actual notes (times, places, highest and
  lowest values, silences), so it always matches what plays.

## Measured results
- Sea surface temperature: zonal averages 60N 7.7, 30N 23.2, equator 28.4, 30S 19.5, 60S 2.5 degrees C,
  in line with known ocean averages. Pitch follows temperature (rank correlation above 0.95). No notes over land.
- Aerosols: dust (strings) heard from about 2.8 to 5 seconds over the Saharan plume; smoke (bell) over
  central Africa just below it.
- Lightning: 49 of 67 notes are low (south of the equator), matching the picture.
- Auto colour scale: 0.998 rank agreement with a hand-made scale on the 13 Nov 2026 map; 0.95 with NASA's
  bar on the ocean-currents picture.

## Dropped
- GEDI forest height globe (SVS 4950): its 3D shading changes the colours too much to read the bar reliably.

## Still open
- Find the NASA page for the 13 Nov 2026 sea temperature map (it works as an upload, in relative units).
- Run `cleanup_old_files.bat` once, then commit.
- Listening test with team members (eyes closed: can they say where the land and the warm water are?).

## Update, 15 Nov 2026 (afternoon): two modes, place names, new look
- Mode switch at the top right (or press A). Standard mode is for mouse and eyes. Accessible mode is for blind and
  low-vision users: self-voicing, full keyboard control (Space, arrows, W, I, S, H, V, Esc, 1 to 9), larger text,
  black and white high contrast, thick focus rings, one column. The choice is remembered in the browser.
- Explore now says the place name first, then the value: "Kasai-Occidental, Democratic Republic of the Congo.
  Lightning here, 8 flash pixels". Names come from static/places.json (Natural Earth admin-1 + marine polygons,
  quarter-degree grid, 4,817 names, 349 KB), built by tools/build_places.py.
- Checked that Natural Earth coastlines line up with all three NASA images (all are full-globe plate carree maps).
- Explore grid is finer: 96 by 48 cells (3.75 degrees) instead of 48 by 24. Drag on the picture to scan it.
- Over land on the ocean map the page says "This is land, so there is no ocean temperature here".
- New page design: track cards with thumbnails, custom player, place read-out under the picture.
- Tests: 28 of 28 pass (3 new place-name checks). Browser check: both modes, clicks, arrow keys, track keys, no errors.
