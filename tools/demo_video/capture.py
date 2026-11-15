"""Films the real Jukebox page frame by frame (30 fps, 1920x1080) and logs every sound event for the audio track."""
import asyncio, json, os, shutil, sys
sys.path.insert(0, '/home/claude/video')
from common import *
from playwright.async_api import async_playwright
FPS = 30
ROOT = '/home/claude/video/scenes'
events = []          # (scene, frame, kind, data)

class Scene:
    def __init__(self, name):
        self.name, self.n, self.dir = name, 0, os.path.join(ROOT, name)
        shutil.rmtree(self.dir, ignore_errors=True); os.makedirs(self.dir)
    async def shot(self, pg, repeat=1):
        data = await pg.screenshot(type='jpeg', quality=92)
        for _ in range(repeat):
            with open(os.path.join(self.dir, f'f_{self.n:04d}.jpg'), 'wb') as fh: fh.write(data)
            self.n += 1

def ease(u): return u * u * (3 - 2 * u)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        ctx = await b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5)
        pg = await ctx.new_page()
        await pg.goto("http://127.0.0.1:5000")
        await pg.wait_for_function("typeof grid !== 'undefined' && grid && audio.readyState >= 1 && img.complete && img.naturalWidth > 0")
        await pg.add_style_tag(content=OVERLAY_CSS); await pg.evaluate(OVERLAY_JS)
        await pg.evaluate("document.activeElement && document.activeElement.blur()")
        top_std = await pg.evaluate("Math.round(document.getElementById('track-list').getBoundingClientRect().top + scrollY - 14)")
        await pg.evaluate(f"window.scrollTo(0,{top_std})")

        # ---- 1. title card (75 frames, from another page)
        card = await ctx.new_page(); await card.set_content(TITLE_HTML); await card.wait_for_timeout(700)
        s = Scene('s1_title'); await s.shot(card, 75)
        events.append(('s1_title', 0, 'logo_up', None))

        # ---- 2. ocean sweep (255 frames)
        s = Scene('s2_sst')
        await pg.evaluate("spot=null; setPlayIcon(true);")
        for k in range(255):
            t = min(k / FPS, 8.0)
            if k == 0: await pg.evaluate("vcap('NASA ocean temperature map. Press Play and a line sweeps it from <b>west to east</b>.')")
            if k == 110: await pg.evaluate("vcap('Warm water plays <b>high notes</b>, cold water plays low notes. Land is <b>silent</b>.')")
            await pg.evaluate(f"audio.currentTime={t:.4f}; updateTime(); draw();")
            await s.shot(pg)
        events.append(('s2_sst', 0, 'wav', {'track': 'sea_surface_temperature', 'start': 0.0, 'dur': 8.5}))

        # ---- 3. explore by clicking (150 frames)
        s = Scene('s3_explore')
        await pg.evaluate("audio.currentTime=0; setPlayIcon(false); updateTime(); draw(); vcap('Click anywhere: hear the note, the <b>name of the place</b> and the value.')")
        r = await pg.evaluate("(()=>{const r=pad.getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
        xy = lambda lat, lon: (r[0] + (lon + 180) / 360 * r[2], r[1] + (90 - lat) / 180 * r[3])
        path = [(xy(-10, 20), None), (xy(15, 65), 14), (xy(19.5, 76.0), 64), (xy(-56, 25), 114)]
        pos = path[0][0]; clicks = {}
        for i in range(1, len(path)):
            clicks[path[i][1]] = (path[i - 1][0], path[i][0])
        ring_at, ring_pos = -100, (0, 0)
        for k in range(150):
            for ck, (a, bb) in clicks.items():
                if ck - 12 <= k < ck:                       # glide to the next spot
                    u = ease((k - (ck - 12) + 1) / 12); pos = (a[0] + (bb[0] - a[0]) * u, a[1] + (bb[1] - a[1]) * u)
                if k == ck:
                    pos = bb
                    await pg.mouse.click(*bb)
                    cell = await pg.evaluate("spot && spot.cell ? {midi: spot.cell.midi, instrument: spot.cell.instrument} : null")
                    txt = await pg.evaluate("document.getElementById('ro-place').textContent + ' | ' + document.getElementById('ro-value').textContent")
                    events.append(('s3_explore', k, 'tone' if cell else 'hush', {'cell': cell, 'pan': (bb[0] - r[0]) / r[2] * 2 - 1, 'text': txt}))
                    ring_at, ring_pos = k, bb
            sc = 1 + (k - ring_at) * 0.08
            await pg.evaluate(f"vcur({pos[0]:.1f},{pos[1]:.1f},true); vring({ring_pos[0]:.1f},{ring_pos[1]:.1f},{str(0 <= k - ring_at < 9).lower()},{sc:.2f});")
            await s.shot(pg)
        await pg.evaluate("vcur(0,0,false); vring(0,0,false)")

        # ---- 4. aerosols sweep, 2.4 to 6.4 s (120 frames)
        s = Scene('s4_aero')
        await pg.evaluate("loadTrack(tracks[1], false)")
        await pg.wait_for_function("img.complete && img.naturalWidth > 0 && audio.readyState >= 1 && current && current.id === 'geos_aerosols_2025'")
        await pg.evaluate(f"document.activeElement && document.activeElement.blur(); window.scrollTo(0,{top_std}); spot=null; setPlayIcon(true);")
        await pg.evaluate("vcap('NASA aerosol map, 19 Aug 2025: Saharan dust plays the <b>strings</b>, smoke plays the <b>bell</b>.')")
        for k in range(120):
            await pg.evaluate(f"audio.currentTime={2.4 + k / FPS:.4f}; updateTime(); draw();")
            await s.shot(pg)
        events.append(('s4_aero', 0, 'wav', {'track': 'geos_aerosols_2025', 'start': 2.4, 'dur': 4.0}))

        # ---- 5. accessible mode: A, then 3, then arrow keys (180 frames)
        s = Scene('s5_access')
        await pg.evaluate("audio.currentTime=0; setPlayIcon(false); updateTime(); setMode('access', false); window.scrollTo(0,0); vkey('A','Accessible mode');")
        await pg.evaluate("vcap('<b>Accessible mode</b> (press A): everything is spoken aloud and works from the keyboard.')")
        await pg.wait_for_timeout(150)
        await s.shot(pg, 45)
        events.append(('s5_access', 0, 'key', None))
        await pg.evaluate("loadTrack(tracks[2], false)")
        await pg.wait_for_function("img.complete && img.naturalWidth > 0 && current && current.id === 'iss_lightning' && grid.cols === 96")
        await pg.evaluate("(()=>{const r=document.querySelector('.readout').getBoundingClientRect(); window.scrollBy(0, r.bottom - (innerHeight - 104));})()")
        await pg.evaluate("vkey('3','Track 3: lightning'); vcap('Press <b>3</b> for the lightning map, then use the <b>arrow keys</b> to explore it.')")
        await pg.wait_for_timeout(150); draw = "draw()"
        await s.shot(pg, 27)
        events.append(('s5_access', 45, 'key', None))
        presses = [(72, 'Shift+ArrowRight', 'Shift + →'), (99, 'ArrowDown', '↓'), (126, 'ArrowRight', '→'), (153, 'ArrowDown', '↓')]
        for i, (fr, key, label) in enumerate(presses):
            await pg.keyboard.press(key)
            cell = await pg.evaluate("spot && spot.cell ? {midi: spot.cell.midi, instrument: spot.cell.instrument} : null")
            fx = await pg.evaluate("spot ? spot.fx : 0.5")
            txt = await pg.evaluate("document.getElementById('ro-place').textContent + ' | ' + document.getElementById('ro-value').textContent")
            events.append(('s5_access', fr, 'tone' if cell else 'hush', {'cell': cell, 'pan': fx * 2 - 1, 'text': txt}))
            if i == 0: await pg.evaluate("vcap('Each step says the <b>place name</b>, then what is there.')")
            await pg.evaluate(f"vkey('{label}','Arrow keys')")
            await s.shot(pg, 27 if i < 3 else 27)
        events.append(('s5_access', 0, 'end', None))

        # ---- 6. end card (90 frames)
        await card.set_content(END_HTML); await card.wait_for_timeout(700)
        s = Scene('s6_end'); await s.shot(card, 90)
        events.append(('s6_end', 0, 'logo_end', None))
        await b.close()
    counts = {d: len(os.listdir(os.path.join(ROOT, d))) for d in sorted(os.listdir(ROOT))}
    json.dump({'events': events, 'counts': counts}, open('/home/claude/video/events.json', 'w'), indent=1)
    print(counts, sum(counts.values()) / FPS, 's')
    for e in events:
        if e[2] in ('tone', 'hush'): print(e[0], e[1], e[2], e[3]['text'], e[3]['cell'])

asyncio.run(main())
