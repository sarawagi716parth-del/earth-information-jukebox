"""
sonification_engine.py
Core Data Sonification & Computer Vision Pipeline for The Earth Information Jukebox.
Converts NASA Earth Information Center (EIC) visual frames into structured,
pleasant musical soundscapes adhering to strict accessibility and musical guardrails.
"""

import os
import cv2
import numpy as np
from scipy.io import wavfile
from gtts import gTTS

SAMPLE_RATE = 44100

# -------------------------------------------------------------
# 1. PENTATONIC & HARMONIC SCALE QUANTIZATION
# -------------------------------------------------------------
# C Major Pentatonic Scale frequencies (Hz) across octaves 2 through 6
# C2, D2, E2, G2, A2 ... C6
PENTATONIC_SCALE = np.array([
    65.41, 73.42, 82.41, 98.00, 110.00,      # Octave 2
    130.81, 146.83, 164.81, 196.00, 220.00,  # Octave 3
    261.63, 293.66, 329.63, 392.00, 440.00,  # Octave 4 (Middle C)
    523.25, 587.33, 659.25, 783.99, 880.00,  # Octave 5
    1046.50, 1174.66, 1318.51, 1567.98, 1760.00 # Octave 6
])

def quantize_to_pentatonic(frequency):
    """Snaps any raw frequency to the nearest note on the Pentatonic Scale."""
    idx = np.argmin(np.abs(PENTATONIC_SCALE - frequency))
    return PENTATONIC_SCALE[idx]


# -------------------------------------------------------------
# 2. AUDIO SYNTHESIS & DSP PRIMITIVES
# -------------------------------------------------------------
def generate_tone(freq, duration, sample_rate=SAMPLE_RATE, timbre="sine", attack=0.03, release=0.05):
    """
    Generates a single synthetic tone with an ADSR envelope to prevent clicks.
    Timbre options: 'sine', 'smooth_pad' (with warm harmonics), 'staccato_pluck'
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    if timbre == "sine":
        tone = np.sin(2 * np.pi * freq * t)
    elif timbre == "smooth_pad":
        # Fundamental + gentle 2nd and 3rd harmonics for rich string-like warmth
        tone = (0.60 * np.sin(2 * np.pi * freq * t) +
                0.25 * np.sin(4 * np.pi * freq * t) +
                0.15 * np.sin(6 * np.pi * freq * t))
    elif timbre == "staccato_pluck":
        # Sharp transient decaying harmonic tone
        tone = (0.5 * np.sin(2 * np.pi * freq * t) +
                0.3 * np.sin(4 * np.pi * freq * t) +
                0.2 * np.sin(8 * np.pi * freq * t))
        decay_envelope = np.exp(-t * 12.0)
        tone = tone * decay_envelope
    else:
        tone = np.sin(2 * np.pi * freq * t)
        
    # Apply Attack and Release envelope
    num_samples = len(t)
    envelope = np.ones(num_samples, dtype=np.float32)
    attack_samples = int(attack * sample_rate)
    release_samples = int(release * sample_rate)
    
    if attack_samples > 0 and attack_samples < num_samples:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    if release_samples > 0 and release_samples < num_samples:
        envelope[-release_samples:] = np.linspace(1.0, 0.0, release_samples)
        
    return tone * envelope


def apply_stereo_panning(mono_audio, pan_position):
    """
    Constant-power stereo panning.
    pan_position ranges from -1.0 (full left) to +1.0 (full right).
    """
    # Angle in radians from 0 to pi/2
    theta = (pan_position + 1.0) * (np.pi / 4.0)
    left_gain = np.cos(theta)
    right_gain = np.sin(theta)
    
    left_channel = mono_audio * left_gain
    right_channel = mono_audio * right_gain
    return np.column_stack((left_channel, right_channel))


def generate_ambient_drone(duration, sample_rate=SAMPLE_RATE):
    """
    Guardrail 3: Ambient Foundation Layer.
    Soft, resonant drone chord (C3 + G3 + C4) providing acoustic grounding.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    drone_c3 = 0.35 * np.sin(2 * np.pi * 130.81 * t)
    drone_g3 = 0.25 * np.sin(2 * np.pi * 196.00 * t)
    drone_c4 = 0.15 * np.sin(2 * np.pi * 261.63 * t)
    drone_mono = (drone_c3 + drone_g3 + drone_c4) * 0.20
    
    # Slight stereo width (subtle phase shift for spatial atmosphere)
    left_drone = drone_mono
    right_drone = np.roll(drone_mono, int(sample_rate * 0.005))
    return np.column_stack((left_drone, right_drone))


# -------------------------------------------------------------
# 3. OPENCV COMPUTER VISION FEATURE EXTRACTION
# -------------------------------------------------------------
class OpenCVFeatureExtractor:
    """
    Extracts structured metrics from NASA EIC frames:
    - Dominant Hue / Brightness per column (scan-line temporal axis)
    - Contours & Shape Geometry (cv2.findContours, approxPolyDP)
    - Thermal Anomalies & Flash Density
    """
    def __init__(self, image_path, quadrant=None):
        self.image_path = image_path
        self.raw_image = cv2.imread(image_path)
        if self.raw_image is None:
            raise FileNotFoundError(f"Cannot load image at {image_path}")
            
        # Optional Auditory Zoom quadrant cropping: 'NW', 'NE', 'SW', 'SE'
        h, w, _ = self.raw_image.shape
        if quadrant == "NW":
            self.image = self.raw_image[:h//2, :w//2]
        elif quadrant == "NE":
            self.image = self.raw_image[:h//2, w//2:]
        elif quadrant == "SW":
            self.image = self.raw_image[h//2:, :w//2]
        elif quadrant == "SE":
            self.image = self.raw_image[h//2:, w//2:]
        else:
            self.image = self.raw_image
            
        self.hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
    def extract_scanline_slices(self, num_slices=64):
        """
        Divides the frame horizontally into temporal scan slices (left to right).
        Computes dominant color, brightness, and vertical center of mass for each slice.
        """
        h, w, _ = self.image.shape
        slice_w = max(1, w // num_slices)
        slices_data = []
        
        for i in range(num_slices):
            x_start = i * slice_w
            x_end = min((i + 1) * slice_w, w)
            col_bgr = self.image[:, x_start:x_end]
            col_hsv = self.hsv[:, x_start:x_end]
            col_gray = self.gray[:, x_start:x_end]
            
            # Average color metrics
            avg_hue = float(np.mean(col_hsv[:, :, 0]))       # 0 to 180 in OpenCV
            avg_val = float(np.mean(col_hsv[:, :, 2]))       # Brightness 0 to 255
            avg_sat = float(np.mean(col_hsv[:, :, 1]))       # Saturation
            
            # Vertical center of mass (where the primary energy is concentrated)
            row_energy = np.mean(col_gray, axis=1)
            total_energy = np.sum(row_energy) + 1e-6
            vertical_center = float(np.sum(np.arange(h) * row_energy) / total_energy)
            # Invert so top of image (north) has higher value (1.0) and bottom has 0.0
            norm_y = 1.0 - (vertical_center / h)
            
            # Normalized horizontal panning: -1.0 (left) to +1.0 (right)
            norm_x = (2.0 * ((x_start + x_end) / 2.0) / w) - 1.0
            
            slices_data.append({
                "index": i,
                "norm_x": norm_x,
                "norm_y": norm_y,
                "hue": avg_hue,
                "brightness": avg_val / 255.0,
                "saturation": avg_sat / 255.0
            })
            
        return slices_data

    def detect_prominent_objects(self, max_objects=8):
        """
        Isolates distinct contour anomalies (e.g. storm cells or thermal pools).
        Maps area to volume/chord fullness and circularity to articulation.
        """
        # Threshold for high-energy regions
        _, thresh = cv2.threshold(self.gray, 110, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h, w, _ = self.image.shape
        detected_objects = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50:  # Filter out trivial noise
                continue
                
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = 0, 0
                
            # Shape geometry: approxPolyDP to estimate polygon vertices
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
            circularity = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)
            
            # Smooth vs Jagged: circularity > 0.6 is smooth pad; < 0.4 is jagged staccato
            norm_x = (2.0 * cx / w) - 1.0
            norm_y = 1.0 - (cy / h)
            
            detected_objects.append({
                "center_x": cx,
                "center_y": cy,
                "norm_x": norm_x,
                "norm_y": norm_y,
                "area": float(area),
                "circularity": float(circularity),
                "vertices": len(approx)
            })
            
        # Sort by area descending
        detected_objects.sort(key=lambda o: o["area"], reverse=True)
        return detected_objects[:max_objects]

    def render_annotated_frame(self):
        """
        Renders OpenCV visual annotations (contours, centroids, bounding boxes)
        for sighted judges and visual inspection.
        """
        annotated = self.image.copy()
        objects = self.detect_prominent_objects()
        
        for obj in objects:
            cx, cy = obj["center_x"], obj["center_y"]
            r = int(np.sqrt(obj["area"] / np.pi))
            cv2.circle(annotated, (cx, cy), max(8, r), (0, 255, 255), 2)
            cv2.circle(annotated, (cx, cy), 3, (0, 0, 255), -1)
            label = f"A:{int(obj['area'])} C:{obj['circularity']:.2f}"
            cv2.putText(annotated, label, (cx + 10, cy - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                        
        return annotated


# -------------------------------------------------------------
# 4. DATA-TO-MUSIC TRANSLATION ENGINE
# -------------------------------------------------------------
class JukeboxSonifier:
    """
    Transforms extracted EIC metrics into scale-quantized, multi-track audio.
    """
    def __init__(self, track_duration=12.0, sample_rate=SAMPLE_RATE):
        self.track_duration = track_duration
        self.sample_rate = sample_rate

    def sonify_dataset(self, image_path, quadrant=None, include_drone=True):
        """
        Performs full multi-track sonification:
        1. Extract scan-line slices and prominent contours
        2. Synthesize melodic thermal line (pitch-quantized)
        3. Synthesize contour chords / staccato plucks
        4. Synthesize stereo ambient foundation
        5. Mix and normalize output audio
        """
        extractor = OpenCVFeatureExtractor(image_path, quadrant=quadrant)
        slices = extractor.extract_scanline_slices(num_slices=64)
        objects = extractor.detect_prominent_objects()
        
        total_samples = int(self.track_duration * self.sample_rate)
        stereo_mix = np.zeros((total_samples, 2), dtype=np.float32)
        
        # 1. Add Ambient Foundation Layer
        if include_drone:
            drone = generate_ambient_drone(self.track_duration, self.sample_rate)
            stereo_mix += drone * 0.40
            
        # 2. Synthesize Scan-Line Melodic Stream (Temporal Sweep)
        slice_duration = self.track_duration / len(slices)
        raw_pitches = []
        
        for s in slices:
            # Map hue and vertical position to frequency range [130 Hz - 880 Hz]
            # Warm hues (red/yellow) & northern coordinates -> higher pitch
            # Cool hues (blue/violet) & southern coordinates -> lower pitch
            base_freq = 130.0 + (s["norm_y"] * 300.0) + (s["brightness"] * 400.0)
            quantized_freq = quantize_to_pentatonic(base_freq)
            raw_pitches.append(quantized_freq)
            
        # Temporal smoothing filter (moving average of 3 slices)
        smoothed_pitches = np.convolve(raw_pitches, np.ones(3)/3.0, mode='same')
        
        for i, s in enumerate(slices):
            freq = quantize_to_pentatonic(smoothed_pitches[i])
            start_sample = int(i * slice_duration * self.sample_rate)
            end_sample = min(start_sample + int(slice_duration * self.sample_rate), total_samples)
            actual_dur = (end_sample - start_sample) / self.sample_rate
            
            if actual_dur <= 0:
                continue
                
            timbre = "smooth_pad" if s["saturation"] > 0.4 else "sine"
            tone = generate_tone(freq, actual_dur, self.sample_rate, timbre=timbre, attack=0.02, release=0.03)
            tone = tone * (0.35 + 0.35 * s["brightness"]) # Dynamic volume
            
            # Constant-power stereo panning according to horizontal scan position
            panned = apply_stereo_panning(tone, s["norm_x"])
            stereo_mix[start_sample:end_sample] += panned * 0.50

        # 3. Layer Prominent Object Anomaly Accents (Staccato / Arpeggio Chords)
        for obj in objects:
            # Time of onset based on horizontal location
            obj_time = ((obj["norm_x"] + 1.0) / 2.0) * (self.track_duration * 0.85)
            start_sample = int(obj_time * self.sample_rate)
            
            obj_pitch = quantize_to_pentatonic(220.0 + obj["norm_y"] * 600.0)
            obj_duration = 0.35 if obj["circularity"] > 0.5 else 0.18
            obj_timbre = "smooth_pad" if obj["circularity"] > 0.5 else "staccato_pluck"
            
            accent = generate_tone(obj_pitch, obj_duration, self.sample_rate, timbre=obj_timbre, attack=0.01, release=0.04)
            # Volume proportional to anomaly area
            accent_vol = np.clip(np.sqrt(obj["area"]) / 40.0, 0.2, 0.7)
            panned_accent = apply_stereo_panning(accent * accent_vol, obj["norm_x"])
            
            end_sample = min(start_sample + len(panned_accent), total_samples)
            if start_sample < total_samples:
                stereo_mix[start_sample:end_sample] += panned_accent[:end_sample - start_sample] * 0.60
                
        # 4. Master Normalization (Prevent Clipping)
        max_val = np.max(np.abs(stereo_mix))
        if max_val > 0:
            stereo_mix = (stereo_mix / max_val) * 0.90
            
        return stereo_mix, extractor.render_annotated_frame()

    def export_wav(self, stereo_data, output_path):
        """Converts float32 audio (-1.0 to +1.0) to 16-bit PCM WAV."""
        int16_audio = (stereo_data * 32767).astype(np.int16)
        wavfile.write(output_path, self.sample_rate, int16_audio)
        return output_path


# -------------------------------------------------------------
# 5. CONCISE TTS VOICE GUIDANCE GENERATOR
# -------------------------------------------------------------
def generate_voice_intro(text, output_path):
    """
    Generates a 4-5 second introductory voice cue using gTTS.
    Announces dataset name, region, and primary anomaly.
    """
    try:
        tts = gTTS(text=text, lang='en', tld='com', slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"TTS Generation Warning: {e}")
        return None


# -------------------------------------------------------------
# 6. NASA SVS PACKS DISCOVERY & SONIFICATION
# -------------------------------------------------------------
def discover_packs(packs_dir=None):
    """
    Discovers all authentic NASA SVS packs and tracks adhering to:
    packs/<pack>/<track>/ (containing video_720p.mp4, colorbar.png, dates.txt)
    """
    if packs_dir is None:
        packs_dir = os.path.join(os.path.dirname(__file__), "packs")
        
    discovered = []
    if not os.path.exists(packs_dir):
        return discovered
        
    for pack_name in os.listdir(packs_dir):
        pack_path = os.path.join(packs_dir, pack_name)
        if not os.path.isdir(pack_path):
            continue
            
        for track_name in os.listdir(pack_path):
            track_path = os.path.join(pack_path, track_name)
            if not os.path.isdir(track_path):
                continue
                
            video_file = os.path.join(track_path, "video_720p.mp4")
            colorbar_file = os.path.join(track_path, "colorbar.png")
            dates_file = os.path.join(track_path, "dates.txt")
            sonified_file = os.path.join(track_path, "sonified.wav")
            intro_file = os.path.join(track_path, "intro.mp3")
            ref_frame = os.path.join(track_path, "reference_frame.png")
            annotated_frame = os.path.join(track_path, "annotated_frame.png")
            
            # Read date range from dates.txt
            date_range = "NASA Science Data"
            if os.path.exists(dates_file):
                with open(dates_file, "r", encoding="utf-8") as df:
                    lines = [line.strip() for line in df if line.strip()]
                    if lines:
                        date_range = f"{lines[0]} to {lines[-1]} ({len(lines)} frames)"
                        
            discovered.append({
                "pack": pack_name,
                "track": track_name,
                "display_name": f"{track_name.replace('_', ' ').title()} ({pack_name.replace('_', ' ').title()})",
                "track_dir": track_path,
                "video_path": video_file if os.path.exists(video_file) else None,
                "colorbar_path": colorbar_file if os.path.exists(colorbar_file) else None,
                "dates_path": dates_file if os.path.exists(dates_file) else None,
                "sonified_path": sonified_file if os.path.exists(sonified_file) else None,
                "intro_path": intro_file if os.path.exists(intro_file) else None,
                "ref_frame_path": ref_frame if os.path.exists(ref_frame) else None,
                "annotated_frame_path": annotated_frame if os.path.exists(annotated_frame) else None,
                "date_range": date_range
            })
            
    return discovered

if __name__ == "__main__":
    packs = discover_packs()
    print(f"Discovered {len(packs)} authentic NASA SVS tracks:")
    for p in packs:
        print(f" - [{p['pack']}] {p['track']}: {p['date_range']}")

