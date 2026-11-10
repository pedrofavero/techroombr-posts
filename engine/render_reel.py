#!/usr/bin/env python3
"""
Renderizador de Reels — The Tech Room (v2: narração + legendas palavra a palavra)
Uso: python3 engine/render_reel.py posts/<slug>/reel.json [...]   [--fake-tts]
Saída: posts/<slug>/reel.mp4 (1080x1920, 30 fps, H.264 + AAC), reel_cover.jpg, reel_legenda.txt,
       reel_fontes.txt (1º comentário), reel_meta.json, _reel_prancha.jpg

REEL (reel.json):
  slug, [display "sans"|"serif"], [accent "#hex"], [masthead], [handle]
  [voice "pt-BR-FranciscaNeural" | "pt-BR-AntonioNeural" | "pt-BR-ThalitaMultilingualNeural"]  (edge-tts, gratuito)
  [voice_rate "+6%"]  [captions true]  [music "reels/musica/x.mp3"]  [music_volume 0.22]
  scenes[]  legenda  [fontes_comentario]  (texto do 1º comentário com as fontes)

CENA (scenes[]):
  media    fotos/<x>.jpg (Ken Burns) ou videos/<x>.mp4 (b-roll, cortado para 1080x1920). Opcional na cena "end".
  say      texto narrado pela voz. Define a duração da cena (áudio + hold). Sem "say", usa "dur".
  dur      duração em segundos quando não há narração (3 a 7; padrão 4)
  hold     respiro depois da narração, em segundos (padrão 0.35)
  kicker   rótulo pequeno em caixa alta (opcional)
  text     texto na tela (opcional); aceita **negrito** e ==destaque==. Com narração, fica no alto; a legenda fica embaixo.
  big      true = texto grande (gancho, virada, número)
  credit   "Vídeo: Nome / Pexels" ou "Foto: Nome / Unsplash" (pequeno no topo direito)
  align    "bottom" (padrão) ou "center" (só para cenas sem narração)
  end      true = cartão final: fundo escuro, title + lines[] (fontes) + handle. Sem media.

Regras de tela: zonas seguras do Instagram (topo 250 px e base 420 px sem texto). Legendas em Montserrat Bold,
palavra ativa na cor de destaque. Transição: fundido de 0,5 s. Música com ducking automático sob a voz.
--fake-tts: gera silêncio e tempos estimados (para testar sem internet). A voz real exige acesso a speech.platform.bing.com.
"""
import asyncio, json, re, shutil, subprocess, sys, tempfile
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "engine" / "fonts"
W, H, FPS, XF = 1080, 1920, 30, 0.5
FAKE = "--fake-tts" in sys.argv

_nat = (ROOT / "engine" / "natgeo.html").read_text(encoding="utf-8")
FONTS = _nat.split("<style>", 1)[1].split("* { margin: 0;", 1)[0]

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:transparent; }
.page { position:relative; width:1080px; height:1920px; font-family:"Lato",sans-serif; color:#fff;
        -webkit-font-smoothing:antialiased; --display:"Montserrat"; }
.page.serif { --display:"Playfair Display"; }
.scrim { position:absolute; inset:0;
  background: linear-gradient(to bottom, rgba(0,0,0,.55) 0%, rgba(0,0,0,.15) 30%, rgba(0,0,0,0) 45%),
              linear-gradient(to top, rgba(0,0,0,.88) 0%, rgba(0,0,0,.70) 28%, rgba(0,0,0,.25) 55%, rgba(0,0,0,0) 70%); }
.page.center .scrim { background: linear-gradient(to bottom, rgba(0,0,0,.55) 0%, rgba(0,0,0,.72) 50%, rgba(0,0,0,.88) 100%); }
.page.end .scrim { background:#0E1420; }
.masthead { position:absolute; top:270px; left:72px; font-family:"Montserrat"; font-weight:600; font-size:22px;
            letter-spacing:.32em; text-transform:uppercase; text-shadow:0 1px 8px rgba(0,0,0,.5); }
.credit { position:absolute; top:272px; right:72px; font-size:17px; letter-spacing:.06em; opacity:.8; }
.handle { position:absolute; left:72px; bottom:440px; font-size:20px; letter-spacing:.08em; opacity:.8; }
.bar { position:absolute; left:72px; right:72px; bottom:420px; height:4px; background:rgba(255,255,255,.22); border-radius:2px; }
.bar i { display:block; height:4px; background:var(--accent); border-radius:2px; }
.text { position:absolute; left:72px; right:120px; bottom:560px; }
.page.top .text { top:380px; bottom:auto; }
.page.center .text { top:50%; transform:translateY(-50%); bottom:auto; }
.kicker { font-family:"Montserrat"; font-weight:600; font-size:22px; letter-spacing:.3em; text-transform:uppercase;
          color:var(--accent); margin-bottom:26px; }
.big { font-family:var(--display); font-weight:800; font-size:74px; line-height:1.1; text-shadow:0 2px 18px rgba(0,0,0,.55); }
.page.sans .big { text-transform:uppercase; font-weight:700; font-size:64px; letter-spacing:.01em; }
.body { font-size:46px; line-height:1.36; text-shadow:0 1px 10px rgba(0,0,0,.55); }
.body b, .big b { font-weight:800; }
mark { background:none; color:var(--accent); }
.end .text { top:50%; transform:translateY(-50%); bottom:auto; right:72px; }
.end h3 { font-family:"Montserrat"; font-weight:600; font-size:24px; letter-spacing:.3em; text-transform:uppercase;
          color:var(--accent); margin-bottom:34px; }
.end .line { font-size:34px; line-height:1.4; padding:14px 0; border-top:1px solid rgba(255,255,255,.18); }
.end .line:last-child { border-bottom:1px solid rgba(255,255,255,.18); }
.end .follow { margin-top:44px; font-family:"Montserrat"; font-weight:700; font-size:40px; }
"""


def rich(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    return t.replace("\n", "<br>")


def overlay_html(reel, s, i, n):
    serif = reel.get("display", "sans") == "serif"
    has_say = bool(s.get("say")) and reel.get("captions", True)
    cls = ["page", "serif" if serif else "sans"]
    if s.get("end"):
        cls.append("end")
    elif s.get("align") == "center" and not has_say:
        cls.append("center")
    elif has_say:
        cls.append("top")
    kicker = f'<div class="kicker">{escape(s["kicker"])}</div>' if s.get("kicker") else ""
    if s.get("end"):
        lines = "".join(f'<div class="line">{rich(l)}</div>' for l in s.get("lines", []))
        body = (f'<h3>{escape(s.get("title", "Fontes"))}</h3>{lines}'
                f'<div class="follow">{escape(reel.get("handle", "@techroombr"))}</div>')
        kicker = ""
    elif s.get("text"):
        body = f'<div class="{"big" if s.get("big") else "body"}">{rich(s["text"])}</div>'
    else:
        body = ""
    credit = f'<div class="credit">{escape(s["credit"])}</div>' if s.get("credit") else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{CSS}</style></head><body>'
            f'<div class="{" ".join(cls)}" style="--accent:{reel.get("accent", "#F2B36B")}"><div class="scrim"></div>'
            f'<div class="masthead">{escape(reel.get("masthead", "The Tech Room"))}</div>{credit}'
            f'<div class="text">{kicker}{body}</div>'
            f'<div class="handle">{escape(reel.get("handle", "@techroombr"))}</div>'
            f'<div class="bar"><i style="width:{(i + 1) / n * 100:.1f}%"></i></div></div></body></html>')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); raise SystemExit(f"ffmpeg falhou: {' '.join(map(str, cmd[:8]))} …")


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


# ---------- voz ----------
def tts(text, voice, rate, dest):
    """Gera dest (mp3) e devolve lista de palavras [(inicio, fim, palavra)] em segundos."""
    if FAKE:
        words = text.split(); per = 0.40
        dur = 0.3 + per * len(words)
        run(["ffmpeg", "-y", "-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=24000:cl=mono", "-c:a", "libmp3lame", "-q:a", "6", str(dest)])
        return [(0.15 + i * per, 0.15 + (i + 1) * per - 0.05, w) for i, w in enumerate(words)]
    import edge_tts

    async def go():
        comm = edge_tts.Communicate(text, voice, rate=rate)
        words = []
        with open(dest, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
        return words
    return asyncio.run(go())


# ---------- legendas (ASS) ----------
def ass_color(hexcolor):
    h = hexcolor.lstrip("#"); r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}&".upper()


def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunk_words(words, max_words=3, max_chars=18):
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or sum(len(x[2]) for x in cur) + len(w[2]) > max_chars):
            chunks.append(cur); cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(all_words, accent, serif):
    """all_words: lista de (inicio, fim, palavra) já com offset global."""
    font = "Montserrat"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},62,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H80000000&,-1,0,0,0,100,100,0.5,0,1,5,2,2,90,90,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    acc = ass_color(accent)
    lines = []
    for chunk in chunk_words(all_words):
        for k, (st, en, w) in enumerate(chunk):
            nxt = chunk[k + 1][0] if k + 1 < len(chunk) else en + 0.18
            parts = []
            for j, (_, _, ww) in enumerate(chunk):
                txt = ww.upper()
                parts.append(f"{{\\c{acc}\\fscx106\\fscy106}}{txt}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}" if j == k else txt)
            lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(nxt)},Cap,,0,0,0,,{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


# ---------- cenas ----------
def scene_clip(s, ov, dest, idx, dur):
    frames = int(dur * FPS)
    if s.get("end") or not s.get("media"):
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-t", str(dur), "-i", f"color=c=#0E1420:s={W}x{H}:r={FPS}"]
        vf = "[0:v]setsar=1[v]"
    else:
        media = ROOT / s["media"]
        if not media.exists():
            raise SystemExit(f"mídia não existe: {media}")
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


def main(paths):
    paths = [p for p in paths if not p.startswith("--")]
    with sync_playwright() as p:
        br = p.chromium.launch()
        for pth in paths:
            reel = json.loads(Path(pth).read_text(encoding="utf-8"))
            out = ROOT / "posts" / reel["slug"]; out.mkdir(parents=True, exist_ok=True)
            tmp = Path(tempfile.mkdtemp(prefix="reel_"))
            scenes = reel["scenes"]; n = len(scenes)
            voice = reel.get("voice", "pt-BR-FranciscaNeural"); rate = reel.get("voice_rate", "+6%")
            accent = reel.get("accent", "#F2B36B"); serif = reel.get("display", "sans") == "serif"
            clips, durs, voices, words_all = [], [], [], []
            pg = br.new_page(viewport={"width": W, "height": H})
            for i, s in enumerate(scenes):
                # 1) voz da cena (define a duração)
                if s.get("say"):
                    a = tmp / f"say{i:02d}.mp3"
                    words = tts(s["say"], voice, rate, a)
                    adur = probe_dur(a)
                    dur = round(adur + float(s.get("hold", 0.35)), 2)
                    voices.append((a, adur)); words_all.append(words)
                else:
                    dur = float(s.get("dur", 4)); voices.append(None); words_all.append([])
                # 2) sobreposição (texto, masthead, barra)
                pg.set_content(overlay_html(reel, s, i, n), wait_until="load"); pg.wait_for_timeout(120)
                ov = tmp / f"ov{i:02d}.png"; pg.screenshot(path=str(ov), omit_background=True)
                box = pg.evaluate("(()=>{const t=document.querySelector('.text');if(!t)return null;const r=t.getBoundingClientRect();return [r.top,r.bottom]})()")
                if box and box[0] < 330:
                    print(f"  AVISO: cena {i+1} com texto alto demais (topo {int(box[0])}px) — reduzir texto")
                if box and s.get("say") and not s.get("end") and box[1] > 1180 and s.get("text"):
                    print(f"  AVISO: cena {i+1}: texto desce até {int(box[1])}px e pode encostar na legenda — encurte")
                # 3) clipe
                c = tmp / f"c{i:02d}.mp4"; scene_clip(s, ov, c, i, dur); clips.append(c); durs.append(dur)
                print(f"  cena {i+1}/{n} · {dur:.1f}s · {s.get('media', 'cartão final')}" + (f" · {len(words_all[-1])} palavras" if s.get('say') else ""))
            pg.close()

            # 4) linha do tempo global (início de cada cena considerando os fundidos)
            starts = []; t = 0.0
            for i, d in enumerate(durs):
                starts.append(t); t += d - (XF if i < n - 1 else 0)
            total = t

            # 5) legendas
            glob_words = []
            for i, ws in enumerate(words_all):
                for st, en, w in ws:
                    glob_words.append((starts[i] + st, starts[i] + en, w))
            ass = tmp / "legendas.ass"
            use_caps = bool(glob_words) and reel.get("captions", True)
            if use_caps:
                ass.write_text(build_ass(glob_words, accent, serif), encoding="utf-8")

            # 6) montagem: fundidos + legendas + áudio (voz com ducking na música)
            fc, prev = [], "[0:v]"
            for i in range(1, n):
                o = f"[v{i}]" if i < n - 1 else "[vx]"
                fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f}{o}"); prev = o
            vlast = "[vx]" if n > 1 else "[0:v]"
            if use_caps:
                fc.append(f"{vlast}subtitles='{ass.as_posix()}':fontsdir='{FONTS_DIR.as_posix()}'[vout]"); vlast = "[vout]"
            cmd = ["ffmpeg", "-y"] + sum([["-i", str(c)] for c in clips], [])
            ai = n; af = []; voice_lbls = []
            for i, v in enumerate(voices):
                if v:
                    cmd += ["-i", str(v[0])]
                    af.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(starts[i]*1000)}|{int(starts[i]*1000)}[s{i}]")
                    voice_lbls.append(f"[s{i}]"); ai += 1
            if len(voice_lbls) > 1:
                af.append("".join(voice_lbls) + f"amix=inputs={len(voice_lbls)}:normalize=0,apad,atrim=0:{total:.2f}[voz]")
            elif voice_lbls:
                af.append(f"{voice_lbls[0]}apad,atrim=0:{total:.2f}[voz]")
            music = reel.get("music")
            has_music = bool(music) and (ROOT / music).exists()
            if has_music:
                cmd += ["-stream_loop", "-1", "-i", str(ROOT / music)]
                af.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.2f},asetpts=PTS-STARTPTS,"
                          f"afade=t=in:d=1,afade=t=out:st={max(0, total-2.5):.2f}:d=2.5,volume={reel.get('music_volume', 0.22)}[mus]"); ai += 1
            if voice_lbls and has_music:
                af.append("[mus][voz]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[musd]")
                af.append("[musd][voz]amix=inputs=2:normalize=0[aout]")
            elif voice_lbls:
                af.append("[voz]anull[aout]")
            elif has_music:
                af.append("[mus]anull[aout]")
            else:
                cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=48000:cl=stereo"]
                af.append(f"[{ai}:a]anull[aout]")
            cmd += ["-filter_complex", ";".join(fc + af), "-map", vlast, "-map", "[aout]", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out / "reel.mp4")]
            run(cmd)

            # 7) capa, prancha, textos e metadados
            run(["ffmpeg", "-y", "-ss", "0.6", "-i", str(out / "reel.mp4"), "-frames:v", "1", "-q:v", "2", str(out / "reel_cover.jpg")])
            th = []
            for i, d in enumerate(durs):
                f = tmp / f"th{i:02d}.jpg"
                run(["ffmpeg", "-y", "-ss", f"{starts[i] + d/2:.2f}", "-i", str(out / "reel.mp4"), "-frames:v", "1", "-q:v", "3", str(f)])
                th.append(Image.open(f).convert("RGB").resize((324, 576)))
            cols = min(4, n); rows = -(-n // cols)
            sheet = Image.new("RGB", (cols * 324 + (cols + 1) * 12, rows * 576 + (rows + 1) * 12), "#E5E5E5")
            for i, im in enumerate(th):
                sheet.paste(im, (12 + (i % cols) * 336, 12 + (i // cols) * 588))
            sheet.save(out / "_reel_prancha.jpg", quality=88)
            if reel.get("legenda"):
                (out / "reel_legenda.txt").write_text(reel["legenda"].strip() + "\n", encoding="utf-8")
            if reel.get("fontes_comentario"):
                (out / "reel_fontes.txt").write_text(reel["fontes_comentario"].strip() + "\n", encoding="utf-8")
            meta = dict(slug=reel["slug"], total_s=round(total, 2), scenes=[dict(dur=d, start=round(st, 2)) for d, st in zip(durs, starts)],
                        words=len(glob_words), voice=voice if voices and any(voices) else None, fake_tts=FAKE)
            (out / "reel_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            size = (out / "reel.mp4").stat().st_size / 1e6
            print(f"  posts/{reel['slug']}/reel.mp4 · {total:.1f}s · {size:.1f} MB · {len(glob_words)} palavras legendadas" + (" · FAKE TTS" if FAKE else ""))
            shutil.rmtree(tmp, ignore_errors=True)
        br.close()


if __name__ == "__main__":
    main(sys.argv[1:])
