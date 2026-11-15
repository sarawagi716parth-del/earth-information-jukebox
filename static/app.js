// The Earth Information Jukebox - page logic
// Two modes: "standard" (mouse and eyes) and "access" (keyboard and voice, for blind and low-vision users).
const $ = (id) => document.getElementById(id);
const audio = $("audio"), img = $("track-image"), canvas = $("overlay"), pad = $("explore-pad"), seek = $("seek");
let tracks = [], current = null, grid = null, places = null, actx = null;
let mode = "standard", spot = null, speakTimer = null, dragging = false;

const ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';

async function init() {
  const [list] = await Promise.all([fetch("/api/tracks").then((r) => r.json()), loadPlaces()]);
  tracks = list;
  let saved = "standard";
  try { saved = localStorage.getItem("jukebox-mode") || "standard"; } catch (e) { /* storage not available */ }
  if (tracks.length) await loadTrack(tracks[0], false);
  setMode(saved, false);
}

// ---------------------------------------------------------------- place names (Natural Earth lookup grid)
async function loadPlaces() {
  try {
    const p = await (await fetch("/static/places.json")).json();
    const cells = new Uint16Array(p.cols * p.rows);
    for (let i = 0, k = 0; i < p.rle.length; i += 2) { cells.fill(p.rle[i], k, k + p.rle[i + 1]); k += p.rle[i + 1]; }
    places = { cols: p.cols, rows: p.rows, names: p.names, waterMax: p.water_max, cells };
  } catch (e) { places = null; }
}
function placeAt(lat, lon) {
  if (!places) return null;
  const x = Math.min(places.cols - 1, Math.max(0, Math.floor((lon + 180) / 360 * places.cols)));
  const y = Math.min(places.rows - 1, Math.max(0, Math.floor((90 - lat) / 180 * places.rows)));
  const id = places.cells[y * places.cols + x];
  return { name: places.names[id], water: id <= places.waterMax };
}

// ---------------------------------------------------------------- tracks
function renderTrackList() {
  const ul = $("track-list");
  ul.innerHTML = "";
  tracks.forEach((t, i) => {
    const li = document.createElement("li"), b = document.createElement("button");
    b.className = "track-card";
    b.setAttribute("aria-pressed", current && current.id === t.id ? "true" : "false");
    b.innerHTML = `<span class="thumb" style="background-image:url('${t.image_url}')"></span>` +
      `<span class="track-meta"><span class="track-num">Track ${i + 1}</span><span class="track-title"></span></span>`;
    b.querySelector(".track-title").textContent = t.title;
    b.onclick = () => loadTrack(t, true);
    li.appendChild(b); ul.appendChild(li);
  });
  const li = document.createElement("li"), up = document.createElement("button");
  up.className = "track-card upload-card";
  up.innerHTML = '<span class="thumb" aria-hidden="true">+</span><span class="track-meta"><span class="track-num">Your own</span>' +
    '<span class="track-title">Upload an image</span></span>';
  up.onclick = () => $("upload-input").click();
  li.appendChild(up); ul.appendChild(li);
}

async function loadTrack(t, announceIt) {
  current = t; spot = null;
  audio.pause();
  audio.src = t.audio_url;
  seek.value = 0;
  img.onload = draw;
  img.src = t.image_url;
  img.alt = t.title + ". A full description is below the picture.";
  $("track-title").textContent = t.title;
  $("image-description").textContent = t.image_description;
  const ad = $("audio-description"); ad.innerHTML = "";
  t.audio_description.split("\n").forEach((line) => { const p = document.createElement("p"); p.textContent = line; ad.appendChild(p); });
  $("listen-for").textContent = t.listen_for || "where the notes rise, fall and go silent as the sweep crosses the picture.";
  $("credit").textContent = t.credit || "";
  const link = $("source-link");
  if (t.source && t.source.startsWith("http")) { link.href = t.source; link.hidden = false; } else { link.hidden = true; }
  const legend = $("legend"); legend.innerHTML = "";
  (t.instruments || []).forEach((x) => {
    const li = document.createElement("li");
    li.innerHTML = (x.colour ? `<span class="swatch" style="background:${x.colour}"></span>` : "") + '<span class="inst"></span><span class="mean"></span>';
    li.querySelector(".inst").textContent = x.instrument;
    li.querySelector(".mean").textContent = x.meaning;
    legend.appendChild(li);
  });
  grid = await (await fetch(t.grid_url)).json();
  setReadout("Explore the picture", "Click or drag on the picture, or use the arrow keys, to hear any spot.", "");
  setPlayIcon(false);
  $("time-now").textContent = "0.0 s";
  renderTrackList();
  draw();
  if (mode === "access") {
    pad.focus({ preventScroll: true });
    if (announceIt) announce(`Track ${tracks.indexOf(t) + 1}: ${t.title}. Press Space to play. Press I for the image description, or S for the sound description.`);
  }
}

// ---------------------------------------------------------------- modes
function setMode(m, announceIt) {
  mode = m === "access" ? "access" : "standard";
  document.body.dataset.mode = mode;
  $("mode-standard").setAttribute("aria-pressed", String(mode === "standard"));
  $("mode-access").setAttribute("aria-pressed", String(mode === "access"));
  $("access-help").hidden = mode !== "access";
  try { localStorage.setItem("jukebox-mode", mode); } catch (e) { /* storage not available */ }
  if (mode === "access") {
    $("speak-toggle").checked = true;
    pad.focus({ preventScroll: true });
    if (announceIt) announce(`Accessible mode is on. ${current ? "The track is: " + current.title + ". " : ""}Press Space to play the sound. ` +
      "Use the arrow keys to move around the picture, and I will say the name of the place and what is there. Press H to hear all the keys.");
  } else if (announceIt) announce("Standard mode is on.");
  requestAnimationFrame(draw);
}
$("mode-standard").onclick = () => setMode("standard", true);
$("mode-access").onclick = () => setMode("access", true);

// ---------------------------------------------------------------- voice
const voiceOn = () => $("speak-toggle").checked;
function say(text, interrupt) {
  if (!("speechSynthesis" in window)) return;
  if (interrupt) speechSynthesis.cancel();
  String(text).split(/(?<=[.!?])\s+/).forEach((part) => {       // short pieces: long ones can get cut off
    if (!part.trim()) return;
    const u = new SpeechSynthesisUtterance(part); u.rate = 1.0; speechSynthesis.speak(u);
  });
}
function announce(text) {                                         // voice + screen reader live region
  $("announcer").textContent = "";
  setTimeout(() => { $("announcer").textContent = text; }, 40);
  if (voiceOn()) say(text, true);
}
function stopTalking() { clearTimeout(speakTimer); if ("speechSynthesis" in window) speechSynthesis.cancel(); }
const soundText = () => current.audio_description.replace(/\n/g, " ") + (current.listen_for ? " Listen for: " + current.listen_for : "");
$("read-btn").onclick = () => { if (current) { stopTalking(); say("About the image. " + current.image_description + " About the sound. " + soundText()); } };
$("stop-btn").onclick = stopTalking;
const helpText = () => `Keys. Space: play or pause the sound. Arrow keys: move around the picture. Hold Shift for bigger steps. ` +
  `W: where am I. Numbers 1 to ${tracks.length}: choose a track. I: describe the image. S: describe the sound. ` +
  "V: turn my voice off or on. Escape: stop talking. A: go back to standard mode.";

// ---------------------------------------------------------------- playback + playhead
function togglePlay() { if (audio.paused) { stopTalking(); audio.play(); } else audio.pause(); }
function setPlayIcon(playing) {
  const b = $("play-btn");
  b.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
  b.setAttribute("aria-label", playing ? "Pause the sound" : "Play the sound");
}
function updateTime() {
  $("time-now").textContent = audio.currentTime.toFixed(1) + " s";
  if (audio.duration) seek.value = Math.round(audio.currentTime / audio.duration * 1000);
}
function tick() { updateTime(); draw(); if (!audio.paused) requestAnimationFrame(tick); }
$("play-btn").onclick = togglePlay;
audio.onplay = () => { setPlayIcon(true); requestAnimationFrame(tick); };
audio.onpause = () => { setPlayIcon(false); draw(); };
audio.onended = () => { setPlayIcon(false); draw(); if (mode === "access") announce("End of the sound. Press Space to play it again."); };
audio.onloadedmetadata = () => { $("time-total").textContent = audio.duration.toFixed(1) + " s"; };
seek.oninput = () => { if (audio.duration) { audio.currentTime = seek.value / 1000 * audio.duration; updateTime(); draw(); } };

function boxPx() {
  const b = (current && current.map_box) || [0, 0, 1, 1];
  return { x0: b[0] * canvas.width, y0: b[1] * canvas.height, x1: b[2] * canvas.width, y1: b[3] * canvas.height };
}
function draw() {
  const r = img.getBoundingClientRect();
  if (!r.width) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = r.width * dpr; canvas.height = r.height * dpr;
  const g = canvas.getContext("2d"), b = boxPx();
  g.clearRect(0, 0, canvas.width, canvas.height);
  if (current && audio.currentTime > 0 && audio.currentTime <= current.duration + 0.05) {      // the sweep line
    const x = b.x0 + (audio.currentTime / current.duration) * (b.x1 - b.x0);
    const grad = g.createLinearGradient(x - 46 * dpr, 0, x, 0);
    grad.addColorStop(0, "rgba(255,209,102,0)"); grad.addColorStop(1, "rgba(255,209,102,0.35)");
    g.fillStyle = grad; g.fillRect(x - 46 * dpr, b.y0, 46 * dpr, b.y1 - b.y0);
    g.fillStyle = "#ffd166"; g.fillRect(x - dpr, b.y0, 2 * dpr, b.y1 - b.y0);
  }
  if (spot) {                                                                                   // the explore marker
    const x = b.x0 + spot.fx * (b.x1 - b.x0), y = b.y0 + spot.fy * (b.y1 - b.y0), rad = (mode === "access" ? 18 : 11) * dpr;
    g.lineWidth = 6 * dpr; g.strokeStyle = "rgba(0,0,0,.7)"; g.beginPath(); g.arc(x, y, rad, 0, Math.PI * 2); g.stroke();
    g.lineWidth = 3 * dpr; g.strokeStyle = "#ffd166"; g.beginPath(); g.arc(x, y, rad, 0, Math.PI * 2); g.stroke();
    g.fillStyle = "#ffd166"; g.beginPath(); g.arc(x, y, 3 * dpr, 0, Math.PI * 2); g.fill();
  }
}
window.addEventListener("resize", draw);

// ---------------------------------------------------------------- explore: place name + value at any spot
function describe(fx, fy) {
  const c = Math.min(grid.cols - 1, Math.max(0, Math.floor(fx * grid.cols)));
  const r = Math.min(grid.rows - 1, Math.max(0, Math.floor(fy * grid.rows)));
  const cell = grid.cells[r][c];
  let place = "", coords = "", coordsSpoken = "", water = null;
  if (current.projection === "equirect") {
    const lat = 90 - fy * 180, lon = -180 + fx * 360, p = placeAt(lat, lon);
    if (p) { place = p.name; water = p.water; }
    coords = `${Math.abs(lat).toFixed(1)}° ${lat >= 0 ? "N" : "S"}, ${Math.abs(lon).toFixed(1)}° ${lon >= 0 ? "E" : "W"}`;
    coordsSpoken = `${Math.abs(lat).toFixed(0)} degrees ${lat >= 0 ? "north" : "south"}, ${Math.abs(lon).toFixed(0)} degrees ${lon >= 0 ? "east" : "west"}`;
  } else {
    const h = ["left", "centre", "right"][Math.min(2, Math.floor(fx * 3))], v = ["Top", "Middle", "Bottom"][Math.min(2, Math.floor(fy * 3))];
    place = `${v} ${h} of the picture`;
  }
  let value;
  if (cell) value = cell.label;
  else if (water === false && current.empty_label_land) value = current.empty_label_land;
  else value = current.empty_label || "Nothing here, no data";
  return { fx, fy, c, r, cell, place, coords, coordsSpoken, value };
}
function setReadout(place, value, coords) {
  $("ro-place").textContent = place; $("ro-value").textContent = value; $("ro-coords").textContent = coords;
}
function probe(fx, fy, speakDelay = 200) {
  if (!grid || !current) return;
  spot = describe(fx, fy);
  setReadout(spot.place || "Unnamed place", spot.value, spot.coords);
  draw();
  const pan = fx * 2 - 1;
  if (spot.cell) tone(spot.cell.midi, spot.cell.instrument, pan); else hush(pan);
  clearTimeout(speakTimer);
  if (voiceOn()) speakTimer = setTimeout(() => say(`${spot.place ? spot.place + ". " : ""}${spot.value}.`, true), speakDelay);
}
function moveCursor([dc, dr], step) {
  if (!grid) return;
  const c0 = spot ? spot.c : Math.floor(grid.cols / 2), r0 = spot ? spot.r : Math.floor(grid.rows / 2);
  const c = Math.max(0, Math.min(grid.cols - 1, c0 + dc * step)), r = Math.max(0, Math.min(grid.rows - 1, r0 + dr * step));
  if (spot && c === c0 && r === r0) { hush(0); if (voiceOn()) say("Edge of the picture.", true); return; }
  probe((c + 0.5) / grid.cols, (r + 0.5) / grid.rows);
}
function pointerFrac(e) {
  const r = pad.getBoundingClientRect(), b = current.map_box || [0, 0, 1, 1];
  return [((e.clientX - r.left) / r.width - b[0]) / (b[2] - b[0]), ((e.clientY - r.top) / r.height - b[1]) / (b[3] - b[1])];
}
const inside = (fx, fy) => fx >= 0 && fx <= 1 && fy >= 0 && fy <= 1;
pad.addEventListener("pointerdown", (e) => {
  if (!grid) return;
  const [fx, fy] = pointerFrac(e);
  if (!inside(fx, fy)) return;
  dragging = true;
  try { pad.setPointerCapture(e.pointerId); } catch (err) { /* not supported */ }
  pad.focus({ preventScroll: true });
  probe(fx, fy, 120);
});
pad.addEventListener("pointermove", (e) => {                       // drag to scan: notes follow, voice waits for a pause
  if (!dragging || !grid) return;
  const [fx, fy] = pointerFrac(e);
  if (!inside(fx, fy)) return;
  const c = Math.min(grid.cols - 1, Math.floor(fx * grid.cols)), r = Math.min(grid.rows - 1, Math.floor(fy * grid.rows));
  if (!spot || c !== spot.c || r !== spot.r) probe(fx, fy, 350);
});
["pointerup", "pointercancel"].forEach((n) => pad.addEventListener(n, () => { dragging = false; }));
pad.addEventListener("focus", draw);

// ---------------------------------------------------------------- keyboard
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const interactive = e.target.closest ? e.target.closest("button, input, a, summary") : null;
  const onPad = e.target === pad, free = onPad || (mode === "access" && !interactive);
  const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (key === "a") { e.preventDefault(); setMode(mode === "access" ? "standard" : "access", true); return; }
  if (key === "Escape") { stopTalking(); return; }
  const arrows = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  if (arrows[key] && free) { e.preventDefault(); moveCursor(arrows[key], e.shiftKey ? 5 : 1); return; }
  if ((key === " " || key === "Enter") && free) { e.preventDefault(); togglePlay(); return; }
  if (mode !== "access" || !current) return;
  if (/^[1-9]$/.test(key)) {
    const t = tracks[Number(key) - 1];
    if (t) loadTrack(t, true); else announce(`There is no track ${key}. There are ${tracks.length} tracks.`);
    return;
  }
  if (key === "i") { stopTalking(); say("About the image. " + current.image_description); }
  else if (key === "s") { stopTalking(); say("About the sound. " + soundText()); }
  else if (key === "h" || key === "?") { stopTalking(); say(helpText()); }
  else if (key === "w") {
    stopTalking();
    say(spot ? `${spot.place}. ${spot.value}. ${spot.coordsSpoken ? "Position: " + spot.coordsSpoken + "." : ""}`
             : "You have not picked a spot yet. Use the arrow keys to move around the picture.");
  } else if (key === "v") {
    const box = $("speak-toggle");
    box.checked = !box.checked;
    stopTalking();
    $("announcer").textContent = box.checked ? "Built-in voice on." : "Built-in voice off.";
    say(box.checked ? "Voice on." : "Voice off.");
  }
});

// ---------------------------------------------------------------- small synth for Explore
function ctx() { if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)(); return actx; }
function tone(midi, instrument, pan) {
  const a = ctx(), t = a.currentTime, f = 440 * Math.pow(2, (midi - 69) / 12);
  const out = a.createGain(), p = a.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan * 0.85));
  out.connect(p).connect(a.destination);
  const voice = (type, freq, gain, attack, decay) => {
    const o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(gain, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
    o.connect(g).connect(out); o.start(t); o.stop(t + attack + decay + 0.05);
  };
  switch (instrument) {
    case "strings": voice("sawtooth", f, 0.08, 0.06, 0.9); voice("sine", f, 0.15, 0.06, 0.9); break;
    case "pluck": voice("triangle", f, 0.3, 0.004, 0.5); break;
    case "bell": voice("sine", f, 0.25, 0.002, 1.2); voice("sine", f * 2.76, 0.08, 0.002, 0.5); break;
    case "flute": voice("sine", f, 0.25, 0.05, 0.6); break;
    default: voice("sine", f, 0.3, 0.003, 0.6); voice("sine", f * 3.93, 0.06, 0.002, 0.12);
  }
}
function hush(pan) {                       // soft noise puff = "nothing here"
  const a = ctx(), n = Math.floor(a.sampleRate * 0.12), buf = a.createBuffer(1, n, a.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (n / 4)) * 0.08;
  const s = a.createBufferSource(), p = a.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan * 0.85));
  s.buffer = buf; s.connect(p).connect(a.destination); s.start();
}

// ---------------------------------------------------------------- upload your own image
$("upload-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const status = $("upload-status");
  status.textContent = "Turning your image into music...";
  const fd = new FormData(); fd.append("image", file);
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();
  e.target.value = "";
  if (!res.ok) { status.textContent = data.error || "Something went wrong."; return; }
  data.title = "Your image: " + data.title;
  tracks.push(data);
  status.textContent = "Done. Your image is now a track.";
  loadTrack(data, true);
});

init();
