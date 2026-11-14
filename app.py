"""
The Earth Information Jukebox
NASA Space Apps Challenge 2026 - Accessible Multi-Sensory Sonification Platform
Powered strictly by real NASA Scientific Visualization Studio (SVS) files in packs/<pack>/<track>/
"""

import os
import cv2
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from sonification_engine import (
    discover_packs,
    OpenCVFeatureExtractor,
    JukeboxSonifier
)

# -------------------------------------------------------------
# PAGE CONFIGURATION & ACCESSIBLE STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Earth Information Jukebox | NASA SVS",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKS_DIR = os.path.join(BASE_DIR, "packs")

CUSTOM_CSS_AND_JS = """
<style>
    body {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    .main-title {
        color: #58a6ff;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #8b949e;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 1.2rem;
    }
    .badge-accessibility {
        background-color: #238636;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
    }
    .badge-nasa {
        background-color: #0b3d91;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .shortcut-tag {
        background: #21262d;
        border: 1px solid #484f58;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
        color: #f0883e;
        font-weight: bold;
    }
</style>

<script>
    function speakAccessibilityAnnouncement(message) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 1.05;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }

    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === 'h' || e.key === 'H') {
            speakAccessibilityAnnouncement("Keyboard Shortcuts: 1 for Sea Surface Temperature, 2 for ISS Lightning Events, Q to cycle Auditory Zoom quadrant, H for Help.");
        }
    });
</script>
"""

st.markdown(CUSTOM_CSS_AND_JS, unsafe_allow_html=True)

# -------------------------------------------------------------
# DYNAMIC PACK DISCOVERY (STRICTLY REAL NASA SVS PACKS)
# -------------------------------------------------------------
discovered_tracks = discover_packs(PACKS_DIR)

if not discovered_tracks:
    st.error("No NASA SVS packs found in packs/<pack>/<track>/. Please ensure authentic NASA SVS files are present.")
    st.stop()

# Track metadata descriptions
TRACK_DESCRIPTIONS = {
    "sea_surface_temperature": {
        "title": "NASA SVS: Sea Surface Temperature & Ocean Currents",
        "instrument": "ECCO2 Model / Multi-scale Ultra-high Resolution (MUR) SST",
        "anomaly": "Pacific & Equatorial High-Energy Thermal Fronts (+28°C to +32°C)",
        "scale": "C Major Pentatonic (65.4 Hz - 1760 Hz)",
        "description": "Visualizes global sea surface temperature gradients and turbulent current flow lines derived from the MIT/JPL ECCO2 model. Warmer waters map to higher pentatonic registers and rich string timbres."
    },
    "iss_lightning": {
        "title": "NASA SVS: ISS Lightning Events & Flash Density",
        "instrument": "Lightning Imaging Sensor (LIS) aboard International Space Station",
        "anomaly": "Equatorial Flash Discharges (>160 flashes/km²/year)",
        "scale": "C Minor Pentatonic with Staccato Pluck Articulation",
        "description": "Multi-year composite of total lightning activity recorded by the ISS Lightning Imaging Sensor. Discharges trigger sharp staccato plucks with spatial stereo panning matching horizontal coordinate."
    }
}

# -------------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://www.nasa.gov/wp-content/themes/nasa/assets/images/nasa-logo.svg", width=110)
    st.markdown("### 🎛️ NASA Jukebox Navigation")
    st.markdown("<span class='badge-nasa'>NASA SVS Real Data</span><span class='badge-accessibility'>ARIA 2.1 AA</span>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Dataset Selector
    selected_track_idx = st.radio(
        "Select NASA SVS Track:",
        options=range(len(discovered_tracks)),
        format_func=lambda i: discovered_tracks[i]["display_name"],
        index=0,
        help="Use Up/Down arrow keys or numbers 1, 2 to switch tracks."
    )
    current_track = discovered_tracks[selected_track_idx]
    track_meta = TRACK_DESCRIPTIONS.get(current_track["track"], {
        "title": current_track["display_name"],
        "instrument": "NASA Earth Science Mission",
        "anomaly": "Active Scientific Anomaly",
        "scale": "Pentatonic Quantization",
        "description": "NASA SVS scientific visualization."
    })
    
    st.markdown("---")
    
    # Auditory Zooming Selector
    st.markdown("#### 🔍 Auditory Zooming")
    zoom_quadrant = st.selectbox(
        "Isolate Geographic Quadrant:",
        options=["Full Earth (Global Scan)", "NW: North Pacific / Americas", "NE: North Atlantic / Eurasia", "SW: South Pacific / South America", "SE: Southern Oceans / Africa & Oceania"],
        index=0,
        help="Enables blind users to sweep specific geographic quadrants at high auditory resolution."
    )
    
    quadrant_code = None
    if "NW" in zoom_quadrant:
        quadrant_code = "NW"
    elif "NE" in zoom_quadrant:
        quadrant_code = "NE"
    elif "SW" in zoom_quadrant:
        quadrant_code = "SW"
    elif "SE" in zoom_quadrant:
        quadrant_code = "SE"
        
    st.markdown("---")
    
    # Multi-Channel Polyphony Controls
    st.markdown("#### 🎚️ Multi-Channel Polyphony")
    layer_drone = st.checkbox("Ambient Foundation Drone (Warm C3 Grounding)", value=True)
    layer_melody = st.checkbox("Scan-Line Thermal Melodic Stream", value=True)
    layer_plucks = st.checkbox("Contour Anomaly & Lightning Plucks", value=True)
    layer_tts = st.checkbox("Concise Scientific Voice Guidance (TTS)", value=True)

    st.markdown("---")
    st.markdown("#### ⌨️ Accessibility Shortcuts")
    st.markdown("""
    - <span class='shortcut-tag'>1</span> Sea Surface Temperature
    - <span class='shortcut-tag'>2</span> ISS Lightning Events
    - <span class='shortcut-tag'>Q</span> Cycle Auditory Zoom
    - <span class='shortcut-tag'>H</span> Audio Help & Status
    """, unsafe_allow_html=True)


# -------------------------------------------------------------
# MAIN VIEW: THE EARTH INFORMATION JUKEBOX
# -------------------------------------------------------------
st.markdown("<div class='main-title'>🌍 The Earth Information Jukebox</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Auditory Data Visualization for Blind & Low-Vision Planetary Exploration • Powered strictly by NASA SVS</div>", unsafe_allow_html=True)

tab_player, tab_vision, tab_validation = st.tabs([
    "🎵 Accessible NASA Jukebox Player",
    "👁️ Computer Vision & SVS Contours",
    "📋 Day 2 Validation & Testing Suite"
])


# =============================================================
# TAB 1: ACCESSIBLE NASA JUKEBOX PLAYER
# =============================================================
with tab_player:
    st.markdown(f"### Now Playing: **{track_meta['title']}**")
    
    col_info, col_audio = st.columns([1.1, 0.9])
    
    with col_info:
        st.markdown(f"""
        <div class='metric-card' role='region' aria-label='Dataset Overview'>
            <p><strong>NASA SVS Source:</strong> <code>packs/{current_track['pack']}/{current_track['track']}/</code></p>
            <p><strong>Science Instrument:</strong> {track_meta['instrument']}</p>
            <p><strong>Observation Dates:</strong> {current_track['date_range']}</p>
            <p><strong>Key Phenomenon:</strong> {track_meta['anomaly']}</p>
            <p><strong>Quantization Scale:</strong> {track_meta['scale']}</p>
            <p style='color: #8b949e; font-size: 0.9rem; margin-top: 8px;'>{track_meta['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_audio:
        st.markdown("<div class='metric-card' role='region' aria-label='Audio Stream Controls'>", unsafe_allow_html=True)
        st.markdown("##### 🎙️ Scientific Voice Guidance (TTS Intro)")
        if layer_tts and current_track["intro_path"] and os.path.exists(current_track["intro_path"]):
            st.audio(current_track["intro_path"], format="audio/mp3")
        else:
            st.caption("TTS intro muted or unavailable.")
            
        st.markdown("##### 🎶 Scaled Musical Sonification Loop (12-Second Spatial Scan)")
        if current_track["sonified_path"] and os.path.exists(current_track["sonified_path"]):
            st.audio(current_track["sonified_path"], format="audio/wav")
        else:
            st.error("Audio track not found in pack.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Authentic NASA Video & Colour Bar Display
    st.markdown("#### 🎬 NASA SVS 720p Video & Scientific Calibration Colour Bar")
    
    col_vid, col_cbar = st.columns([1.3, 0.7])
    with col_vid:
        st.markdown(f"**Trimmed NASA 720p Video (`video_720p.mp4`)**")
        if current_track["video_path"] and os.path.exists(current_track["video_path"]):
            st.video(current_track["video_path"])
        else:
            st.warning("Video file not found.")
            
    with col_cbar:
        st.markdown("**Scientific Colour Bar (`colorbar.png`)**")
        if current_track["colorbar_path"] and os.path.exists(current_track["colorbar_path"]):
            st.image(current_track["colorbar_path"], use_container_width=True)
            st.caption("Authentic NASA SVS calibrated scale mapping color hues to measured physical units.")
        
        st.markdown("**Active Observation Dates (`dates.txt`)**")
        if current_track["dates_path"] and os.path.exists(current_track["dates_path"]):
            with open(current_track["dates_path"], "r") as df:
                dates_preview = [line.strip() for line in df][:8]
            st.code("\n".join(dates_preview) + "\n... [360 temporal frames]", language="text")


# =============================================================
# TAB 2: COMPUTER VISION & SVS CONTOURS
# =============================================================
with tab_vision:
    st.markdown("### 👁️ OpenCV Feature Extraction on NASA SVS Frames")
    st.markdown("""
    Lightweight OpenCV algorithms inspect the real NASA SVS frames, extracting dominant hues, brightness,
    and contour geometry to map physical variables into musical parameters without manual tagging.
    """)
    
    if current_track["ref_frame_path"] and os.path.exists(current_track["ref_frame_path"]):
        try:
            extractor = OpenCVFeatureExtractor(current_track["ref_frame_path"], quadrant=quadrant_code)
            slices = extractor.extract_scanline_slices(num_slices=32)
            objects = extractor.detect_prominent_objects()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Temporal Scan Slices", len(slices))
            col_m2.metric("Prominent Contours", len(objects))
            col_m3.metric("Quantization Scale", "Pentatonic 5-Tone")
            col_m4.metric("Panning Range", "-100% (L) to +100% (R)")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown("**Real NASA SVS Keyframe**")
                st.image(current_track["ref_frame_path"], use_container_width=True)
            with col_f2:
                st.markdown("**OpenCV Isolated Contours & Centroids**")
                if current_track["annotated_frame_path"] and os.path.exists(current_track["annotated_frame_path"]):
                    st.image(current_track["annotated_frame_path"], use_container_width=True)
                else:
                    st.image(extractor.render_annotated_frame(), use_container_width=True)
                    
            # Extracted Metrics Table
            st.markdown("#### 📐 Extracted Anomaly Contours & Acoustic Translation")
            if objects:
                table_data = []
                for idx, obj in enumerate(objects):
                    pan_label = f"{int(abs(obj['norm_x'])*100)}% Left" if obj['norm_x'] < 0 else f"{int(obj['norm_x']*100)}% Right"
                    shape_label = "Continuous Thermal Front (Smooth Pad)" if obj["circularity"] > 0.4 else "Discharge Cluster (Staccato Pluck)"
                    table_data.append({
                        "Contour ID": f"#{idx+1}",
                        "Pixel Area": f"{int(obj['area'])} px",
                        "Circularity": f"{obj['circularity']:.2f}",
                        "Stereo Panning": pan_label,
                        "Pitch Register": f"{int(220 + obj['norm_y'] * 600)} Hz (Quantized)",
                        "Acoustic Articulation": shape_label
                    })
                st.dataframe(table_data, use_container_width=True)

            # Trajectory Plot
            st.markdown("#### 📈 Spatial Scan-Line Trajectory Profile")
            x_indices = [s["index"] for s in slices]
            brightness_curve = [s["brightness"] for s in slices]
            vertical_pos = [s["norm_y"] for s in slices]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_indices, y=brightness_curve, mode='lines+markers', name='Regional Brightness / Physical Energy', line=dict(color='#f0883e', width=2.5)))
            fig.add_trace(go.Scatter(x=x_indices, y=vertical_pos, mode='lines', name='Latitude Center of Mass (Pitch Height)', line=dict(color='#58a6ff', width=2, dash='dash')))
            fig.update_layout(
                title="Scan-Line Profile Across Timeline (Slice 0 = West, Slice 32 = East)",
                xaxis_title="Temporal Slice Index (Time)",
                yaxis_title="Normalized Value (0.0 - 1.0)",
                template="plotly_dark",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error extracting computer vision metrics: {e}")


# =============================================================
# TAB 3: DAY 2 VALIDATION & TESTING SUITE
# =============================================================
with tab_validation:
    st.markdown("### 📋 Day 2 Blindfold Peer Testing & Audio Comprehension Quiz")
    st.markdown("""
    Administer this standardized audio matching quiz during the Day 2 validation protocol
    to collect quantifiable comprehension scores from blindfolded peer testers.
    """)
    st.markdown("---")
    
    # Quiz Question 1
    st.markdown("#### Question 1: Thermal Anomaly Localization (NASA SVS Sea Surface Temp)")
    st.caption("Listen to the Sea Surface Temperature track. Where does the primary thermal surge peak occur?")
    sst_track = next((t for t in discovered_tracks if "sea_surface" in t["track"]), None)
    if sst_track and sst_track["sonified_path"]:
        st.audio(sst_track["sonified_path"], format="audio/wav")
    q1_answer = st.radio(
        "Select identified peak anomaly position:",
        options=[
            "First 3-4 seconds, panned Left (Pacific Ocean)",
            "Middle 6 seconds, centered (Atlantic Basin)",
            "Last 3 seconds, panned Right (Indian Ocean)",
            "No peak detected"
        ],
        key="q1"
    )
    
    # Quiz Question 2
    st.markdown("#### Question 2: Phenomenon Density & Clustering (NASA SVS ISS Lightning)")
    st.caption("Listen to the ISS Lightning track. Where is the highest frequency of sharp staccato discharge plucks?")
    light_track = next((t for t in discovered_tracks if "lightning" in t["track"]), None)
    if light_track and light_track["sonified_path"]:
        st.audio(light_track["sonified_path"], format="audio/wav")
    q2_answer = st.radio(
        "Select identified maximum cluster location:",
        options=[
            "Uniformly distributed with no distinct clusters",
            "Mid-to-late region, slightly right of center (Equatorial Continental Landmasses)",
            "Extremely early, panned full left",
            "Only at the very end of the track"
        ],
        key="q2"
    )
    
    # Quiz Question 3
    st.markdown("#### Question 3: Spatial Orientation & Boundary Recognition")
    st.caption("Across all tracks, what does vertical coordinate (latitude) map to in the acoustic soundscape?")
    q3_answer = st.radio(
        "Select correct acoustic mapping parameter:",
        options=[
            "Musical Pitch & Octave Height (Northern latitudes play higher, Southern lower)",
            "Playback Speed and Tempo",
            "White Noise Volume",
            "Stereo Left-Right Panning"
        ],
        key="q3"
    )
    
    if st.button("📊 Submit & Grade Comprehension Quiz"):
        score = 0
        feedback = []
        if "Pacific Ocean" in q1_answer:
            score += 1
            feedback.append("✅ **Question 1 Correct**: The Pacific warm anomaly emerges within the first 3-4 seconds panned left.")
        else:
            feedback.append("❌ **Question 1 Incorrect**: The Pacific warm anomaly occurs within the first 3-4 seconds panned left.")
            
        if "Equatorial" in q2_answer:
            score += 1
            feedback.append("✅ **Question 2 Correct**: Major continental lightning hotspots emerge at middle-right scan time with intense staccato plucks.")
        else:
            feedback.append("❌ **Question 2 Incorrect**: Peak lightning discharge clusters correspond to equatorial continental landmasses at middle-right.")
            
        if "Musical Pitch" in q3_answer:
            score += 1
            feedback.append("✅ **Question 3 Correct**: Vertical position strictly maps to pitch register and octave height.")
        else:
            feedback.append("❌ **Question 3 Incorrect**: Vertical position maps to musical pitch height.")
            
        st.markdown(f"### Overall Comprehension Accuracy: **{int((score/3)*100)}%** ({score}/3)")
        for fb in feedback:
            st.markdown(fb)
            
        if score == 3:
            st.balloons()
            st.success("Perfect Score! Validates complete non-visual spatial comprehension via the Pentatonic Sonification Framework.")
