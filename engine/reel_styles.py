#!/usr/bin/env python3
"""
Estilos desenhados dos reels — The Tech Room
Páginas HTML no contrato window.DUR / window.render(t) (toolbox lemo-opuscar), 1080x1920, uma por cena.
Gramática inspirada nos STYLE.md de chalkboard, whiteboard/one-line, blueprint e watercolor; nenhum desenho,
personagem ou layout copiado. Tudo é traço e texto que "se escrevem" na tela: sem foto.

ESTILOS (campo "style" do reel.json)
  lousa      quadro-negro verde, giz branco e um giz amarelo        → EXPLICA, COMO FUNCIONA
  caderno    papel creme, traço a nanquim e lápis vermelho           → CURIOSIDADE, CONVERSA, ESTANTE
  planta     cianotipia azul, linha técnica branca, grade            → COMO FUNCIONA (máquinas, redes, chips)
  aquarela   papel de algodão, manchas translúcidas e pincel seco    → HISTÓRIA, ESTANTE
  (sem "style" ou "foto": o formato com fotografia, em render_reel.py)

CENAS (campo "anim" de cada cena; "kicker" opcional vai escrito à mão no alto)
  {"type":"hook","big":"...","line":"..."}                  afirmação gigante sublinhada + frase
  {"type":"write","title":"...","lines":["...","..."]}       texto que se escreve palavra a palavra (==destaque==)
  {"type":"corrige","errado":"...","certo":"..."}            escreve o mito, apaga com um passe, escreve o fato
  {"type":"draw","svg":"<svg viewBox=...>","caption":"..."}  desenho de linha que se traça na ordem do SVG
        SVG: só path/line/polyline/polygon/rect/circle/ellipse/text; sem cor (herda o traço do estilo);
        class="acc" = cor de destaque; class="wash" = mancha preenchida (aquarela/caderno); textos curtos, longe dos traços.
  {"type":"number",...} {"type":"bars",...} {"type":"timeline",...}   como no formato foto, no traço do estilo
  cena "end": cartão de fontes no próprio estilo
"""
import base64, json, re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HAND = ROOT / "engine" / "fonts" / "hand"

STYLES = {
    "lousa":    dict(light=False, hand="Caveat Brush", bg="#1F2D28", ink="#F3F0E6", accent="#FFD23F", mute="rgba(243,240,230,.62)",
                     sw=8, rough=5, grain=True, sfx="scratch", caps_color="#FFD23F"),
    "caderno":  dict(light=True, hand="Caveat", bg="#F3EEE2", ink="#1F1C18", accent="#D7381E", mute="rgba(31,28,24,.6)",
                     sw=5, rough=3.2, grain=False, sfx="pencil", caps_color="#FFC21A"),
    "planta":   dict(light=False, hand="Architects Daughter", bg="#0F3A6B", ink="#EAF2FF", accent="#FFC21A", mute="rgba(234,242,255,.62)",
                     sw=3.5, rough=1.2, grain=False, sfx="pencil", caps_color="#FFC21A"),
    "aquarela": dict(light=True, hand="Patrick Hand", bg="#F6F1E7", ink="#2B2622", accent="#C2452D", mute="rgba(43,38,34,.6)",
                     sw=6, rough=6, grain=False, sfx="brush", caps_color="#FFC21A"),
}
DRAWN = set(STYLES)


def is_drawn(reel):
    return reel.get("style") in DRAWN


def _font_css():
    out = []
    for fam, file, w in [("Caveat Brush", "caveat-brush-latin-400-normal.woff2", 400), ("Caveat", "caveat-latin-700-normal.woff2", 700),
                         ("Architects Daughter", "architects-daughter-latin-400-normal.woff2", 400),
                         ("Patrick Hand", "patrick-hand-latin-400-normal.woff2", 400)]:
        b = base64.b64encode((HAND / file).read_bytes()).decode()
        out.append(f'@font-face{{font-family:"{fam}";font-weight:{w};src:url(data:font/woff2;base64,{b}) format("woff2");}}')
    return "".join(out)


def rich(t):
    t = escape(str(t))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)


def words(t, cls=""):
    """Cada palavra num span para escrever uma a uma; ==x== vira destaque."""
    out = []
    for part in re.split(r"(==.+?==)", str(t)):
        acc = part.startswith("==") and part.endswith("==")
        for w in (part[2:-2] if acc else part).split():
            out.append(f'<span class="w{" acc" if acc else ""} {cls}">{escape(w)}</span>')
    return " ".join(out)


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
body { color:var(--ink); font-family:var(--hand), "Caveat", cursive; }
.tex { position:absolute; inset:0; pointer-events:none; }
.stage { position:absolute; left:72px; right:72px; top:400px; height:840px; display:flex; flex-direction:column; justify-content:center; }
.kick { position:absolute; left:72px; top:330px; font-size:56px; color:var(--accent); letter-spacing:.02em; }
.inked { filter:url(#rough); }
.w { display:inline-block; opacity:0; } .w.acc, mark { color:var(--accent); background:none; }
.big { font-size:210px; line-height:.94; } .big.s { font-size:150px; }
.und { height:26px; margin:6px 0 26px; }
.line { font-size:96px; line-height:1.08; margin-top:6px; }
.title { font-size:120px; line-height:1.02; margin-bottom:34px; color:var(--accent); }
.li { font-size:84px; line-height:1.12; margin-bottom:26px; }
.wrong { font-size:104px; line-height:1.06; position:relative; }
.right { font-size:124px; line-height:1.04; color:var(--accent); margin-top:44px; }
.strike { position:absolute; left:-10px; right:-10px; top:0; bottom:0; }
.cap { font-size:68px; line-height:1.12; margin-top:22px; color:var(--mute); }
.draw svg { width:100%; height:auto; max-height:700px; overflow:visible; }
.draw svg * { fill:none; stroke:var(--ink); stroke-width:var(--sw); stroke-linecap:round; stroke-linejoin:round; }
.draw svg .acc { stroke:var(--accent); }
.draw svg .wash { stroke:none; fill:var(--accent); fill-opacity:0; }
.draw svg .wash.ink { fill:var(--ink); }
.draw svg text { stroke:none; fill:var(--ink); font-family:var(--hand); font-size:42px; }
.draw svg text.acc { fill:var(--accent); stroke:none; }
.num { font-size:300px; line-height:.9; color:var(--accent); white-space:nowrap; } .num small { font-size:130px; margin-left:8px; }
.lab { margin-top:26px; font-size:64px; line-height:1.1; }
.row { margin:0 0 46px; } .row .n { font-size:56px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:baseline; }
.row .n b { font-size:72px; font-weight:400; color:var(--accent); } .row.other .n b { color:var(--ink); }
.track { height:44px; border:var(--sw) solid var(--ink); border-radius:6px; overflow:hidden; }
.fill { height:100%; width:0; background:var(--accent); } .row.other .fill { background:var(--ink); opacity:.55; }
.note { font-size:40px; line-height:1.15; color:var(--mute); }
.it { display:flex; gap:30px; padding:24px 0; opacity:0; } .it .wh { font-size:104px; color:var(--accent); min-width:250px; line-height:1; } .it .t { font-size:66px; line-height:1.1; }
.src { margin-top:36px; font-size:50px; color:var(--mute); opacity:0; } .src b { color:var(--ink); font-weight:400; text-decoration:underline; }
.endl { font-size:60px; line-height:1.15; margin-bottom:22px; } .follow { font-size:84px; color:var(--accent); margin-top:30px; }
body.lousa .tex { background:
   radial-gradient(900px 500px at 20% 30%, rgba(255,255,255,.055), transparent 70%),
   radial-gradient(700px 700px at 85% 75%, rgba(255,255,255,.04), transparent 70%),
   radial-gradient(1400px 1900px at 50% 50%, transparent 55%, rgba(0,0,0,.38) 100%); }
body.caderno .tex { background: radial-gradient(circle, rgba(31,28,24,.16) 1.6px, transparent 2px) 0 0 / 54px 54px,
   radial-gradient(1400px 1900px at 50% 50%, transparent 60%, rgba(120,96,60,.16) 100%); }
body.planta .tex { background:
   repeating-linear-gradient(0deg, rgba(255,255,255,.10) 0 2px, transparent 2px 270px),
   repeating-linear-gradient(90deg, rgba(255,255,255,.10) 0 2px, transparent 2px 270px),
   repeating-linear-gradient(0deg, rgba(255,255,255,.045) 0 1px, transparent 1px 54px),
   repeating-linear-gradient(90deg, rgba(255,255,255,.045) 0 1px, transparent 1px 54px),
   radial-gradient(1400px 1900px at 50% 50%, transparent 55%, rgba(0,10,40,.45) 100%); }
body.aquarela .tex { background:
   radial-gradient(620px 520px at 12% 22%, rgba(194,69,45,.16), transparent 68%),
   radial-gradient(700px 600px at 92% 70%, rgba(54,110,140,.15), transparent 70%),
   radial-gradient(500px 420px at 30% 92%, rgba(214,160,60,.14), transparent 70%); }
body.aquarela .draw svg .wash { filter:url(#bleed); }
body.planta .big, body.planta .title { text-transform:uppercase; letter-spacing:.02em; }
body.planta .big { font-size:136px; } body.planta .big.s { font-size:108px; } body.planta .line, body.planta .li { font-size:66px; } body.planta .wrong { font-size:76px; } body.planta .right { font-size:86px; } body.planta .title { font-size:88px; } body.planta .it .wh { font-size:80px; } body.planta .it .t { font-size:52px; } body.planta .cap { font-size:52px; }
body.aquarela .big { font-size:170px; } body.aquarela .big.s { font-size:128px; } body.aquarela .line, body.aquarela .li { font-size:76px; } body.aquarela .wrong { font-size:88px; } body.aquarela .right { font-size:104px; } body.aquarela .it .t { font-size:56px; }
"""

JS = r"""
(() => {
const A = __ANIM__, ST = __STYLE__; window.DUR = __DUR__;
const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x)), ease = x => 1 - Math.pow(1 - clamp(x), 3);
const fmt = (v, d) => v.toFixed(d).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const D = window.DUR, END = Math.max(1.2, Math.min(D * 0.72, D - 0.9));   // tudo desenhado até aqui; o resto é leitura

// escreve as palavras de um conjunto entre t0 e t1 (cada palavra entra da esquerda, como traço)
function writer(els, t0, t1) {
  const L = els.map(e => e.textContent.length + 2), tot = L.reduce((a, b) => a + b, 0) || 1;
  let acc = 0; const plan = els.map((e, i) => { const a = t0 + (t1 - t0) * acc / tot; acc += L[i]; return [e, a, t0 + (t1 - t0) * acc / tot]; });
  return t => plan.forEach(([e, a, b]) => { const p = clamp((t - a) / Math.max(0.05, b - a)); e.style.opacity = p > 0 ? 1 : 0; e.style.clipPath = p >= 1 ? 'none' : `inset(-20% ${(1 - p) * 100}% -20% -10%)`; });
}
// traça os elementos de um SVG em sequência
function drawer(svg, t0, t1) {
  const els = [...svg.querySelectorAll('path,line,polyline,polygon,rect,circle,ellipse,text')];
  const items = els.map(e => {
    const isText = e.tagName === 'text', wash = e.classList.contains('wash');
    let len = 60; if (!isText) { try { len = e.getTotalLength(); } catch (x) { len = 100; } }
    if (!isText && !wash) { e.style.strokeDasharray = len; e.style.strokeDashoffset = len; }
    if (isText) e.style.opacity = 0;
    return { e, isText, wash, cost: isText ? 140 : wash ? 260 : Math.max(120, len) };
  });
  const tot = items.reduce((a, b) => a + b.cost, 0) || 1; let acc = 0;
  items.forEach(it => { it.a = t0 + (t1 - t0) * acc / tot; acc += it.cost; it.b = t0 + (t1 - t0) * acc / tot; });
  return t => items.forEach(it => {
    const p = clamp((t - it.a) / Math.max(0.05, it.b - it.a));
    if (it.isText) it.e.style.opacity = p;
    else if (it.wash) it.e.style.fillOpacity = 0.42 * ease(p);
    else it.e.style.strokeDashoffset = (1 - p) * parseFloat(it.e.style.strokeDasharray);
  });
}
const UND = `<svg class="und inked" viewBox="0 0 900 26" preserveAspectRatio="none"><path id="u" d="M4 14 C 160 4, 330 22, 520 11 S 800 6, 896 15" fill="none" stroke="var(--accent)" stroke-width="var(--sw)" stroke-linecap="round"/></svg>`;
const st = $('.stage'); let steps = [];
if (A.kicker) { $('.kick').innerHTML = WORDS(A.kicker); steps.push(writer($$('.kick .w'), 0.05, 0.5)); }

if (A.type === 'hook') {
  st.innerHTML = `<div class="big ${String(A.big).length > 11 ? 's' : ''} inked">${WORDS(A.big)}</div>${UND}<div class="line inked">${WORDS(A.line || '')}</div>`;
  steps.push(writer($$('.big .w'), 0.08, Math.min(0.9, D * 0.25)));
  const u = $('#u'), ul = u.getTotalLength(); u.style.strokeDasharray = ul;
  steps.push(t => u.style.strokeDashoffset = (1 - ease((t - Math.min(0.9, D * 0.25)) / 0.3)) * ul);
  steps.push(writer($$('.line .w'), Math.min(1.25, D * 0.35), END));
} else if (A.type === 'write' || A.type === 'end') {
  const lines = A.lines || [];
  st.innerHTML = (A.title ? `<div class="title inked">${WORDS(A.title)}</div>` : '') +
    lines.map(l => `<div class="${A.type === 'end' ? 'endl' : 'li'} inked">${WORDS(l)}</div>`).join('') +
    (A.type === 'end' ? `<div class="follow inked">${WORDS(A.handle || '@techroombr')}</div>` : '');
  steps.push(writer($$('.stage .w'), 0.15, A.type === 'end' ? Math.min(1.6, D * 0.7) : END));
} else if (A.type === 'corrige') {
  st.innerHTML = `<div class="wrong inked" id="wr">${WORDS(A.errado)}<svg class="strike" viewBox="0 0 900 200" preserveAspectRatio="none"><path id="sk" d="M0 110 C 220 80, 420 140, 640 96 S 860 120, 900 92" fill="none" stroke="var(--accent)" stroke-width="var(--sw)" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg></div><div class="right inked">${WORDS(A.certo)}</div>`;
  const a = END * 0.38, b = END * 0.52;
  steps.push(writer($$('#wr .w'), 0.15, a));
  const sk = $('#sk'), sl = sk.getTotalLength(); sk.style.strokeDasharray = sl;
  steps.push(t => { sk.style.strokeDashoffset = (1 - ease((t - a) / (b - a))) * sl; $('#wr').style.opacity = 1 - 0.62 * ease((t - b + 0.05) / 0.3); });
  steps.push(writer($$('.right .w'), b + 0.1, END));
} else if (A.type === 'draw') {
  st.innerHTML = `<div class="draw inked">${A.svg}</div>` + (A.caption ? `<div class="cap inked">${WORDS(A.caption)}</div>` : '');
  steps.push(drawer($('.draw svg'), 0.15, END * 0.86));
  if (A.caption) steps.push(writer($$('.cap .w'), END * 0.7, END));
} else if (A.type === 'number') {
  st.innerHTML = `<div class="num inked"><span id="v"></span><small>${A.unit || ''}</small></div>${UND}<div class="lab inked">${WORDS(A.label || '')}</div>`;
  const u = $('#u'), ul = u.getTotalLength(); u.style.strokeDasharray = ul; const T = Math.min(1.3, D * 0.4);
  steps.push(t => { $('#v').textContent = (A.prefix || '') + fmt(A.value * ease((t - 0.2) / T), A.decimals || 0); u.style.strokeDashoffset = (1 - ease((t - 0.2 - T) / 0.3)) * ul; });
  steps.push(writer($$('.lab .w'), 0.3 + T, Math.max(0.6 + T, END)));
} else if (A.type === 'bars') {
  st.innerHTML = A.bars.map((b, i) => `<div class="row ${b.other ? 'other' : ''}"><div class="n inked"><span>${b.name}</span><b id="b${i}"></b></div><div class="track inked"><div class="fill" id="f${i}"></div></div></div>`).join('') + (A.note ? `<div class="note inked">${A.note}</div>` : '');
  const max = Math.max(...A.bars.map(b => b.value)) || 1;
  steps.push(t => A.bars.forEach((b, i) => { const p = ease((t - 0.25 - i * 0.45) / 1.1); $('#f' + i).style.width = (b.value / max * 100 * p) + '%'; const el = $('#b' + i); el.textContent = b.label || ''; el.style.opacity = clamp((t - 0.6 - i * 0.45) / 0.4); }));
} else if (A.type === 'timeline') {
  st.innerHTML = A.items.map((it, i) => `<div class="it inked" id="i${i}"><div class="wh">${it.when}</div><div class="t">${it.what}</div></div>`).join('');
  const step = Math.min(1.6, (D * 0.75) / A.items.length);
  steps.push(t => A.items.forEach((it, i) => { const p = ease((t - 0.2 - i * step) / 0.6), el = $('#i' + i); el.style.opacity = p; el.style.clipPath = `inset(0 ${(1 - p) * 100}% 0 0)`; }));
}
if (A.fonte) { st.insertAdjacentHTML('beforeend', `<div class="src inked">fonte: <b>${A.fonte}</b></div>`); steps.push(t => $('.src').style.opacity = ease((t - 0.5) / 0.4)); }
const turb = document.getElementById('turb');
window.render = t => {
  if (turb && ST.rough > 2) turb.setAttribute('seed', 3 + (Math.floor(t * 6) % 3));   // "fervura" leve do traço feito à mão
  steps.forEach(f => f(t));
};
window.render(0);
})();
"""


def page(reel, scene, dur):
    st = STYLES[reel["style"]]
    a = dict(scene.get("anim") or {})
    if scene.get("end"):
        a = {"type": "end", "title": scene.get("title", "Fontes"), "lines": scene.get("lines", []), "handle": reel.get("handle", "@techroombr")}
    if scene.get("kicker") and "kicker" not in a:
        a["kicker"] = scene["kicker"]
    accent = reel.get("accent") or st["accent"]
    # as palavras são quebradas em spans no Python (função words) e injetadas pelo marcador WORDS(...) do JS
    js = JS.replace("__ANIM__", json.dumps(a, ensure_ascii=False)).replace("__STYLE__", json.dumps({"rough": st["rough"]})).replace("__DUR__", str(dur))
    WORDS = ("const WORDS = t => String(t).split(/(==.+?==)/).map(p => { const acc = /^==.*==$/.test(p); "
             "return (acc ? p.slice(2, -2) : p).split(/\\s+/).filter(Boolean).map(w => "
             "`<span class=\"w${acc ? ' acc' : ''}\">${w.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</span>`).join(' '); }).join(' ');\n")
    js = js.replace("(() => {\n", "(() => {\n" + WORDS, 1)
    grain = ('<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="1" seed="9" result="g"/>'
             '<feColorMatrix in="g" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -2.6 1.85" result="gm"/>'
             '<feComposite in="d" in2="gm" operator="in"/>') if st["grain"] else ""
    defs = (f'<svg width="0" height="0" style="position:absolute"><defs>'
            f'<filter id="rough" x="-5%" y="-20%" width="110%" height="140%"><feTurbulence id="turb" type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{st["rough"]}" result="d"/>{grain}</filter>'
            f'<filter id="bleed" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="5" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="38"/><feGaussianBlur stdDeviation="2.2"/></filter>'
            f'<filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="2"/><feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.09 0"/></filter>'
            f'</defs></svg>')
    noise = '<svg class="tex" width="1080" height="1920"><rect width="1080" height="1920" filter="url(#paper)"/></svg>'
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{_font_css()}{CSS}</style></head>'
            f'<body class="{reel["style"]}" style="--bg:{st["bg"]};--ink:{st["ink"]};--accent:{accent};--mute:{st["mute"]};--sw:{st["sw"]}px;--hand:\'{st["hand"]}\'">'
            f'{defs}<div class="tex"></div>{noise}<div class="kick inked"></div><div class="stage"></div><script>{js}</script></body></html>')
