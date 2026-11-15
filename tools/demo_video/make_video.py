import json, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve
sys.path.insert(0, '/home/claude/jb3')
import jukebox_engine as je
SR, FPS = 44100, 30
E = json.load(open('events.json'))
order = ['s1_title', 's2_sst', 's3_explore', 's4_aero', 's5_access', 's6_end']
start, t = {}, 0.0
for s in order:
    start[s] = t; t += E['counts'][s] / FPS
TOTAL = t
mix = np.zeros((int(TOTAL * SR) + SR, 2))

def reverb(x, wet=0.2):
    rng = np.random.default_rng(7); n = int(1.4 * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.35); ir = np.convolve(ir, np.ones(12) / 12, mode='same'); ir /= np.sqrt(np.sum(ir ** 2))
    return x + wet * np.stack([fftconvolve(x[:, c], np.roll(ir, c * 37))[:len(x)] for c in range(2)], axis=1)

def notes_to_audio(notes, length, peak):
    out = np.zeros((int(length * SR), 2))
    for (tt, inst, midi, vel, pan) in notes:
        sig = je.INSTRUMENTS[inst](je.hz(midi), 0.6) * je.GAINS[inst] * vel
        s0 = int(tt * SR); e = min(len(out), s0 + len(sig)); th = (pan + 1) * np.pi / 4
        out[s0:e, 0] += sig[:e - s0] * np.cos(th); out[s0:e, 1] += sig[:e - s0] * np.sin(th)
    out = reverb(out)
    return out / (np.max(np.abs(out)) + 1e-9) * peak

def put(sig, t0, gain=1.0):
    s0 = int(round(t0 * SR)); e = min(len(mix), s0 + len(sig)); mix[s0:e] += sig[:e - s0] * gain

def wav_segment(track, a, dur, fade_in=0.04, fade_out=0.3):
    sr, x = wavfile.read(f'/home/claude/jb3/packs/{track}/sonified.wav'); x = x.astype(np.float32) / 32767
    seg = x[int(a * sr):int((a + dur) * sr)].copy(); n = len(seg)
    seg[:int(fade_in * sr)] *= np.linspace(0, 1, int(fade_in * sr))[:, None]
    seg[n - int(fade_out * sr):] *= np.linspace(1, 0, int(fade_out * sr))[:, None]
    return seg

def puff(pan):
    n = int(0.14 * SR); rng = np.random.default_rng(3)
    d = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)) * 0.22
    th = (pan + 1) * np.pi / 4
    return np.stack([d * np.cos(th), d * np.sin(th)], axis=1)

def click():
    n = int(0.03 * SR); d = np.sin(2 * np.pi * 1800 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.005 * SR)) * 0.25
    return np.stack([d, d], axis=1)

for scene, frame, kind, data in E['events']:
    t0 = start[scene] + frame / FPS
    if kind == 'logo_up':
        put(notes_to_audio([(0.20, 'marimba', 60, 0.8, -0.6), (0.42, 'marimba', 64, 0.8, -0.3), (0.64, 'marimba', 67, 0.85, 0.0),
                            (0.86, 'marimba', 69, 0.9, 0.3), (1.08, 'marimba', 72, 1.0, 0.6), (1.08, 'strings', 60, 0.55, 0.0)], 2.5, 0.55), t0)
    elif kind == 'logo_end':
        put(notes_to_audio([(0.15, 'bell', 72, 0.8, -0.5), (0.35, 'bell', 76, 0.8, -0.15), (0.55, 'bell', 79, 0.85, 0.15),
                            (0.80, 'bell', 84, 0.9, 0.5), (0.80, 'strings', 60, 0.6, 0.0), (0.80, 'strings', 67, 0.5, 0.0)], 3.0, 0.55), t0)
    elif kind == 'wav':
        put(wav_segment(data['track'], data['start'], data['dur']), t0)
    elif kind == 'tone':
        c = data['cell']
        put(notes_to_audio([(0.0, c['instrument'], c['midi'], 1.0, data['pan'] * 0.85)], 1.4, 0.6), t0)
    elif kind == 'hush':
        put(puff(data['pan'] * 0.85), t0)
    elif kind == 'key':
        put(click(), t0)

n = int(TOTAL * SR); mix = mix[:n]
f = int(0.6 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
peak = np.max(np.abs(mix)); mix = np.tanh(1.1 * mix / peak) / np.tanh(1.1) * 0.89
wavfile.write('soundtrack.wav', SR, (mix * 32767).astype(np.int16))
print('total', TOTAL, 's; scene starts', {k: round(v, 2) for k, v in start.items()})

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: print(r.stderr[-1500:]); raise SystemExit(1)

os.makedirs('enc', exist_ok=True)
for s in order:
    nfr = E['counts'][s]; vf = 'format=yuv420p'
    if s == 's1_title': vf = 'fade=t=in:st=0:d=0.4,format=yuv420p'
    if s == 's6_end': vf = f'fade=t=out:st={nfr / FPS - 0.6:.3f}:d=0.6,format=yuv420p'
    tmp, final = f'enc/{s}.tmp.mp4', f'enc/{s}.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'scenes/{s}/f_%04d.jpg', '-vf', vf,
         '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp])
    os.replace(tmp, final)
with open('enc/list.txt', 'w') as fh:
    fh.writelines(f"file '{s}.mp4'\n" for s in order)
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'enc/list.txt', '-c', 'copy', 'enc/video_only.mp4'])
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'enc/video_only.mp4', '-i', 'soundtrack.wav', '-map', '0:v', '-map', '1:a',
     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'enc/final.tmp.mp4'])
os.replace('enc/final.tmp.mp4', 'CodeHub_Earth_Information_Jukebox_demo.mp4')
print('done')
