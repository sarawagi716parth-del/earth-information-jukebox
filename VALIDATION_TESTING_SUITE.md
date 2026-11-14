# Day 2 Validation & Testing Suite
## The Earth Information Jukebox — NASA Space Apps Challenge 2026

---

## 1. Overview & Objective

To prove that **The Earth Information Jukebox** is an authentic scientific accessibility tool rather than merely an artistic synthesizer, the team must execute a structured, quantifiable validation protocol on Day 2 of the hackathon.

This suite provides:
1. **Blindfold Peer Evaluation Protocol** (Subjective & qualitative usability testing).
2. **Standardized 3-Question Audio Comprehension Quiz** (Objective quantitative accuracy measurement).
3. **WCAG 2.1 AA Screen-Reader & Keyboard Accessibility Checklist**.
4. **Automated Audio DSP & Signal Integrity Test Suite** (`test_validation_suite.py`).

---

## 2. Blindfold Peer Evaluation Protocol

### Target Testers
- Minimum 3 peer teammates/students not directly involved in coding the specific OpenCV-to-frequency mapping script.
- Testing environment: Quiet room, high-quality over-ear stereo headphones.

### Testing Procedure
1. **Physical Blindfold**: The participant is blindfolded prior to sitting down at the terminal.
2. **Contextual Grounding**: The tester hears only the 5-second TTS introduction (e.g., *"NASA Earth Information Center: Global Sea Surface Temperature"*).
3. **Playback Sweep**: The 12-second sonified track is played twice in full.
4. **Verbal Query**: The evaluator asks the tester to state:
   - **Direction of Travel**: Did the scan move Left-to-Right or Right-to-Left?
   - **Peak Anomaly Location**: Where was the highest energy/temperature point (Ear/Time)?
   - **Phenomenon Texture**: Was the feature smooth/continuous or violent/sporadic?

### Scoring Rubric (5-Point Usability Scale)

| Metric | 1 (Fails) | 3 (Moderate) | 5 (Exemplary) |
| :--- | :--- | :--- | :--- |
| **Spatial Awareness** | Cannot determine left from right channel | Identifies left vs right after multiple repeats | Instantly identifies spatial panning within 2 seconds |
| **Trend Direction** | Cannot detect pitch rise or fall | Detects general rise but misses subtle peaks | Accurately identifies thermal peak onset and duration |
| **Texture Recognition** | Cannot distinguish smooth pad from pluck | Distinguishes pluck from pad with guidance | Instantly identifies lightning discharge vs sea surface |
| **Cognitive Comfort** | Finds audio irritating or painful (Static Trap) | Audio is tolerable but fatiguing | Audio is harmonic, pleasant, and engaging |

---

## 3. Standardized 3-Question Comprehension Quiz

Administered via the web application's **"Day 2 Validation & Testing Suite"** tab to collect quantifiable percentages for Slide 7 of the presentation deck.

### Question 1: Thermal Anomaly Localization (Dataset 1: Sea Surface Temp)
- **Audio Clip**: `sea_temp_sonified.wav` (12 seconds)
- **Prompt**: *"Listen to the Sea Surface Temperature track. Where does the primary thermal surge peak occur?"*
- **Options**:
  - [x] **A. First 3 seconds, panned Left (North Pacific Basin)** *(Correct)*
  - [ ] B. Middle 6 seconds, centered (Atlantic Basin)
  - [ ] C. Last 3 seconds, panned Right (Indian Ocean)
  - [ ] D. No peak detected
- **Scientific Rationale**: The North Pacific Marine Heatwave anomaly is located at the far west of the Pacific basin ($X \approx 15\%$), placing its onset at 1.8 to 2.8 seconds panned heavily to the left stereo channel.

### Question 2: Phenomenon Density & Clustering (Dataset 2: ISS Lightning)
- **Audio Clip**: `lightning_sonified.wav` (12 seconds)
- **Prompt**: *"Listen to the ISS Lightning track. Where is the highest frequency of sharp staccato discharge plucks?"*
- **Options**:
  - [ ] A. Uniformly distributed with no distinct clusters
  - [x] **B. Mid-to-late region, slightly right of center (Congo Basin, Africa)** *(Correct)*
  - [ ] C. Extremely early, panned full left
  - [ ] D. Only at the very end of the track
- **Scientific Rationale**: The Congo Basin lightning hotspot is located near $X \approx 58\%$, producing an intense cluster of staccato plucks centered slightly to the right of the acoustic stage.

### Question 3: Parameter Mapping Knowledge
- **Prompt**: *"Across all sonified tracks, what does vertical coordinate (latitude) map to in the acoustic soundscape?"*
- **Options**:
  - [x] **A. Musical Pitch & Octave Height (Northern latitudes play higher, Southern lower)** *(Correct)*
  - [ ] B. Playback Speed and Tempo
  - [ ] C. White Noise Volume
  - [ ] D. Stereo Left-Right Panning
- **Scientific Rationale**: Vertical coordinates strictly govern pitch height/octaves, allowing blind users to construct an intuitive 2D grid ($X = \text{Time/Pan}, Y = \text{Pitch}$).

---

## 4. Screen-Reader & Keyboard Accessibility Audit Checklist

| Requirement | Standard | Implementation in Web App | Status |
| :--- | :--- | :--- | :--- |
| **No Mouse Requirement** | WCAG 2.1.1 (Level A) | All actions mapped to keys `[1]`, `[2]`, `[3]`, `[Q]`, `[H]` | Passed |
| **Live Announcements** | WCAG 4.1.3 (Level AA) | Web Speech API announces state changes verbally | Passed |
| **High Contrast UI** | WCAG 1.4.3 (Level AA) | Contrast ratio $\ge 7:1$ (Dark space theme `#0d1117`, text `#ffffff`) | Passed |
| **ARIA Semantic Regions** | WCAG 1.3.1 (Level A) | `role="region"`, `aria-label`, `aria-live="polite"` applied | Passed |
| **Audio Control Pause** | WCAG 1.4.2 (Level A) | Audio streams provide pause/stop and volume sliders | Passed |

---

## 5. Automated Signal Integrity & DSP Test Suite

Run the automated verification script:
```powershell
python "C:\Users\Parth\Downloads\The Earth Information Jukebox\test_validation_suite.py"
```
The test suite verifies:
1. All NASA input images load without corrupt headers.
2. OpenCV contour detection generates valid positive polygon vertices.
3. Pentatonic quantization accurately locks frequencies within 0.1 Hz of valid musical notes.
4. Exported `.wav` files have exact 44.1kHz stereo headers and no clipping exceeding $\pm 1.0$.
5. Voice intros exist and have non-zero file size.
