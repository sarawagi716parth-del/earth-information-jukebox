# Development log: how the Earth Information Jukebox was built

Team CodeHub, NASA Space Apps Challenge 2026 (14 and 15 November 2026). This is the real timeline of what we
built, what went wrong and what we changed. The git history starts with the first build on 14 November; the
later commits were made on 15 November, grouped by part of the project.

## Before the hackathon: research only
- Read the challenge and the judging criteria, and reviewed every NASA resource pack for how musical and how
  readable it would be (lightning, ocean currents, aerosols, air quality, forest height and others).
- Teammates wrote research notes and a technical research report on how blind and low-vision people can
  understand pictures through sound. Key lessons we kept: give every sound one clear meaning, keep at most about
  three sounds at once, use a pentatonic scale so it never sounds harsh, and let users explore by keyboard.

## 14 November: first build, then an audit
- The first version was built quickly with an AI coding assistant: a Streamlit app with video packs. This is
  the first commit in the history.
- When we checked it against the NASA pages, we found serious problems:
  - the "lightning" pack was a satellite animation, not the NASA lightning video;
  - the colour bars and date lists were generated, not NASA's;
  - some text and quiz answers contained made-up science;
  - the engine only turned brightness into pitch over a constant drone, so the sound did not describe the data;
  - the videos used a codec Chrome cannot play.
- Decision: use only real NASA files, and nothing made up anywhere in the app.
- Rebuilt the engine (version 2) so that it reads NASA's own colour bar and turns colours back into
  temperatures before making any sound. On the real ocean clip, pitch followed temperature exactly and no notes
  played over land.
- Lightning proof of concept: the first try made 210 notes in 20 seconds and the melody got stuck on about five
  notes. Raising the thresholds for "busy" storms fixed both (154 notes).

## 15 November, morning: images only
- We tested the engine with two sea temperature pictures. It could not read still images, and it could not
  read pictures that have no colour bar inside them.
- Decision: the jukebox takes images only, not videos. Videos were large (NASA's 8K files are hundreds of
  megabytes) and slow to analyse.
- Downloaded official still images and colour bar files from NASA's Scientific Visualization Studio: ocean
  temperature (SVS 3912), aerosols on 19 August 2025 (SVS 5669) and lightning (SVS 5011).
- Tried NASA's GEDI forest height globe (SVS 4950) and dropped it: its 3D shading changes the colours too much
  to read the scale reliably.
- Built automatic colour-scale learning for uploaded pictures. The first version linked colours in the wrong
  order (coastline and land colours joined the cold end to the warm end), and it agreed with a hand-made scale
  only about half the time. Linking only colours that touch each other on the map fixed it: 0.998 rank agreement.
- Rebuilt the web page in Flask: the image and its description on the left, the sound and its description on the
  right. The description of the sound is generated from the actual notes, so it always matches what plays.
- Checked the science: from the ocean image the engine reads 28.4 °C at the equator and 2.5 °C near 60° south,
  the same pattern real oceans show.

## 15 November, afternoon and evening
- Added Accessible mode for blind and low-vision users: everything is spoken and works from the keyboard, with
  larger text and high contrast.
- Added place names: wherever you click or move, the page says the state, province, ocean or sea, using Natural
  Earth (public domain) data, for example "Maharashtra, India" or "Arabian Sea, 29.4 °C".
- New page design, the 7-slide presentation and the 29-second demo video.
- Automated checks: 28 of 28 pass.

## How we used AI
AI assistants wrote most of the code, the slides and the documents: Claude (Anthropic) for most of the project,
and an AI coding assistant for the first build on 14 November. The team researched the challenge, chose the NASA
data and the design, set the requirements (for example images only, two modes and place names), reviewed the
results and made the decisions. All data in the app comes from NASA and Natural Earth.

## Still to do
- A listening test with blind and low-vision users.
- A test with a real screen reader such as NVDA.
- More NASA image packs and a phone-friendly version.
