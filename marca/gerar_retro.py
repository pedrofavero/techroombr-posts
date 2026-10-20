#!/usr/bin/env python3
"""Marca "Tech Room" em estilo retrô-corporativo (globos de meridianos, listras de velocidade,
emblema). Uso: python3 marca/gerar_retro.py → marca/_opcoes4.png
     python3 marca/gerar_retro.py final <A|B|C> → marca/final/
"""
import math, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = (ROOT / "engine/natgeo.html").read_text(encoding="utf-8").split("<style>", 1)[1].split("* { margin: 0;", 1)[0]

def globe(cx, cy, r, ink, sw=7, meridians=(-0.62, -0.3, 0, 0.3, 0.62), parallels=(-0.55, -0.2, 0.2, 0.55)):
    """Globo de arame: círculo, meridianos (elipses) e paralelos (linhas horizontais recortadas)."""
    s = f'<g fill="none" stroke="{ink}" stroke-width="{sw}" stroke-linecap="round"><circle cx="{cx}" cy="{cy}" r="{r}"/>'
    for m in meridians:
        rx = abs(m) * r
        if rx < 2: s += f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}"/>'
        else: s += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.1f}" ry="{r}"/>'
    for p in parallels:
        y = cy + p * r; half = math.sqrt(max(0, r * r - (p * r) ** 2))
        s += f'<line x1="{cx-half:.1f}" y1="{y:.1f}" x2="{cx+half:.1f}" y2="{y:.1f}"/>'
    return s + "</g>"

def wordmark(x, y, ink, size=74, sub="TECNOLOGIA EXPLICADA · BRASIL", anchor="middle", tm=True):
    s = (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Montserrat" font-weight="800" font-size="{size}" '
         f'letter-spacing="{size*0.06:.0f}" fill="{ink}" transform="translate({x},0) scale(1.12,1) translate({-x},0)">TECH ROOM'
         + (f'<tspan font-size="{size*0.3:.0f}" dy="{-size*0.5:.0f}" font-weight="700" letter-spacing="0">™</tspan>' if tm else "") + "</text>")
    if sub:
        s += (f'<text x="{x}" y="{y+size*0.62:.0f}" text-anchor="middle" font-family="Montserrat" font-weight="500" font-size="{size*0.22:.0f}" letter-spacing="{size*0.09:.0f}" fill="{ink}">{sub}</text>')
    return s

def tile(bg, ink, v, W=600):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 600 600"><rect width="600" height="600" fill="{bg}"/>'
    if v == "A":  # globo entrando numa sala: moldura com porta aberta, globo meio dentro + listras de velocidade
        s += globe(262, 215, 95, ink, 8)
        # listras saindo para a direita (velocidade), encurtando
        for i, (y, w) in enumerate(((150, 150), (176, 120), (202, 90), (228, 90), (254, 120), (280, 150))):
            s += f'<rect x="{372}" y="{y-6}" width="{w}" height="12" rx="6" fill="{ink}"/>'
        s += wordmark(300, 408, ink, 58)
    elif v == "B":  # emblema: sala (retângulo arredondado) com globo recortado atrás do nome
        s += f'<rect x="60" y="130" width="480" height="340" rx="28" fill="none" stroke="{ink}" stroke-width="10"/>'
        s += f'<clipPath id="c"><rect x="75" y="145" width="450" height="310" rx="18"/></clipPath>'
        s += f'<g clip-path="url(#c)">{globe(300, 300, 200, ink, 6, parallels=(-0.7,-0.45,-0.2,0.2,0.45,0.7))}</g>'
        # faixa do nome
        s += f'<rect x="60" y="262" width="480" height="78" fill="{bg}"/>'
        s += f'<text x="300" y="320" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="62" letter-spacing="5" fill="{ink}" transform="translate(300,0) scale(1.12,1) translate(-300,0)">TECH ROOM<tspan font-size="18" dy="-30" letter-spacing="0">™</tspan></text>'
        s += f'<text x="300" y="505" text-anchor="middle" font-family="Montserrat" font-weight="600" font-size="15" letter-spacing="6" fill="{ink}">TECNOLOGIA EXPLICADA · EST. 2026</text>'
    else:  # sol de listras com uma janela quadrada (a sala) no canto
        cx, cy, r = 300, 210, 120
        for i in range(-5, 6):
            y = cy + i * 22; half = math.sqrt(max(0, r * r - (i * 22) ** 2)); h = 14
            s += f'<rect x="{cx-half:.1f}" y="{y-h/2}" width="{2*half:.1f}" height="{h}" rx="{h/2}" fill="{ink}"/>'
        # janela: quadrado "vazado" sobre o sol, com um ponto
        s += f'<rect x="312" y="190" width="120" height="120" fill="{bg}"/><rect x="330" y="208" width="84" height="84" fill="none" stroke="{ink}" stroke-width="10"/>'
        s += wordmark(300, 420, ink, 58)
    return s + "</svg>"

def render(html, path, w, h):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h})
        pg.set_content(html, wait_until="load"); pg.wait_for_timeout(300); pg.screenshot(path=str(path)); b.close()

PAL = (("#1B2BCF", "#FFFFFF"), ("#F2F1EC", "#1B2BCF"), ("#0E0E0E", "#F4F2EC"))
if __name__ == "__main__":
    out = ROOT / "marca"
    if len(sys.argv) > 1 and sys.argv[1] == "final":
        v = sys.argv[2]; fin = out / "final"; fin.mkdir(exist_ok=True)
        for name, (bg, ink) in zip(("azul", "claro", "escuro"), PAL):
            svg = tile(bg, ink, v, 1080); (fin / f"techroom-{name}.svg").write_text(svg, encoding="utf-8")
            render(f"<html><head><style>{FONTS} body{{margin:0}}</style></head><body>{svg}</body></html>", fin / f"techroom-{name}-1080.png", 1080, 1080)
        print("ok", fin)
    else:
        html = f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS} body{{margin:0;background:#888;}} .g{{display:grid;grid-template-columns:repeat(3,600px);gap:12px;padding:12px;width:1860px}}</style></head><body><div class="g">'
        for bg, ink in PAL:
            for v in "ABC": html += tile(bg, ink, v)
        render(html + "</div></body></html>", out / "_opcoes4.png", 1860, 1860); print("ok")
