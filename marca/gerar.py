#!/usr/bin/env python3
"""Gera o wordmark geométrico "techroom" (letras construídas em SVG, sem fonte) e exporta
PNG/SVG. Uso: python3 marca/gerar.py            → marca/_opcoes3.png (prancha de opções)
             python3 marca/gerar.py final 2     → marca/final/*.svg|png da variante escolhida
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
nat = (ROOT / "engine/natgeo.html").read_text(encoding="utf-8")
FONTS = nat.split("<style>", 1)[1].split("* { margin: 0;", 1)[0]
SW = 36  # espessura do traço (x-height = 100)

# glifos: (paths, avanço). x-height 0..100, linha de base y=100, ascendente y=-48
G = {
    "t": (["M0,-48 V72 A28,28 0 0 0 28,100 H44", "M-22,2 H26"], 52),
    "e": (["M-50,50 H50", "M50,50 A50,50 0 1 0 36,86"], 100),
    "c": (["M38,14 A50,50 0 1 0 38,86"], 100),
    "h": (["M0,-48 V100", "M0,50 A50,50 0 0 1 100,50 V100"], 100),
    "r": (["M0,0 V100", "M0,50 A50,50 0 0 1 50,0 H56"], 62),
    "o": (["M0,0 A50,50 0 1 0 0,100 A50,50 0 1 0 0,0"], 100),
    "m": (["M0,0 V100", "M0,50 A50,50 0 0 1 100,50 V100", "M100,50 A50,50 0 0 1 200,50 V100"], 200),
}
CENTERED = {"e", "c", "o"}
RING = "M0,0 A50,50 0 1 0 0,100 A50,50 0 1 0 0,0"

def word(text, stroke, gap=32, oo="ring"):
    """oo: 'ring' (dois anéis entrelaçados), 'square' (duas salas quadradas) ou None."""
    out, x, i = [], 0, 0
    while i < len(text):
        if text[i:i + 2] == "oo" and oo:
            if oo == "ring":
                out.append(f'<g transform="translate({x+50},0)"><path d="{RING}"/></g>')
                out.append(f'<g transform="translate({x+50+72},0)"><path d="{RING}"/></g>')
                x += 100 + 72 + gap
            else:
                for k in (0, 100 + gap):
                    out.append(f'<rect x="{x+k}" y="0" width="100" height="100" rx="20"/>')
                x += 200 + 2 * gap
            i += 2; continue
        paths, adv = G[text[i]]
        off = 50 if text[i] in CENTERED else 0
        out.append(f'<g transform="translate({x+off},0)">' + "".join(f'<path d="{p}"/>' for p in paths) + "</g>")
        x += adv + gap; i += 1
    w = x - gap
    return (f'<g fill="none" stroke="{stroke}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(out) + "</g>"), w

def monogram(ink, bg, size=200, x=0, y=0):
    return (f'<g transform="translate({x},{y})"><rect width="{size}" height="{size}" rx="{size*0.22}" fill="{ink}"/>'
            f'<g fill="none" stroke="{bg}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round" '
            f'transform="translate({size*0.19},{size*0.33}) scale({size/420})">'
            f'<path d="M0,-48 V72 A28,28 0 0 0 28,100 H44"/><path d="M-22,2 H26"/>'
            f'<path d="M92,0 V100"/><path d="M92,50 A50,50 0 0 1 142,0 H148"/></g></g>')

def tile(bg, ink, v, W=600):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}"><rect width="{W}" height="{W}" fill="{bg}"/>'
    if v == "1":
        g, w = word("techroom", ink, oo="ring"); sc = 520 / w
        s += f'<g transform="translate(40,{300-80*sc}) scale({sc})">{g}</g>'
        s += f'<text x="300" y="{300+60*sc+56}" text-anchor="middle" font-family="Montserrat" font-weight="600" font-size="16" letter-spacing="7" fill="{ink}" opacity=".55">TECNOLOGIA EXPLICADA COM CLAREZA</text>'
    elif v == "2":
        g1, w1 = word("tech", ink, oo=None); g2, w2 = word("room", ink, oo="square"); sc = 440 / w2
        s += f'<g transform="translate({300-w1*sc/2},{300-150*sc-20}) scale({sc})">{g1}</g>'
        s += f'<g transform="translate({300-w2*sc/2},{300+10}) scale({sc})">{g2}</g>'
    else:
        s += monogram(ink, bg, 200, 200, 100)
        g, w = word("techroom", ink, oo=None); sc = 360 / w
        s += f'<g transform="translate(120,372) scale({sc})">{g}</g>'
    return s + "</svg>"

def render(html, path, w, h):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h})
        pg.set_content(html, wait_until="load"); pg.wait_for_timeout(300); pg.screenshot(path=str(path)); b.close()

if __name__ == "__main__":
    out = ROOT / "marca"
    if len(sys.argv) > 1 and sys.argv[1] == "final":
        v = sys.argv[2]; fin = out / "final"; fin.mkdir(exist_ok=True)
        for name, bg, ink in (("claro", "#F2F1EC", "#111111"), ("escuro", "#0E0E0E", "#F4F2EC")):
            svg = tile(bg, ink, v, 1080)
            (fin / f"techroom-{name}.svg").write_text(svg, encoding="utf-8")
            render(f"<html><head><style>{FONTS} body{{margin:0}}</style></head><body>{svg}</body></html>", fin / f"techroom-{name}-1080.png", 1080, 1080)
        print("ok", fin)
    else:
        html = f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS} body{{margin:0;background:#888;}} .g{{display:grid;grid-template-columns:repeat(3,600px);gap:12px;padding:12px;width:1860px}}</style></head><body><div class="g">'
        for bg, ink in (("#F2F1EC", "#111111"), ("#0E0E0E", "#F4F2EC")):
            for v in "123": html += tile(bg, ink, v)
        render(html + "</div></body></html>", out / "_opcoes3.png", 1860, 1248); print("ok")
