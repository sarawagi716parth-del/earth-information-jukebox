# Demo video tools

These scripts made `CodeHub_Earth_Information_Jukebox_demo.mp4` (29 seconds, 1920x1080, 30 fps). They film the real
app and use its real sound.

1. Start the app: `python app.py`
2. `python tools/demo_video/capture.py` films the page frame by frame in headless Chrome (Playwright). It plays the
   ocean sweep, clicks three spots, plays part of the aerosol sweep, then uses Accessible mode with the keys A, 3 and the
   arrows. It writes the frames to `scenes/` and every sound event to `events.json`.
3. `python tools/demo_video/make_video.py` builds the soundtrack from the tracks' own `sonified.wav` files plus the explore
   tones. It encodes each scene with ffmpeg, joins the scenes and adds the sound.

The paths at the top of the scripts point to the build machine. Change them before running on another computer.
The video has no voice: in the real app the place names are spoken aloud, and in the video they appear on screen.
