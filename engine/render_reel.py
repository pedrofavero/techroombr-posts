#!/usr/bin/env python3
"""
Renderizador de Reels — The Tech Room (v2: narração + legendas palavra a palavra)
Uso: python3 engine/render_reel.py posts/<slug>/reel.json [...]   [--fake-tts]
Saída: posts/<slug>/reel.mp4 (1080x1920, 30 fps, H.264 + AAC), reel_cover.jpg, reel_legenda.txt,
       reel_fontes.txt (1º comentário), reel_meta.json, _reel_prancha.jpg

REEL (reel.json):
  slug, [display "sans"|"serif"], [accent "#hex"], [masthead], [handle]
  [voice "pt-BR-FranciscaNeural" | "pt-BR-AntonioNeural" | "pt-BR-ThalitaMultilingualNeural"]  (edge-tts, gratuito)
  [voice_rate "+6%"]  [captions true]
  Som: por padrão SÓ a voz. Opcionais, desligados: [music "auto" | "reels/musica/x.mp3"] [music_volume] [sfx true]
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
  anim     cena de dados animada (contrato window.DUR / window.render(t) do toolbox lemo-opuscar), no lugar de "text":
             {"type":"number","value":65.8,"decimals":1,"prefix":"","unit":"%","label":"..."}
             {"type":"bars","bars":[{"name":"...","value":65.8,"label":"65,8%","other":false}],"note":"..."}
             {"type":"timeline","items":[{"when":"1991","what":"..."}]}
           "media" (foto) vira fundo desfocado e escurecido; sem media, fundo da marca. Só infográfico: nada de ilustração.

Voz: edge-tts (online). Se falhar, cai para Kokoro offline (pt-BR: pf_dora / pm_alex) quando KOKORO_DIR aponta para a pasta
com kokoro-v1.0.onnx e voices-v1.0.bin. Áudio final: toolbox/mux.sh (loudnorm em duas passagens, -14 LUFS) com ffmpeg 7+;
com ffmpeg mais antigo, loudnorm simples.

Regras de tela: zonas seguras do Instagram (topo 250 px e base 420 px sem texto). Legendas em Montserrat Bold,
palavra ativa na cor de destaque. Transição: fundido de 0,5 s. Música com ducking automático sob a voz.
--fake-tts: gera silêncio e tempos estimados (para testar sem internet). A voz real exige acesso a speech.platform.bing.com.
"""
import asyncio, json, math, os, re, shutil, subprocess, sys, tempfile
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import reel_styles  # noqa: E402
FONTS_DIR = ROOT / "engine" / "fonts"
W, H, FPS, XF = 1080, 1920, 30, 0.1   # XF curto: corte seco (gramática caption-news), não fundido
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
.page.flat .scrim { background:none; }
.page.flat .masthead, .page.flat .credit { text-shadow:none; }
.page.light { color:#1F1C18; } .page.light .bar { background:rgba(0,0,0,.16); }
.page.anim .scrim { background: linear-gradient(to bottom, rgba(0,0,0,.45) 0%, rgba(0,0,0,0) 22%); }
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
    if reel_styles.is_drawn(reel):   # estilos desenhados: a página do estilo traz o conteúdo; aqui só a moldura da marca
        stl = reel_styles.STYLES[reel["style"]]
        return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{CSS}</style></head><body>'
                f'<div class="page sans flat {"light" if stl["light"] else ""}" style="--accent:{reel.get("accent") or stl["accent"]}"><div class="scrim"></div>'
                f'<div class="masthead">{escape(reel.get("masthead", "The Tech Room"))}</div>'
                f'<div class="handle">{escape(reel.get("handle", "@techroombr"))}</div>'
                f'<div class="bar"><i style="width:{(i + 1) / n * 100:.1f}%"></i></div></div></body></html>')
    serif = reel.get("display", "sans") == "serif"
    has_say = bool(s.get("say")) and reel.get("captions", True)
    cls = ["page", "serif" if serif else "sans"]
    if s.get("end"):
        cls.append("end")
    elif s.get("align") == "center" and not has_say:
        cls.append("center")
    elif has_say:
        cls.append("top")
    if s.get("anim"):
        cls.append("anim")
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
    try:
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
        words = asyncio.run(go())
        if Path(dest).exists() and Path(dest).stat().st_size > 1000:
            if not words:   # versões novas do edge-tts só mandam limites de frase: estima por palavra
                words = estimate_words(text, probe_dur(dest))
            return words
        raise RuntimeError("edge-tts não devolveu áudio")
    except Exception as e:
        print(f"  voz: edge-tts falhou ({type(e).__name__}: {str(e)[:120]}); usando Kokoro offline")
        return tts_kokoro(text, voice, rate, dest)


def estimate_words(text, dur, lead=0.08):
    """Sem marcação de palavras: distribui a duração pelo tamanho de cada palavra."""
    ws = text.split()
    if not ws:
        return []
    weights = [len(re.sub(r"\W", "", w)) + 1.5 + (2.5 if w[-1] in ".!?:;" else 1.0 if w[-1] == "," else 0) for w in ws]
    unit = max(0.01, dur - lead - 0.1) / sum(weights)
    out, t = [], lead
    for w, k in zip(ws, weights):
        out.append((t, t + k * unit * 0.92, w)); t += k * unit
    return out


_KOKORO = None
def tts_kokoro(text, voice, rate, dest):
    global _KOKORO
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    d = Path(os.environ.get("KOKORO_DIR", ROOT / "toolbox" / "modelos"))
    if _KOKORO is None:
        _KOKORO = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
    kv = "pm_alex" if "Antonio" in voice else "pf_dora"
    try:
        speed = 1.0 + int(re.sub(r"[^\d+-]", "", rate or "0") or 0) / 100
    except ValueError:
        speed = 1.0
    a, sr = _KOKORO.create(text, voice=kv, speed=speed, lang="pt-br")
    nz = np.where(np.abs(a) > (np.abs(a).max() if len(a) else 0) * .02)[0]
    if len(nz):
        a = a[max(0, nz[0] - int(.03 * sr)): nz[-1] + int(.08 * sr)]
    wav = Path(dest).with_suffix(".wav"); sf.write(wav, a, sr)
    run(["ffmpeg", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-q:a", "3", str(dest)])
    return estimate_words(text, len(a) / sr, lead=0.03)


# ---------- legendas (ASS) ----------
def ass_color(hexcolor):
    h = hexcolor.lstrip("#"); r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}&".upper()


def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunk_words(words, max_words=3, max_chars=15):
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or sum(len(x[2]) for x in cur) + len(w[2]) > max_chars):
            chunks.append(cur); cur = []
        cur.append(w)
        if w[2][-1:] in ".!?:":   # fim de frase fecha o bloco (não mistura frases nem cenas)
            chunks.append(cur); cur = []
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
Style: Cap,{font},80,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H80000000&,-1,0,0,0,100,100,0.5,0,1,6,3,2,70,70,600,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    acc = ass_color(accent)
    lines = []
    chunks = chunk_words(all_words)
    for ci, chunk in enumerate(chunks):
        prox = chunks[ci + 1][0][0] if ci + 1 < len(chunks) else None   # início do bloco seguinte: nunca dois blocos na tela
        for k, (st, en, w) in enumerate(chunk):
            nxt = chunk[k + 1][0] if k + 1 < len(chunk) else (min(en + 0.18, prox) if prox is not None else en + 0.18)
            if nxt <= st:
                continue
            parts = []
            for j, (_, _, ww) in enumerate(chunk):
                txt = ww.upper()
                parts.append(f"{{\\c{acc}\\fscx106\\fscy106}}{txt}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}" if j == k else txt)
            slam = "{\\fscx122\\fscy122\\t(0,110,\\fscx100\\fscy100)}" if k == 0 else ""
            lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(nxt)},Cap,,0,0,0,,{slam}{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


# ---------- cenas animadas (contrato window.DUR / window.render(t), do toolbox lemo-opuscar) ----------
ANIM_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#0E1420; }
.bg { position:absolute; inset:-60px; background-size:cover; background-position:center; filter:blur(26px) brightness(.32) saturate(.8); }
.stage { position:absolute; left:72px; right:72px; top:520px; height:700px; font-family:"Lato",sans-serif; color:#fff;
         display:flex; flex-direction:column; justify-content:center; }
.num { font-family:"Montserrat"; font-weight:800; font-size:230px; line-height:1; color:var(--accent); letter-spacing:-.02em; white-space:nowrap; }
.num small { font-size:96px; font-weight:700; margin-left:10px; letter-spacing:0; }
.lab { margin-top:34px; font-size:44px; line-height:1.3; max-width:900px; }
.row { margin:0 0 44px; }
.row .n { font-family:"Montserrat"; font-weight:600; font-size:34px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:baseline; }
.row .n b { font-family:"Montserrat"; font-weight:800; font-size:46px; }
.track { height:34px; background:rgba(255,255,255,.12); border-radius:4px; overflow:hidden; }
.fill { height:100%; width:0; background:var(--accent); border-radius:4px; }
.row.other .fill { background:rgba(255,255,255,.55); } .row.other .n b { color:#fff; } .row .n b { color:var(--accent); }
.note { font-size:26px; line-height:1.35; opacity:.7; margin-top:6px; }
.it { display:flex; gap:34px; padding:22px 0; border-top:1px solid rgba(255,255,255,.18); opacity:0; }
.it .w { font-family:"Montserrat"; font-weight:800; font-size:50px; color:var(--accent); min-width:190px; }
.it .t { font-size:36px; line-height:1.32; }
.bg.hook { filter:blur(4px) brightness(.62) saturate(.85) contrast(1.05); inset:-20px; }
.hk { font-family:"Montserrat"; font-weight:700; font-size:30px; letter-spacing:.26em; text-transform:uppercase; margin-bottom:26px; }
.hb { display:inline-block; position:relative; font-family:"Montserrat"; font-weight:800; font-size:210px; line-height:1; color:#0E0E0C;
      padding:6px 30px 14px; letter-spacing:-.02em; transform-origin:left center; white-space:nowrap; align-self:flex-start; }
.hb i { position:absolute; inset:0; background:var(--accent); z-index:-1; transform-origin:left center; }
.hl { margin-top:34px; font-family:"Montserrat"; font-weight:800; font-size:74px; line-height:1.08; text-transform:uppercase;
      text-shadow:0 2px 18px rgba(0,0,0,.6); }
.src { margin-top:40px; align-self:flex-start; display:flex; font-family:"Montserrat"; font-size:24px; font-weight:700; letter-spacing:.06em; }
.src b { background:#fff; color:#0E0E0C; padding:8px 14px; } .src span { background:rgba(14,14,12,.82); padding:8px 16px; font-weight:600; }
"""
ANIM_JS = """
(() => {
const A = __ANIM__; window.DUR = __DUR__;
const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x)), ease = x => 1 - Math.pow(1 - clamp(x), 3);
const fmt = (v, d) => v.toFixed(d).replace('.', ',').replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.');
const st = document.querySelector('.stage');
if (A.type === 'number') {
  st.innerHTML = `<div class="num"><span id="v"></span><small>${A.unit || ''}</small></div><div class="lab" id="l">${A.label || ''}</div>`;
} else if (A.type === 'bars') {
  st.innerHTML = A.bars.map((b, i) => `<div class="row ${b.other ? 'other' : ''}"><div class="n"><span>${b.name}</span><b id="b${i}"></b></div><div class="track"><div class="fill" id="f${i}"></div></div></div>`).join('') + (A.note ? `<div class="note">${A.note}</div>` : '');
} else if (A.type === 'hook') {
  st.innerHTML = `<div class="hk">${A.kicker || ''}</div><div class="hb" id="hb"><i id="hbi"></i><span id="v">${A.big}</span></div><div class="hl" id="hl">${A.line || ''}</div>`;
} else if (A.type === 'timeline') {
  st.innerHTML = A.items.map((it, i) => `<div class="it" id="i${i}"><div class="w">${it.when}</div><div class="t">${it.what}</div></div>`).join('');
}
if (A.fonte) st.insertAdjacentHTML('beforeend', `<div class="src" id="src"><b>FONTE</b><span>${A.fonte}</span></div>`);
const back = x => { x = clamp(x); const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
window.render = t => {
  const src = document.getElementById('src');
  if (src) { const p = ease((t - 0.35) / 0.2); src.style.opacity = p; src.style.transform = `translateX(${(1 - p) * -60}px)`; }
  if (A.type === 'hook') {
    const p = clamp((t - 0.1) / 0.13);
    document.getElementById('hbi').style.transform = `scaleX(${ease((t - 0.1) / 0.12)})`;
    const hb = document.getElementById('hb'); hb.style.opacity = t >= 0.1 ? 1 : 0; hb.style.transform = `scale(${1.3 - 0.3 * back(p)})`;
    if (A.value != null) document.getElementById('v').textContent = (A.prefix || '') + fmt(A.value * ease((t - 0.1) / 0.45), A.decimals || 0) + (A.unit || '');
    const q = ease((t - 0.55) / 0.18), hl = document.getElementById('hl'); hl.style.opacity = q; hl.style.transform = `translateY(${(1 - q) * 14}px)`;
    document.querySelector('.hk').style.opacity = clamp(t / 0.1);
  } else if (A.type === 'number') {
    const p = ease((t - 0.2) / Math.min(1.3, window.DUR * 0.4));
    document.getElementById('v').textContent = (A.prefix || '') + fmt(A.value * p, A.decimals || 0);
    document.getElementById('l').style.opacity = clamp((t - 0.6) / 0.6);
  } else if (A.type === 'bars') {
    const max = Math.max(...A.bars.map(b => b.value)) || 1;
    A.bars.forEach((b, i) => {
      const p = ease((t - 0.25 - i * 0.45) / 1.1);
      document.getElementById('f' + i).style.width = (b.value / max * 100 * p) + '%';
      const el = document.getElementById('b' + i); el.textContent = b.label || ''; el.style.opacity = clamp((t - 0.6 - i * 0.45) / 0.4);
    });
  } else if (A.type === 'timeline') {
    const step = Math.min(1.6, (window.DUR * 0.75) / A.items.length);
    A.items.forEach((it, i) => {
      const p = ease((t - 0.2 - i * step) / 0.6), el = document.getElementById('i' + i);
      el.style.opacity = p; el.style.transform = `translateY(${(1 - p) * 26}px)`;
    });
  }
};
window.render(0);
})();
"""


def anim_clip(pg, reel, s, ov, dest, dur):
    """Renderiza a cena quadro a quadro: o navegador desenha window.render(t) e os JPEGs vão por pipe para o ffmpeg."""
    if reel_styles.is_drawn(reel):
        html = reel_styles.page(reel, s, dur)
        return _frames(pg, html, ov, dest, dur)
    bg = ""
    if s.get("media"):
        import base64
        m = ROOT / s["media"]
        bg = f'<div class="bg{" hook" if s["anim"].get("type") == "hook" else ""}" style="background-image:url(data:image/jpeg;base64,{base64.b64encode(m.read_bytes()).decode()})"></div>'
    js = ANIM_JS.replace("__ANIM__", json.dumps(s["anim"], ensure_ascii=False)).replace("__DUR__", str(dur))
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{ANIM_CSS}</style></head>'
            f'<body style="--accent:{reel.get("accent", "#F2B36B")}">{bg}<div class="stage"></div><script>{js}</script></body></html>')
    _frames(pg, html, ov, dest, dur)


def _frames(pg, html, ov, dest, dur):
    pg.set_content(html, wait_until="load"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
    frames = int(round(dur * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-i", str(ov), "-filter_complex", "[0:v][1:v]overlay=0:0,format=yuv420p[o]", "-map", "[o]",
                           "-t", str(dur), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-r", str(FPS), str(dest)],
                          stdin=subprocess.PIPE)
    for f in range(frames):
        pg.evaluate("t => window.render(t)", f / FPS)
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg falhou na cena animada")


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
            # nenhum plano parado: a cada ~2,5 s a mesma foto "corta" para outro enquadramento (punch-in) e segue em push lento
            nseg = max(1, round(dur / 2.5)); seg = frames / nseg
            Z = [1.00, 1.24, 1.10, 1.32]; CX = [0.50, 0.40, 0.60, 0.50]; CY = [0.50, 0.42, 0.56, 0.38]
            def nest(vals):
                e = vals[-1]
                for k in range(len(vals) - 2, -1, -1):
                    e = f"if(lt(on,{int((k + 1) * seg)}),{vals[k]},{e})"
                return e
            o = idx % 2
            z = nest([f"{Z[(k + o) % 4]}+0.05*(on-{int(k * seg)})/{seg:.1f}" for k in range(nseg)])
            cx = nest([str(CX[(k + o) % 4]) for k in range(nseg)]); cy = nest([str(CY[(k + o) % 4]) for k in range(nseg)])
            vf = (f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                  f"zoompan=z='{z}':d={frames}:x='(iw-iw/zoom)*({cx})':y='(ih-ih/zoom)*({cy})':s={W}x{H}:fps={FPS},"
                  f"eq=contrast=1.07:saturation=0.92:brightness=-0.02,setsar=1[v]")
            cmd = ["ffmpeg", "-y", "-i", str(media)]
    cmd += ["-i", str(ov), "-filter_complex", vf + ";[v][1:v]overlay=0:0,format=yuv420p[o]", "-map", "[o]",
            "-t", str(dur), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19", str(dest)]
    run(cmd)


def ffmpeg_major():
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    m = re.search(r"ffmpeg version n?(\d+)", r)
    return int(m.group(1)) if m else 0


def master(video, mix, dest):
    """Áudio final em -14 LUFS. Com ffmpeg 7+, usa toolbox/mux.sh (duas passagens + limitador); senão, loudnorm simples."""
    mux = ROOT / "toolbox" / "mux.sh"
    if mux.exists() and ffmpeg_major() >= 7 and not FAKE:
        r = subprocess.run(["sh", str(mux), str(video), str(mix), str(dest), str(FPS), "0"], capture_output=True, text=True,
                           env={**os.environ, "LEMO_COLOR": "bt709"})
        print("  " + "\n  ".join((r.stdout + r.stderr).strip().splitlines()[-6:]))
        if r.returncode == 0 and Path(dest).exists():
            return
        print("  mux.sh falhou; usando loudnorm simples")
    af = "anull" if FAKE else "loudnorm=I=-14:TP=-1.5:LRA=11"
    run(["ffmpeg", "-y", "-i", str(video), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af,
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(dest)])


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
            drawn = reel_styles.is_drawn(reel)
            if drawn:
                accent = reel_styles.STYLES[reel["style"]]["caps_color"]
                for k, sc in enumerate(scenes):
                    if not sc.get("anim") and not sc.get("end"):
                        raise SystemExit(f"cena {k+1}: no estilo '{reel['style']}' toda cena precisa de 'anim' (hook, write, corrige, draw, number, bars, timeline)")
            clips, durs, voices, words_all = [], [], [], []
            pg = br.new_page(viewport={"width": W, "height": H})
            for i, s in enumerate(scenes):
                # 1) voz da cena (define a duração)
                if s.get("say"):
                    a = tmp / f"say{i:02d}.mp3"
                    words = tts(s["say"], voice, rate, a)
                    adur = probe_dur(a)
                    dur = math.ceil((adur + float(s.get("hold", 0.25)) + XF) * 2) / 2   # cortes na grade de 0,5 s (120 BPM)
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
                c = tmp / f"c{i:02d}.mp4"
                if s.get("anim") or drawn:
                    anim_clip(pg, reel, s, ov, c, dur)
                else:
                    scene_clip(s, ov, c, i, dur)
                clips.append(c); durs.append(dur)
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
            # efeitos e trilha gerados em código (engine/reel_audio.py, com toolbox/sfx.py)
            events = []
            for i, sc in enumerate(scenes):
                a = sc.get("anim") or {}; t0 = starts[i]
                if drawn:
                    kind = reel_styles.STYLES[reel["style"]]["sfx"]
                    fim = max(1.2, min(durs[i] * 0.72, durs[i] - 0.9))
                    if a.get("type") == "hook":
                        events.append((t0 + 0.08, "thump"))
                    if a.get("type") == "number":
                        events.append((t0 + 0.2, "ticks", min(1.3, durs[i] * 0.4)))
                    elif a.get("type") == "bars":
                        events += [(t0 + 0.6 + k * 0.45, "pop") for k in range(len(a["bars"]))]
                    else:
                        events.append((t0 + 0.15, kind, fim - 0.15))
                    if a.get("type") == "corrige":
                        events.append((t0 + fim * 0.38, "whoosh"))
                elif a.get("type") == "hook":
                    events.append((t0 + 0.1, "hook"))
                elif a:
                    events.append((t0, "whoosh"))
                    if a.get("type") == "number":
                        events.append((t0 + 0.2, "ticks", min(1.3, durs[i] * 0.4)))
                    elif a.get("type") == "bars":
                        events += [(t0 + 0.6 + k * 0.45, "pop") for k in range(len(a["bars"]))]
                    elif a.get("type") == "timeline":
                        step = min(1.6, durs[i] * 0.75 / len(a["items"]))
                        events += [(t0 + 0.2 + k * step, "pop") for k in range(len(a["items"]))]
                elif i > 0:
                    events.append((t0, "thump" if sc.get("big") else "cut"))
            music = reel.get("music")   # padrão: sem trilha (decisão editorial de 10/11/2026: só a voz da narradora)
            sfx_wav, mus_wav = tmp / "sfx.wav", tmp / "music.wav"
            try:
                if not (reel.get("sfx", False) or music == "auto"):
                    raise RuntimeError("desligado")
                import reel_audio
                reel_audio.build(total, events if reel.get("sfx", False) else [], str(mus_wav), str(sfx_wav), music_on=(music == "auto"))
            except Exception as e:
                if str(e) != "desligado":
                    print(f"  som procedural indisponível ({type(e).__name__}: {e})")
                music = None if music == "auto" else music
            if music == "auto" and mus_wav.exists():
                music_path = mus_wav
            else:
                music_path = (ROOT / music) if music and music != "auto" else None
            has_music = bool(music_path) and Path(music_path).exists()
            if has_music:
                cmd += ["-stream_loop", "-1", "-i", str(music_path)]
                af.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.2f},asetpts=PTS-STARTPTS,"
                          f"afade=t=in:d=1,afade=t=out:st={max(0, total-2.5):.2f}:d=2.5,volume={reel.get('music_volume', 0.5 if music == 'auto' else 0.22)}[mus]"); ai += 1
            if voice_lbls and has_music:
                af.append("[voz]asplit=2[voza][vozk]")
                af.append("[mus][vozk]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[musd]")
                af.append("[musd][voza]amix=inputs=2:normalize=0[aout]")
            elif voice_lbls:
                af.append("[voz]anull[aout]")
            elif has_music:
                af.append("[mus]anull[aout]")
            else:
                cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=48000:cl=stereo"]
                af.append(f"[{ai}:a]anull[aout]")
            if sfx_wav.exists():
                cmd += ["-i", str(sfx_wav)]
                af.append(f"[aout][{ai}:a]amix=inputs=2:normalize=0[aout2]"); ai += 1; aout = "[aout2]"
            else:
                aout = "[aout]"
            pre, mix = tmp / "pre.mp4", tmp / "mix.wav"
            cmd += ["-filter_complex", ";".join(fc + af),
                    "-map", vlast, "-t", f"{total:.2f}", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), str(pre),
                    "-map", aout, "-t", f"{total:.2f}", "-c:a", "pcm_s16le", "-ar", "48000", str(mix)]
            run(cmd)
            master(pre, mix, out / "reel.mp4")

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
