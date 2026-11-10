#!/usr/bin/env python3
"""
Conferência da narração em português — The Tech Room
Uso: python3 engine/asr_check_pt.py posts/<slug>/reel.json   (precisa de posts/<slug>/reel.mp4 e faster-whisper)

Transcreve o áudio final do reel (faster-whisper, pt) e compara com o roteiro ("say" das cenas).
Grava posts/<slug>/reel_asr.txt. Sai com código 1 se um NÚMERO do roteiro não foi ouvido (troca de número é o erro
que não pode ir ao ar); diferença só de palavras gera aviso. Adaptação para pt-BR da ideia de core/tts/asr_check.py
do lemo-opuscar (que só trata en/zh/ja/ko).
"""
import difflib, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UN = "zero um dois tres quatro cinco seis sete oito nove dez onze doze treze quatorze quinze dezesseis dezessete dezoito dezenove".split()
DEZ = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90}
CEM = {"cem": 100, "cento": 100, "duzentos": 200, "trezentos": 300, "quatrocentos": 400, "quinhentos": 500,
       "seiscentos": 600, "setecentos": 700, "oitocentos": 800, "novecentos": 900}
VAL = {**{w: i for i, w in enumerate(UN)}, **DEZ, **CEM, "uma": 1, "duas": 2, "catorze": 14}


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9,.% ]+", " ", t)


def numeros(t):
    """Conjunto de números do texto, como strings canônicas ('65.8', '196'). Lê dígitos e números por extenso até 999."""
    t = norm(t); out = []
    for m in re.finditer(r"\d+(?:[.,]\d+)?", t):
        s = m.group(0)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
            s = s.replace(".", "")
        out.append(str(float(s.replace(",", "."))).rstrip("0").rstrip("."))
    toks = re.sub(r"[,.%]", " ", t.replace("por cento", " ")).split(); i = 0

    def grupo(i):
        """Lê um número por extenso a partir de toks[i] (centena > dezena > unidade). Devolve (valor, próximo índice) ou (None, i)."""
        v, j, nivel = 0, i, 4
        while j < len(toks):
            w = toks[j]
            if w == "e" and j > i and j + 1 < len(toks) and toks[j + 1] in VAL:
                j += 1; continue
            if w not in VAL:
                break
            x = VAL[w]; n = 3 if x >= 100 else 2 if x >= 20 else 1
            if n >= nivel or (nivel == 2 and x >= 10):
                break
            v += x; nivel = n if x >= 20 else 0; j += 1
        if j > i and toks[j - 1] == "e":
            j -= 1
        return (v, j) if j > i else (None, i)

    while i < len(toks):
        if toks[i] in ("um", "uma") or toks[i] not in VAL:
            i += 1; continue
        v, j = grupo(i)
        if j < len(toks) - 1 and toks[j] == "virgula":
            f, k = grupo(j + 1)
            if f is not None:
                out.append(f"{v}.{f}".rstrip("0").rstrip(".") if f else str(v)); i = k; continue
        out.append(str(v)); i = j
    return out


def main(path):
    reel = json.loads(Path(path).read_text(encoding="utf-8"))
    d = ROOT / "posts" / reel["slug"]
    roteiro = " ".join(s["say"] for s in reel["scenes"] if s.get("say"))
    from faster_whisper import WhisperModel
    import os
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(d / "reel.mp4"), language="pt", beam_size=5)
    ouvido = " ".join(s.text.strip() for s in segs)
    a, b = re.sub(r"[,.%]", " ", norm(roteiro)).split(), re.sub(r"[,.%]", " ", norm(ouvido)).split()
    sim = difflib.SequenceMatcher(None, a, b).ratio()
    esperados, ouvidos = numeros(roteiro), numeros(ouvido)
    faltam = [n for n in dict.fromkeys(esperados) if n not in ouvidos and n != "1"]
    linhas = [f"semelhança roteiro x áudio: {sim:.1%}", f"números do roteiro: {', '.join(esperados) or '-'}",
              f"números ouvidos:    {', '.join(ouvidos) or '-'}",
              ("NÚMEROS NÃO OUVIDOS: " + ", ".join(faltam)) if faltam else "números: todos ouvidos",
              "", "ROTEIRO:", roteiro, "", "OUVIDO:", ouvido, ""]
    (d / "reel_asr.txt").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas[:4]))
    if sim < 0.85:
        print("AVISO: a transcrição difere bastante do roteiro; ouça o reel antes de publicar")
    raise SystemExit(1 if faltam else 0)


if __name__ == "__main__":
    main(sys.argv[1])
