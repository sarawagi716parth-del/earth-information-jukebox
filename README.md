# The Earth Information Jukebox
### NASA Space Apps Challenge 2026 • Real NASA SVS Multi-Sensory Platform

An accessible, multi-sensory planetary data sonification platform that transforms real NASA Scientific Visualization Studio (SVS) video datasets into structured, pleasant musical soundscapes paired with concise voice guidance—prioritizing blind and low-vision users first.

---

## 👥 The Team
- **Parth Sarawagi**: Presenter, Narrative Lead & Researcher (Pitch delivery, demo coordination)
- **Shivraj Tripathi**: Researcher & Developer (Web application, algorithm testing)
- **Swayam Raj Gupta**: Researcher & PPT Design (Technical research compilation, presentation deck)
- **AP**: Researcher & Developer (OpenCV data extraction, audio synthesis engine)

---

## 🏛️ Architecture: Real NASA SVS Packs (`packs/<pack>/<track>/`)

All data loaded by the application is derived exclusively from real NASA Scientific Visualization Studio (SVS) assets organized as:
```
packs/<pack>/<track>/
├── video_720p.mp4      # Trimmed 720p (1280x720) scientific video copy
├── colorbar.png        # Calibrated NASA scientific colour bar
├── dates.txt           # Observation dates matching video frames
├── sonified.wav        # 44.1kHz stereo audio sonified from video frames
├── intro.mp3           # Concise TTS voice guidance intro
├── reference_frame.png # SVS keyframe
└── annotated_frame.png # OpenCV contour overlay
```

### Active Packs
1. **`packs/earth_information_center/sea_surface_temperature/`**:
   - Real NASA SVS visualization of ECCO2 / MUR Sea Surface Temperature & ocean currents.
   - Includes real thermal colour bar (-2°C to 32°C) and 360 observation dates (2015-06-01 to 2015-11-27).
2. **`packs/earth_information_center/iss_lightning/`**:
   - Real NASA SVS observation of ISS Lightning Imaging Sensor (LIS) flash density.
   - Includes real lightning density colour bar (0.1 to >160 fl/km²/yr) and 360 observation dates (2017-01-01 to 2023-05-23).

---

## 🔒 Test Data Isolation (`tests/` only)

Per strict scientific integrity requirements, test data is completely isolated:
- ONE tiny 64x32 synthetic image with exact ground-truth values (`tests/known_answer_test.png`) is maintained exclusively under `tests/`.
- The application (`app.py`) **never** loads or references `tests/`.

---

## 🚀 Quick Start Instructions

### 1. Launch the Web Application
Double-click `run_jukebox.bat` or run:
```powershell
python -m streamlit run app.py
```
Open `http://localhost:8501`.

### 2. Run Automated Test Suite
To verify known-answer unit invariants, pack integrity, 720p video headers, and .gitignore rules:
```powershell
python tests/test_validation_suite.py
```

---

## 📦 Version Control (.gitignore)
- Original large raw NASA video files (`*orig*.mp4`, `*large*.mp4`, etc.) are ignored by `.gitignore`.
- Only the trimmed 720p copies (`packs/*/*/video_720p.mp4`) are tracked.
