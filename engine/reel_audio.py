#!/usr/bin/env python3
"""
Som do reel — The Tech Room: trilha procedural (120 BPM) e efeitos, tudo gerado em código, sem arquivo de terceiros.
Efeitos vêm de toolbox/sfx.py (lemo-opuscar, MIT): whoosh, thump, click, pop. A trilha é uma base discreta em lá menor
(bumbo suave, chimbal no contratempo, baixo em colcheias, ostinato de marimba) pensada para ficar SOB a voz.

  build(total_s, events, out_music, out_sfx, music=True)
  events: lista de (tempo_s, tipo[, duração]) com tipo em hook | whoosh | thump | pop | ticks | cut
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "toolbox"))
import sfx as S   # noqa: E402

SR = S.SR
BPM = 120
BEAT = 60 / BPM


def _note(freq, d, tau=0.18, harm=((1, 1.0), (4, 0.25), (10, 0.06))):
    """Barra de marimba: fundamental + parciais inarmônicos com decaimento rápido."""
    t = S.t_(d)
    x = sum(a * np.sin(2 * np.pi * freq * h * t) * np.exp(-t / (tau / (1 + 0.6 * i))) for i, (h, a) in enumerate(harm))
    return x * np.minimum(1, t / 0.003) * np.minimum(1, (d - t) / 0.03)


def _bass(freq, d):
    t = S.t_(d)
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) + 0.12 * np.sin(2 * np.pi * 3 * freq * t)
    return x * np.exp(-t / 0.22) * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.02)


def _kick():
    d = 0.22; t = S.t_(d)
    f = 48 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)


def _hat():
    d = 0.05
    return S.hp(S.noise(d), 7000) * S.env_exp(d, 0.012)


def _hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(total):
    n = int(total * SR) + SR
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)

    def put(x, at, g=1.0, pan=0.0):
        i = int(at * SR)
        if i >= n:
            return
        x = x[: n - i] * g
        L[i:i + len(x)] += x * (1 - max(0, pan)); R[i:i + len(x)] += x * (1 + min(0, pan))

    prog = [45, 41, 48, 43]                 # Am  F  C  G (baixo, MIDI)
    arp = [[69, 72, 76, 72], [65, 69, 72, 69], [67, 72, 76, 72], [67, 71, 74, 71]]
    bars = int(total / (4 * BEAT)) + 1
    kick, hat = _kick(), _hat()
    for b in range(bars):
        t0 = b * 4 * BEAT; c = b % 4
        intro = b == 0                       # primeiro compasso mais vazio: o gancho é da voz
        for q in range(4):
            if not intro:
                put(kick, t0 + q * BEAT, 0.55)
            put(hat, t0 + q * BEAT + BEAT / 2, 0.10, pan=0.3)
        for e in range(8):
            put(_bass(_hz(prog[c]), BEAT / 2), t0 + e * BEAT / 2, 0.30 if not intro else 0.18)
        for s in range(16):
            if s % 2 == 0 or s in (3, 11):
                put(_note(_hz(arp[c][s % 4] + (12 if s % 8 == 6 else 0)), 0.35), t0 + s * BEAT / 4, 0.16, pan=-0.35 if s % 4 < 2 else 0.35)
    n_out = int(total * SR)
    st = np.stack([L[:n_out], R[:n_out]], 1)
    fade = int(1.5 * SR); st[-fade:] *= np.linspace(1, 0, fade)[:, None]; st[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))[:, None]
    return st / (np.abs(st).max() or 1) * 0.7


def effects(total, events):
    n = int(total * SR)
    L = np.zeros(n + SR, np.float32); R = np.zeros(n + SR, np.float32)

    def put(x, at, g=1.0):
        i = max(0, int(at * SR))
        if i < n:
            x = np.asarray(x, np.float32)[: n + SR - i] * g
            L[i:i + len(x)] += x; R[i:i + len(x)] += x

    for ev in events:
        t, kind = ev[0], ev[1]
        if kind == "hook":
            put(S.thump(1.0, f=60), t + 0.02, 0.9); put(S.click(0.8), t + 0.02, 0.35)
        elif kind == "whoosh":
            put(S.whoosh(0.28), t - 0.12, 0.30)
        elif kind == "thump":
            put(S.thump(1.0, f=75), t, 0.55)
        elif kind == "pop":
            put(S.pop(), t, 0.35)
        elif kind == "cut":
            put(S.click(1.3), t, 0.10)
        elif kind == "ticks":
            d = ev[2] if len(ev) > 2 else 1.0
            for k in range(int(d / 0.06)):
                put(S.click(1.6 + 0.3 * (k % 3)), t + k * 0.06, 0.10)
            put(S.thump(1.0, f=85), t + d, 0.5)
    st = np.stack([L[:n], R[:n]], 1)
    return np.clip(st, -1, 1)


def build(total, events, out_music, out_sfx, music_on=True):
    from scipy.io import wavfile
    wavfile.write(out_sfx, SR, (effects(total, events) * 32767).astype(np.int16))
    if music_on:
        wavfile.write(out_music, SR, (music(total) * 32767).astype(np.int16))


if __name__ == "__main__":
    build(20, [(0, "hook"), (3, "whoosh"), (3.2, "ticks", 1.2), (8, "pop"), (8.4, "pop")], sys.argv[1], sys.argv[2])
    print("ok")
