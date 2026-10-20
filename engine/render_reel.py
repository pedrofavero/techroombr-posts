#!/usr/bin/env python3
"""
Renderizador de Reels — The Tech Room (v1)
Uso: python3 engine/render_reel.py posts/<slug>/reel.json [...]
Saída: posts/<slug>/reel.mp4 (1080x1920, 30 fps, H.264 + AAC), reel_cover.jpg, reel_legenda.txt, _reel_prancha.jpg

REEL (reel.json): slug, [display "sans"|"serif"], [accent "#hex"], [music "reels/musica/x.mp3"], [music_volume 0.0-1.0],
                  [voice "posts/<slug>/voz.mp3"], scenes[], legenda

CENA (scenes[]):
  media    fotos/<x>.jpg (Ken Burns: zoom lento) ou videos/<x>.mp4 (b-roll real; cortado/escalado para 1080x1920)
  start    segundo inicial do vídeo (padrão 0)
  dur      duração da cena em segundos (3 a 7; padrão 4)
  kicker   rótulo pequeno em caixa alta (opcional)
  text     texto principal; aceita **negrito** e ==destaque==
  big      true = texto grande em fonte de título (capa, virada, número); false = texto corrido (padrão)
  credit   "Vídeo: Nome / Pexels" ou "Foto: Nome / Unsplash" (opcional; aparece pequeno no topo direito)
  align    "bottom" (padrão) ou "center"

Regras de tela: 1080x1920 com zonas seguras do Instagram (topo 250 px e base 420 px ficam livres de texto).
Transição: fundido cruzado de 0,5 s entre cenas. Duração total = soma das cenas − 0,5 s por transição.
"""
import json, re, shutil, subprocess, sys, tempfile
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS, XF = 1080, 1920, 30, 0.5

# fontes embutidas do molde dos carrosséis (mesma tipografia)
_nat = (ROOT / "engine" / "natgeo.html").read_text(encoding="utf-8")
FONTS = _nat.split("<style>", 1)[1].split("* { margin: 0;", 1)[0]

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:transparent; }
.page { position:relative; width:1080px; height:1920px; font-family:"Lato",sans-serif; color:#fff;
        -webkit-font-smoothing:antialiased; --display:"Montserrat"; }
.page.serif { --display:"Playfair Display"; }
.scrim { position:absolute; inset:0;
  background: linear-gradient(to bottom, rgba(0,0,0,.45) 0%, rgba(0,0,0,0) 18%),
              linear-gradient(to top, rgba(0,0,0,.90) 0%, rgba(0,0,0,.78) 30%, rgba(0,0,0,.35) 58%, rgba(0,0,0,0) 78%); }
.page.center .scrim { background: linear-gradient(to bottom, rgba(0,0,0,.55) 0%, rgba(0,0,0,.72) 50%, rgba(0,0,0,.88) 100%); }
.masthead { position:absolute; top:270px; left:72px; font-family:"Montserrat"; font-weight:600; font-size:22px;
            letter-spacing:.32em; text-transform:uppercase; text-shadow:0 1px 8px rgba(0,0,0,.5); }
.credit { position:absolute; top:272px; right:72px; font-size:17px; letter-spacing:.06em; opacity:.8; }
.handle { position:absolute; left:72px; bottom:440px; font-size:20px; letter-spacing:.08em; opacity:.8; }
.bar { position:absolute; left:72px; right:72px; bottom:420px; height:4px; background:rgba(255,255,255,.22); border-radius:2px; }
.bar i { display:block; height:4px; background:var(--accent); border-radius:2px; }
.text { position:absolute; left:72px; right:150px; bottom:500px; }
.page.center .text { top:50%; transform:translateY(-50%); bottom:auto; }
.kicker { font-family:"Montserrat"; font-weight:600; font-size:22px; letter-spacing:.3em; text-transform:uppercase;
          color:var(--accent); margin-bottom:28px; }
.big { font-family:var(--display); font-weight:800; font-size:76px; line-height:1.1; text-shadow:0 2px 18px rgba(0,0,0,.45); }
.page.sans .big { text-transform:uppercase; font-weight:700; font-size:68px; letter-spacing:.01em; }
.body { font-size:48px; line-height:1.38; text-shadow:0 1px 10px rgba(0,0,0,.5); }
.body b, .big b { font-weight:800; }
mark { background:none; color:var(--accent); }
"""

def rich(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    return t.replace("\n", "<br>")

def overlay_html(reel, s, i, n):
    serif = reel.get("display", "sans") == "serif"
    cls = " ".join(["page", "serif" if serif else "sans", "center" if s.get("align") == "center" else ""])
    kicker = f'<div class="kicker">{escape(s["kicker"])}</div>' if s.get("kicker") else ""
    body = f'<div class="{"big" if s.get("big") else "body"}">{rich(s.get("text", ""))}</div>'
    credit = f'<div class="credit">{escape(s["credit"])}</div>' if s.get("credit") else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{CSS}</style></head><body>'
            f'<div class="{cls}" style="--accent:{reel.get("accent", "#F2B36B")}"><div class="scrim"></div>'
            f'<div class="masthead">{escape(reel.get("masthead", "The Tech Room"))}</div>{credit}'
            f'<div class="text">{kicker}{body}</div>'
            f'<div class="handle">{escape(reel.get("handle", "@techroombr"))}</div>'
            f'<div class="bar"><i style="width:{(i + 1) / n * 100:.1f}%"></i></div></div></body></html>')

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); raise SystemExit(f"ffmpeg falhou: {' '.join(map(str, cmd[:6]))} …")

def scene_clip(s, ov, dest, idx):
    media = ROOT / s["media"]; dur = float(s.get("dur", 4)); frames = int(dur * FPS)
    if media.suffix.lower() in (".mp4", ".mov", ".webm", ".m4v"):
        vf = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1[v]"
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-ss", str(s.get("start", 0)), "-t", str(dur), "-i", str(media)]
    else:  # foto: Ken Burns (zoom in nas cenas pares, zoom out nas ímpares)
        z = f"1+0.10*on/{frames}" if idx % 2 == 0 else f"1.10-0.10*on/{frames}"
        vf = (f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},setsar=1[v]")
        cmd = ["ffmpeg", "-y", "-i", str(media)]
    cmd += ["-i", str(ov), "-filter_complex", vf + ";[v][1:v]overlay=0:0,format=yuv420p[o]", "-map", "[o]",
            "-t", str(dur), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19", str(dest)]
    run(cmd)
    return dur

def main(paths):
    with sync_playwright() as p:
        br = p.chromium.launch()
        for pth in paths:
            reel = json.loads(Path(pth).read_text(encoding="utf-8"))
            out = ROOT / "posts" / reel["slug"]; out.mkdir(parents=True, exist_ok=True)
            tmp = Path(tempfile.mkdtemp(prefix="reel_"))
            scenes = reel["scenes"]; n = len(scenes); clips, durs = [], []
            pg = br.new_page(viewport={"width": W, "height": H})
            for i, s in enumerate(scenes):
                pg.set_content(overlay_html(reel, s, i, n), wait_until="load"); pg.wait_for_timeout(120)
                ov = tmp / f"ov{i:02d}.png"; pg.screenshot(path=str(ov), omit_background=True)
                top = pg.evaluate("(()=>{const t=document.querySelector('.text');return t?t.getBoundingClientRect().top:0})()")
                if top < 330: print(f"  AVISO: cena {i+1} com texto alto demais (topo {int(top)}px) — reduzir texto")
                c = tmp / f"c{i:02d}.mp4"; durs.append(scene_clip(s, ov, c, i)); clips.append(c)
                print(f"  cena {i+1}/{n} · {durs[-1]:.1f}s · {s['media']}")
            pg.close()
            # fundido cruzado entre cenas
            fc, prev, off = [], "[0:v]", 0.0
            for i in range(1, n):
                off += durs[i - 1] - XF
                o = f"[v{i}]" if i < n - 1 else "[vout]"
                fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{o}"); prev = o
            total = sum(durs) - XF * (n - 1)
            vmap = "[vout]" if n > 1 else "[0:v]"
            cmd = ["ffmpeg", "-y"] + sum([["-i", str(c)] for c in clips], [])
            ai = n; afilters = []; amix = []
            if reel.get("music") and (ROOT / reel["music"]).exists():
                cmd += ["-stream_loop", "-1", "-i", str(ROOT / reel["music"])]
                afilters.append(f"[{ai}:a]atrim=0:{total:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=1,afade=t=out:st={max(0, total-2.5):.2f}:d=2.5,"
                                f"volume={reel.get('music_volume', 0.45)}[am]"); amix.append("[am]"); ai += 1
            if reel.get("voice") and (ROOT / reel["voice"]).exists():
                cmd += ["-i", str(ROOT / reel["voice"])]
                afilters.append(f"[{ai}:a]apad,atrim=0:{total:.2f},asetpts=PTS-STARTPTS[av]"); amix.append("[av]"); ai += 1
            if amix:
                afilters.append("".join(amix) + f"amix=inputs={len(amix)}:normalize=0[aout]" if len(amix) > 1 else f"{amix[0]}anull[aout]")
            else:
                cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=48000:cl=stereo"]
                afilters.append(f"[{ai}:a]anull[aout]")
            cmd += ["-filter_complex", ";".join(fc + afilters), "-map", vmap, "-map", "[aout]", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out / "reel.mp4")]
            run(cmd)
            # capa (frame 0,5 s) e prancha de conferência (um frame por cena)
            run(["ffmpeg", "-y", "-ss", "0.5", "-i", str(out / "reel.mp4"), "-frames:v", "1", "-q:v", "2", str(out / "reel_cover.jpg")])
            t, th = 0.0, []
            for i, d in enumerate(durs):
                f = tmp / f"th{i:02d}.jpg"
                run(["ffmpeg", "-y", "-ss", f"{t + d/2:.2f}", "-i", str(out / "reel.mp4"), "-frames:v", "1", "-q:v", "3", str(f)])
                th.append(Image.open(f).convert("RGB").resize((324, 576))); t += d - XF
            cols = min(4, n); rows = -(-n // cols)
            sheet = Image.new("RGB", (cols * 324 + (cols + 1) * 12, rows * 576 + (rows + 1) * 12), "#E5E5E5")
            for i, im in enumerate(th): sheet.paste(im, (12 + (i % cols) * 336, 12 + (i // cols) * 588))
            sheet.save(out / "_reel_prancha.jpg", quality=88)
            if reel.get("legenda"): (out / "reel_legenda.txt").write_text(reel["legenda"], encoding="utf-8")
            size = (out / "reel.mp4").stat().st_size / 1e6
            print(f"  posts/{reel['slug']}/reel.mp4 · {total:.1f}s · {size:.1f} MB")
            shutil.rmtree(tmp, ignore_errors=True)
        br.close()

if __name__ == "__main__":
    main(sys.argv[1:])
