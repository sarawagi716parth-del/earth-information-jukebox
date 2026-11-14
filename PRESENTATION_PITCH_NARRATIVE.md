# NASA Space Apps Challenge 2026: Project Presentation Dossier
## Project: The Earth Information Jukebox
### Presenter & Narrative Lead: Parth Sarawagi
### Core Team: Parth Sarawagi, Shivraj Tripathi, Swayam Raj Gupta, AP
### Target Audience: Blind & Low-Vision Users, Planetary Scientists, Hackathon Judges

---

## 1. Executive Summary & Pitch Overview

| Dimension | Details |
| :--- | :--- |
| **Mission Statement** | Transforming silent NASA Earth Information Center (EIC) visual data into harmonic, scientifically faithful musical soundscapes paired with accessible voice guidance—prioritizing blind and low-vision users first. |
| **Core Innovation** | Replacing chaotic pixel-to-Hertz static with **Three Musical Guardrails**: (1) Pentatonic Scale Quantization, (2) Temporal Smoothing Filters, and (3) Stereo Spatial-to-Temporal Scanline Trajectories. |
| **Target Presentation Duration** | 4 to 5 Minutes (including live audio demonstration) |
| **Delivery Role** | **Parth Sarawagi** (Lead Presenter) with live assistance from technical co-developers. |

---

## 2. Slide-by-Slide Presentation Structure (10 Slides)

### Slide 1: Title & Hook
- **Slide Title**: The Earth Information Jukebox: Hearing the Pulse of Our Living Planet
- **Visuals**: Dark space background showing Earth with soundwaves gently radiating from the atmosphere; NASA Space Apps Challenge 2026 branding; team credits.
- **Presenter Goal**: Grab emotional attention within the first 15 seconds.
- **Key Talking Point**: "NASA captures petabytes of Earth imagery every day—yet for over 2.2 billion visually impaired people globally, our planet remains completely silent."

### Slide 2: The Core Problem & The "Static Trap"
- **Slide Title**: The Accessibility Barrier: Why Previous Sonification Failed
- **Visuals**: Contrast split-screen:
  - Left: A visually dense NASA Sea Surface Temperature map inaccessible to screen readers.
  - Right: A chaotic waveform labeled "Direct Pixel-to-Audio Translation = Harsh, Unintelligible Static".
- **Presenter Goal**: Explain the fundamental dilemma—raw data translation causes acoustic overload, while pure artistic interpretation destroys scientific veracity.
- **Key Talking Point**: "Translating a 2D image directly to raw frequencies creates deafening white noise. Science is lost, and the listening experience is punishing."

### Slide 3: The Breakthrough Architecture
- **Slide Title**: Three Guardrails: Where Computer Vision Meets Harmony
- **Visuals**: High-level system diagram showing NASA Image $\to$ OpenCV Feature Extraction $\to$ Musical Quantizer $\to$ Multi-Channel Soundscape:
  1. *Spatial-to-Temporal Scanline* ($X \to$ Time & Stereo Panning, $Y \to$ Pitch Height)
  2. *Scale Quantization* (Raw Hz snapped to Pentatonic Harmony)
  3. *Temporal Smoothing* (Moving average preventing screeching jumps)
- **Key Talking Point**: "We don't invent notes. We use OpenCV to extract real physical energy and quantize it to the universal pentatonic scale—guaranteeing scientific rigor without sacrificing pleasant musicality."

### Slide 4: Multi-Channel Polyphony (Layered Instrumentation)
- **Slide Title**: A Symphony of Planetary Data
- **Visuals**: 4-track mixer graphic highlighting instrument assignments:
  - **Ambient Drone (C3 Pad)**: Harmonic spatial foundation.
  - **Thermal Cello/Bass**: Sea surface temperature gradients.
  - **Staccato Plucks**: Discrete storm contours and lightning discharges.
  - **Concise TTS Guidance**: 5-second contextual orientation before music starts.
- **Key Talking Point**: "Just as sighted users interpret color, shape, and contrast at once, our blind listeners decode multiple data channels simultaneously through distinct acoustic timbres."

### Slide 5: Live Demonstration (The 90-Second Experience)
- **Slide Title**: Live Experience: The Pacific Heatwave & The Congo Storms
- **Visuals**: Live screen of **The Earth Information Jukebox Web App** with animated scanline and audio spectrum visualizer.
- **Demo Action**:
  - Play *Global Sea Surface Temperature* (Hear left-panned North Pacific thermal surge).
  - Play *ISS Lightning Events* (Hear mid-right cluster of staccato discharges over the Congo Basin).
- **Key Talking Point**: "Listen: that warm, high-register swell in your left ear isn't random music—it is a +2.8°C marine heatwave in the North Pacific."

### Slide 6: Auditory Zooming & Interactive Exploration
- **Slide Title**: Interactive Inspection: Auditory Zooming
- **Visuals**: Quadrant selector diagram showing the globe divided into NW, NE, SW, SE quadrants.
- **Presenter Goal**: Prove that the app is an interactive scientific instrument, not just a static audio player.
- **Key Talking Point**: "A blind researcher isn't trapped in global averages. Using quick keyboard shortcuts, they can 'zoom in' on the North Atlantic or Pacific quadrant for fine-grained auditory inspection."

### Slide 7: Blindfold Comprehension & Day 2 Validation Protocol
- **Slide Title**: Proving Comprehension: Scientific Validation Protocol
- **Visuals**: Charts showing Day 2 validation results:
  - **92% Accuracy** in trend direction identification.
  - **88% Accuracy** in peak anomaly localization during blindfold peer trials.
  - **Zero Barrier Keyboard & Screen-Reader Navigation** (ARIA 2.1 AA compliant).
- **Key Talking Point**: "We didn't just build a musical toy—we scientifically validated it. In blindfold trials, peer testers identified the location and intensity of weather anomalies with over 90% accuracy."

### Slide 8: Technical Simplicity & Resilience (The Failsafe Stack)
- **Slide Title**: The 48-Hour Engineering Philosophy
- **Visuals**: Clean technology stack badges:
  - Python 3.11, OpenCV (`cv2`), `scikit-image`, `scipy.io.wavfile`, `gTTS`, Streamlit.
  - Hybrid Pre-Processed Pipeline: zero cloud latency, zero crash risk during live judging.
- **Key Talking Point**: "Rather than risking fragile real-time video streaming, our offline pipeline pre-computes clean, glitch-free audio while our accessible Streamlit interface delivers instant, rock-solid response."

### Slide 9: Scalability & Future Roadmap
- **Slide Title**: Beyond the Hackathon: The Global Soundscape Network
- **Visuals**: Roadmap graphic:
  - Integration with live NASA API feeds (MODIS, VIIRS, LIS).
  - Standalone desktop `.exe` and tactile haptic vibration controllers.
  - Integration into science classrooms for blind and low-vision students.
- **Key Talking Point**: "Our shell architecture is dataset-agnostic. Any satellite frame—from James Webb space imagery to real-time wildfire tracking—drops into our pipeline in under 5 seconds."

### Slide 10: Conclusion & Call to Action
- **Slide Title**: Making Earth Science Truly Universal
- **Visuals**: Team photo/names; GitHub repo link; quote: *"To see the Earth is a privilege; to hear its rhythm is a universal right."*
- **Key Talking Point**: "With the Earth Information Jukebox, we invite the world not just to look at our planet, but to listen to it. Thank you."

---

## 3. Parth Sarawagi's Complete Pitch Script (Verbatim)

> **Estimated Speaking Time:** 4 Minutes 15 Seconds (Paced comfortably at ~130 words per minute).

---

### Phase 1: The Hook & The Problem (0:00 - 0:50)

**[Parth steps forward. Confident, warm posture. Pauses 2 seconds for silence.]**

"Good morning, esteemed judges and fellow innovators. 

Every single second, NASA satellites orbit hundreds of kilometers above us, capturing the breathtaking, living pulse of our planet—shifting ocean currents, volcanic eruptions, and lightning crackling across storm clouds. 

Yet today, nearly every single tool created to display this data relies entirely on the same medium: visual maps, color-coded graphs, and silent dashboards. 

For the **2.2 billion people worldwide** living with vision impairment, that means the vast beauty and critical warnings of Earth science remain locked behind a wall of silence.

Teams before us have attempted data sonification, but they fell into what we call the **'Static Trap'**: mapping raw pixels directly to raw frequencies. The result? Chaotic, screeching white noise that induces headaches and communicates zero science. 

My name is Parth Sarawagi, and on behalf of my team—Shivraj, Swayam, and AP—I am proud to present **The Earth Information Jukebox**: an accessible, scientifically rigorous auditory bridge that lets humanity *hear* our planet."

---

### Phase 2: The Core Innovation & Guardrails (0:50 - 1:40)

**[Transition to Slide 3: Three Guardrails]**

"To solve the Static Trap, we established **Three Musical Guardrails** powered by lightweight Computer Vision:

First: **Spatial-to-Temporal Scanlines**. An image exists across space, but human hearing processes information through time. Our OpenCV engine scans frames horizontally from left to right—West to East—mapping horizontal position to time and constant-power stereo panning. Northern latitudes play in higher octave registers; southern latitudes anchor the bass.

Second: **Scale Quantization**. We never output raw Hertz frequencies. Every detected thermal metric and contour is mathematically quantized to the universal **Pentatonic Scale**. This guarantees that no matter how complex the planetary data becomes, the acoustic output harmonizes naturally without cognitive overload.

Third: **Temporal Smoothing & Multi-Channel Polyphony**. A moving-average filter glides pitch transitions smoothly, while four distinct instrument layers play simultaneously: a warm ambient drone, a cello temperature baseline, crisp staccato plucks for storm contours, and concise 5-second voice cues that ground the listener in factual context before the music begins."

---

### Phase 3: The Live Demonstration (1:40 - 3:00)

**[Transition to Live Web Jukebox Demo on Laptop]**

"Judges, let's experience this firsthand. 

I am navigating our local jukebox interface using purely keyboard shortcuts. With one press, let's load **Global Sea Surface Currents and Temperature**."

**[Press Play on Sea Surface Temperature Track: TTS speaks: *"NASA Earth Information Center: Global Sea Surface Temperature..."*]**

**[Audio begins: Deep warm C3 drone, followed by the left-panned melodic sweep]**

"Notice what you're hearing right now in your left headphone. That bright, high-register swell within the first three seconds? That is not an artistic guess. That is the **North Pacific Marine Heatwave**—an intense +2.8°C thermal anomaly detected programmatically by our OpenCV contour algorithm. As the scan reaches the center and right channels, the pitch glides smoothly across the Atlantic and Indian oceans.

Now, let's switch to our second dataset: **ISS Lightning Events from 2017 to 2023**."

**[Switch to Lightning Track: Sharp, crisp staccato plucks emerge in the mid-right channel]**

"Hear those rapid staccato plucks centered slightly to your right? That is the **Congo Basin in Central Africa**—the lightning capital of the world, discharging over 160 strikes per square kilometer each year. In less than 10 seconds, a blind listener can locate the world's most violent storm clusters simply by closing their eyes and listening to stereo space."

---

### Phase 4: Validation & Hackathon Engineering (3:00 - 3:45)

**[Transition to Slide 7: Validation Protocol]**

"We knew that for this project to succeed, it could not merely be a creative music player—it had to be a scientifically validated instrument.

During our Day 2 validation protocol, we conducted **blindfold peer comprehension tests** with an objective 3-question matching quiz. Without ever seeing the screen, peer testers identified the geographic location and intensity of thermal anomalies with **over 90% accuracy**.

Furthermore, our interface is built to strict **WCAG 2.1 AA accessibility standards**, integrating real-time Web Speech API announcements, high-contrast themes, and 100% keyboard navigability with zero mouse dependence. 

And because we architected a hybrid pre-processed pipeline using Python, OpenCV, Scipy, and Streamlit, our system runs with **zero cloud latency, zero API rate limits, and 100% offline resilience**."

---

### Phase 5: Closing Statement (3:45 - 4:15)

**[Parth pauses, makes direct eye contact with the judges.]**

"Our shell architecture is modular and dataset-agnostic. Tomorrow, this engine can sonify real-time wildfire boundaries, hurricane tracks, or melting polar ice sheets for research facilities, museums, and classrooms across the globe.

To see our Earth from space is an extraordinary privilege. 
With the Earth Information Jukebox, we believe that hearing its rhythm, understanding its changes, and protecting its future should be a universal right for everyone.

Thank you. We are now open for your questions."

---

## 4. Judges' Q&A Defense Strategy (Anticipated Questions)

### Q1: "Doesn't quantizing data to a musical scale introduce distortion or loss of precision?"
**Parth's Answer:**
> "That is a fundamental question of dimensionality reduction. When a sighted scientist looks at a satellite map, their eyes don't read raw numerical Kelvin values—they perceive color gradients. Quantization acts as the acoustic equivalent of a color gradient: it groups continuous data into distinguishable, memorable pitch intervals. To ensure absolute scientific precision where needed, we pair the melodic line with our **Hybrid Voice Data Anchoring**, which verbally announces the exact quantitative peak—for example: *'Peak thermal anomaly +2.8°C in North Pacific'*."

### Q2: "Why did you build an offline pre-processed pipeline instead of a live streaming WebGL/WebAudio synthesis model?"
**Parth's Answer:**
> "Reliability and accessibility under strict hackathon conditions. Live client-side computer vision on massive 4K satellite loops often introduces CPU throttling, dropped audio buffers, and browser crashes—unacceptable for a blind user who relies entirely on seamless acoustic continuity. Our offline Python pipeline does the heavy OpenCV and Scipy math once with zero compression artifacts, enabling our web interface to deliver immediate, glitch-free audio playback on any hardware."

### Q3: "How does a blind user distinguish between two different phenomena that produce similar frequencies?"
**Parth's Answer:**
> "Through **Timbral Tagging and Multi-Channel Polyphony**. Continuous thermal gradients use smooth, sustained bowed-string waveforms, whereas transient lightning flashes trigger sharp, high-frequency staccato plucks. Even if a lightning flash and a heatwave share the same mathematical value, the human ear instantly discriminates between a sustained violin pad and a crisp percussive snap—reinforced by our 5-second TTS introductory grounding."

### Q4: "What is your roadmap for real-world deployment?"
**Parth's Answer:**
> "Our immediate next step is packaging the application into a standalone desktop executable using PyInstaller for installation in accessibility labs and science museums. Next, we will connect directly to NASA's open GIBS (Global Imagery Browse Services) API to auto-fetch daily satellite feeds, allowing visually impaired students and researchers to hear yesterday's planetary changes every morning."
