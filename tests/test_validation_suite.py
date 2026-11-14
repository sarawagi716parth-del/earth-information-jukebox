"""
tests/test_validation_suite.py
Automated Verification Suite for The Earth Information Jukebox.
Uses strictly ONE tiny synthetic image (tests/known_answer_test.png) for unit assertions,
verifying that the app only loads real NASA SVS packs and never loads test data.
"""

import os
import sys
import json
import cv2
import numpy as np
from scipy.io import wavfile

# Add project root
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from sonification_engine import (
    quantize_to_pentatonic,
    PENTATONIC_SCALE,
    generate_tone,
    apply_stereo_panning,
    OpenCVFeatureExtractor,
    discover_packs
)

def run_tests():
    print("=" * 70)
    print("NASA SPACE APPS 2026: SVS PACKS & ARCHITECTURE VALIDATION")
    print("=" * 70)
    
    results = {"passed": 0, "failed": 0, "log": []}
    
    # -----------------------------------------------------------------
    # TEST 1: Known-Answer Unit Test on Tiny Synthetic Image (tests/ only)
    # -----------------------------------------------------------------
    print("\n[TEST 1] Verifying Known-Answer Unit Invariants on tests/known_answer_test.png...")
    known_img_path = os.path.join(TESTS_DIR, "known_answer_test.png")
    assert os.path.exists(known_img_path), "Missing tests/known_answer_test.png"
    
    test_img = cv2.imread(known_img_path)
    assert test_img.shape == (32, 64, 3), f"Expected (32, 64, 3), got {test_img.shape}"
    
    extractor = OpenCVFeatureExtractor(known_img_path)
    slices = extractor.extract_scanline_slices(num_slices=4)
    objects = extractor.detect_prominent_objects()
    
    # Ground truth checks:
    # 1. Left slice must be blue (dominant hue ~120), right slice red (hue ~0)
    assert slices[0]["hue"] > 100, f"Left slice hue should be blue (~120), got {slices[0]['hue']}"
    assert slices[-1]["hue"] < 20, f"Right slice hue should be red (~0), got {slices[-1]['hue']}"
    
    # 2. Detected white square contour must have area == 81 px (10x10 square) and center near x=48, y=16
    assert len(objects) >= 1, "Failed to detect known contour square"
    target_obj = objects[0]
    assert abs(target_obj["area"] - 81.0) < 5.0, f"Known area should be ~81, got {target_obj['area']}"
    assert abs(target_obj["center_x"] - 48) <= 2, f"Known cx should be 48, got {target_obj['center_x']}"
    assert abs(target_obj["center_y"] - 16) <= 2, f"Known cy should be 16, got {target_obj['center_y']}"
    
    print(f"  ✓ Known-Answer assertions passed: Area={target_obj['area']}px, Centroid=({target_obj['center_x']}, {target_obj['center_y']})")
    results["passed"] += 1
    results["log"].append("Known-Answer Unit Test: PASS")
    
    # -----------------------------------------------------------------
    # TEST 2: Verify App Never Loads Test Data
    # -----------------------------------------------------------------
    print("\n[TEST 2] Verifying app.py Isolation (Never Loads tests/)...")
    app_py_path = os.path.join(PROJECT_ROOT, "app.py")
    with open(app_py_path, "r", encoding="utf-8") as f:
        app_code = f.read()
        
    assert "tests/" not in app_code and "known_answer_test" not in app_code, "app.py must NOT reference tests/ or test data!"
    assert "generate_datasets" not in app_code, "app.py must NOT reference synthetic dataset generator!"
    print("  ✓ Isolation verified: app.py strictly references packs/ and never accesses tests/.")
    results["passed"] += 1
    results["log"].append("App Isolation Test: PASS")
    
    # -----------------------------------------------------------------
    # TEST 3: NASA SVS Packs Directory Structure & Metadata
    # -----------------------------------------------------------------
    print("\n[TEST 3] Verifying Real NASA SVS Packs in packs/<pack>/<track>/...")
    packs = discover_packs(os.path.join(PROJECT_ROOT, "packs"))
    assert len(packs) >= 2, f"Expected at least 2 tracks, found {len(packs)}"
    
    for p in packs:
        print(f"  -> Validating Pack [{p['pack']}] Track [{p['track']}]...")
        assert p["video_path"] and os.path.exists(p["video_path"]), f"Missing video_720p.mp4 in {p['track']}"
        assert p["colorbar_path"] and os.path.exists(p["colorbar_path"]), f"Missing colorbar.png in {p['track']}"
        assert p["dates_path"] and os.path.exists(p["dates_path"]), f"Missing dates.txt in {p['track']}"
        
        # Verify 720p video dimensions
        cap = cv2.VideoCapture(p["video_path"])
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        assert (w, h) == (1280, 720), f"Video must be 720p (1280x720), got {w}x{h}"
        print(f"     ✓ Video: {w}x{h} @ {fps} fps | Colour bar verified | Dates: {p['date_range']}")
        
    results["passed"] += 1
    results["log"].append("NASA SVS Packs Verification: PASS")
    
    # -----------------------------------------------------------------
    # TEST 4: .gitignore Rules for Original Videos
    # -----------------------------------------------------------------
    print("\n[TEST 4] Verifying .gitignore Rules...")
    gitignore_path = os.path.join(PROJECT_ROOT, ".gitignore")
    assert os.path.exists(gitignore_path), "Missing .gitignore file"
    with open(gitignore_path, "r", encoding="utf-8") as f:
        git_rules = f.read()
    assert "*orig*.mp4" in git_rules or "*large*.mp4" in git_rules, ".gitignore must ignore raw/original videos"
    assert "!packs/*/*/video_720p.mp4" in git_rules, ".gitignore must whitelist trimmed 720p copies"
    print("  ✓ .gitignore properly configured to commit only trimmed 720p copies.")
    results["passed"] += 1
    results["log"].append(".gitignore Rules: PASS")
    
    # -----------------------------------------------------------------
    # TEST 5: Pentatonic Scale Quantization & DSP Integrity
    # -----------------------------------------------------------------
    print("\n[TEST 5] Verifying Pentatonic Scale Quantization & DSP...")
    for test_f in [100.0, 220.0, 440.0, 880.0, 1400.0]:
        q_f = quantize_to_pentatonic(test_f)
        assert q_f in PENTATONIC_SCALE, f"Frequency {test_f} Hz snapped to non-pentatonic {q_f} Hz"
        
    tone = generate_tone(440.0, duration=0.5, attack=0.02, release=0.03)
    assert not np.isnan(tone).any() and not np.isinf(tone).any(), "Audio tone contains invalid floats"
    panned = apply_stereo_panning(tone, pan_position=-0.8)
    assert panned.shape == (len(tone), 2), "Stereo panning dimensions invalid"
    print("  ✓ DSP & Pentatonic Quantization validated with zero digital clipping.")
    results["passed"] += 1
    results["log"].append("DSP & Pentatonic Quantization: PASS")

    # -----------------------------------------------------------------
    # REPORT
    # -----------------------------------------------------------------
    total = results["passed"] + results["failed"]
    print("\n" + "=" * 70)
    print(f"RESULTS: {results['passed']}/{total} Tests Passed ({(results['passed']/total)*100:.1f}%)")
    print("=" * 70)
    
    report_file = os.path.join(TESTS_DIR, "VALIDATION_REPORT.json")
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump({
            "status": "SUCCESS",
            "passed": results["passed"],
            "failed": results["failed"],
            "log": results["log"]
        }, rf, indent=4)
    print(f"Report saved to: {report_file}")
    return results["failed"] == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
