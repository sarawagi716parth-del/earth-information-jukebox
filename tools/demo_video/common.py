OVERLAY_CSS = """
#vid-cap{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);width:max-content;max-width:1180px;padding:12px 24px;
 border-radius:16px;background:rgba(5,8,20,.93);border:1.5px solid rgba(255,209,102,.75);color:#fff;
 font:600 23px/1.35 "Segoe UI",system-ui,sans-serif;text-align:center;z-index:9999;box-shadow:0 14px 44px rgba(0,0,0,.65)}
#vid-cap:empty{display:none}
#vid-cap b{color:#ffd166}
#vid-cur{position:fixed;width:36px;height:36px;pointer-events:none;z-index:10001;display:none;left:0;top:0;transform:translate(-5px,-3px)}
#vid-ring{position:fixed;width:52px;height:52px;border-radius:50%;border:4px solid #ffd166;pointer-events:none;z-index:10000;display:none;transform:translate(-50%,-50%)}
#vid-key{position:fixed;right:28px;bottom:96px;z-index:10002;display:none;align-items:center;gap:14px;padding:12px 18px;border-radius:16px;
 background:rgba(5,8,20,.94);border:2px solid #ffd166;color:#fff;font:600 19px "Segoe UI",system-ui,sans-serif;box-shadow:0 14px 44px rgba(0,0,0,.65)}
#vid-key kbd{font:800 25px ui-monospace,Consolas,monospace;background:#ffd166;color:#111;border-radius:9px;padding:4px 16px;border:0}
::-webkit-scrollbar{display:none}
"""
OVERLAY_JS = """
(() => {
  const mk = (tag, id, html) => { const e = document.createElement(tag); e.id = id; if (html) e.innerHTML = html; document.body.appendChild(e); return e; };
  mk('div','vid-cap');
  mk('div','vid-ring');
  mk('div','vid-key');
  mk('div','vid-cur','<svg viewBox="0 0 24 24" width="36" height="36"><path d="M3 2l15 11.5-6.6.9 3.9 7.4-3 1.5-3.8-7.5L3 20.5z" fill="#fff" stroke="#000" stroke-width="1.4" stroke-linejoin="round"/></svg>');
  window.vcap = (h) => { document.getElementById('vid-cap').innerHTML = h || ''; };
  window.vcur = (x, y, show) => { const c = document.getElementById('vid-cur'); c.style.display = show ? 'block' : 'none'; c.style.left = x + 'px'; c.style.top = y + 'px'; };
  window.vring = (x, y, show, scale) => { const r = document.getElementById('vid-ring'); r.style.display = show ? 'block' : 'none'; r.style.left = x + 'px'; r.style.top = y + 'px';
    r.style.transform = `translate(-50%,-50%) scale(${scale||1})`; r.style.opacity = String(Math.max(0, 1.4 - (scale||1))); };
  window.vkey = (k, label) => { const e = document.getElementById('vid-key'); if (!k) { e.style.display = 'none'; return; }
    e.style.display = 'flex'; e.innerHTML = `<span>${label || 'Key pressed'}</span><kbd>${k}</kbd>`; };
})();
"""
CARD_CSS = """
*{box-sizing:border-box}html,body{margin:0;width:1280px;height:720px;overflow:hidden;background:#060a17;color:#eef2fb;font-family:"Segoe UI",system-ui,sans-serif}
.bg{position:absolute;inset:0;background:url('http://127.0.0.1:5000/packs/sea_surface_temperature/image.jpg') center/cover;filter:saturate(1.2) brightness(.62)}
.shade{position:absolute;inset:0;background:radial-gradient(900px 520px at 50% 48%, rgba(6,10,23,.62), rgba(6,10,23,.88))}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:60px}
.logo{width:96px;height:96px;filter:drop-shadow(0 0 28px rgba(255,209,102,.55));margin-bottom:26px}
h1{font-size:62px;margin:0;letter-spacing:-.01em;line-height:1.08}
.sub{font-size:29px;color:#ffd166;margin-top:18px;font-weight:600}
.team{font-size:21px;color:#c9d2e8;margin-top:44px}
.team b{color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin-top:40px;max-width:1100px}
.chip{font-size:22px;padding:10px 20px;border-radius:999px;background:rgba(16,24,48,.85);border:1.5px solid rgba(255,209,102,.6)}
.small{font-size:16px;color:#a9b4cf;margin-top:34px}
"""
LOGO = '<svg class="logo" viewBox="0 0 48 48"><circle cx="24" cy="24" r="22" fill="#12204a" stroke="#ffd166" stroke-width="2"/><path d="M9 24h5l3-9 5 18 5-14 3 9 3-4h6" fill="none" stroke="#ffd166" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
TITLE_HTML = f"""<html><head><style>{CARD_CSS}</style></head><body><div class="bg"></div><div class="shade"></div><div class="wrap">{LOGO}
<h1>The Earth Information Jukebox</h1><div class="sub">Hear NASA's pictures of Earth</div>
<div class="team"><b>Team CodeHub</b> &nbsp;|&nbsp; NASA Space Apps Challenge 2026</div></div></body></html>"""
END_HTML = f"""<html><head><style>{CARD_CSS}</style></head><body><div class="bg"></div><div class="shade"></div><div class="wrap">{LOGO}
<h1 style="font-size:50px">The Earth Information Jukebox</h1>
<div class="chips"><span class="chip">3 real NASA images</span><span class="chip">Place name for any spot</span>
<span class="chip">Accessible mode</span><span class="chip">28 of 28 checks pass</span></div>
<div class="team"><b>Team CodeHub</b> &nbsp;|&nbsp; NASA Space Apps Challenge 2026</div>
<div class="small">Images: NASA Scientific Visualization Studio (SVS 3912, 5669, 5011) &nbsp;|&nbsp; Place names: Natural Earth</div></div></body></html>"""
