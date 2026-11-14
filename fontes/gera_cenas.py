# gera_cenas.py: desenha as quatro cenas animadas do mod fundos-animados e grava hooks/cenas.js.
#
# Rodar de novo depois de mudar uma cena:
#   python fontes/gera_cenas.py [pasta-para-gravar-cada-cena-em-svg]
# O sorteio usa semente fixa, entao a mesma versao deste arquivo gera sempre as mesmas cenas.
# Regras do app para uma cena: viewBox, preserveAspectRatio="xMidYMid slice", menos de 131.072
# caracteres, animacao so em CSS dentro do proprio <style>, nada de script nem arquivo de fora.
# O assunto fica no alto e nas laterais: o meio e o pe da janela sao do texto e da caixa de mensagem.
import json
import math
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(os.path.dirname(AQUI), "hooks", "cenas.js")
LIMITE = 131072
W, H = 1600, 1000

MOVIMENTO_REDUZIDO = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def f(v):
    """Numero curto para o SVG: uma casa decimal, sem '.0' no fim."""
    s = f"{v:.1f}"
    if s in ("-0.0", "0.0"):
        return "0"
    return s[:-2] if s.endswith(".0") else s


def caminho(pontos, fechar=True):
    partes = [f"M{f(pontos[0][0])} {f(pontos[0][1])}"]
    partes += [f"L{f(x)} {f(y)}" for x, y in pontos[1:]]
    return "".join(partes) + ("Z" if fechar else "")


def svg(estilo, defs, corpo):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
        f"<style>{estilo}{MOVIMENTO_REDUZIDO}</style>"
        f"<defs>{defs}</defs>{corpo}</svg>"
    )


def degrade(id_, paradas, x1=0, y1=0, x2=0, y2=1, extra=""):
    """Degrade linear; cada parada e (posicao, cor) ou (posicao, cor, opacidade)."""
    stops = []
    for p in paradas:
        op = f' stop-opacity="{p[2]}"' if len(p) > 2 else ""
        stops.append(f'<stop offset="{p[0]}" stop-color="{p[1]}"{op}/>')
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{extra}>{"".join(stops)}</linearGradient>'


def radial(id_, paradas, extra=""):
    stops = []
    for p in paradas:
        op = f' stop-opacity="{p[2]}"' if len(p) > 2 else ""
        stops.append(f'<stop offset="{p[0]}" stop-color="{p[1]}"{op}/>')
    return f'<radialGradient id="{id_}"{extra}>{"".join(stops)}</radialGradient>'


def estrelas(r, n, x0, x1, y0, y1, rmin, rmax, opmin, opmax, piscam, op_por_y=None):
    """Circulos de estrela; parte deles pisca (classes p1, p2, p3 com atraso proprio)."""
    out = []
    for _ in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        raio = r.uniform(rmin, rmax)
        op = r.uniform(opmin, opmax) * (op_por_y(y) if op_por_y else 1)
        if op < 0.06:
            continue
        if r.random() < piscam:
            classe = r.choice(("p1", "p2", "p3"))
            out.append(
                f'<circle class="{classe}" style="animation-delay:-{r.uniform(0, 7):.1f}s" '
                f'cx="{f(x)}" cy="{f(y)}" r="{f(raio)}" fill-opacity="{op:.2f}"/>'
            )
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(raio)}" fill-opacity="{op:.2f}"/>')
    return "".join(out)


PISCA = (
    ".p1{animation:pisca 3.4s ease-in-out infinite}"
    ".p2{animation:pisca 5.2s ease-in-out infinite}"
    ".p3{animation:pisca 7.6s ease-in-out infinite}"
    "@keyframes pisca{0%,100%{opacity:1}50%{opacity:.2}}"
)


def serra(r, x0, x1, ymin, ymax, aspereza, passos):
    """Crista de montanha por deslocamento do ponto medio: lista de (x, y)."""
    pts = [(x0, r.uniform(ymin, ymax)), (x1, r.uniform(ymin, ymax))]
    desloc = (ymax - ymin) * 0.8
    for _ in range(passos):
        novos = []
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            novos.append((xa, ya))
            novos.append(((xa + xb) / 2, (ya + yb) / 2 + r.uniform(-desloc, desloc)))
        novos.append(pts[-1])
        pts = novos
        desloc *= aspereza
    return [(x, min(max(y, ymin - 40), ymax + 40)) for x, y in pts]


def janela_suave(pts, x0, x1, base, expoente=0.6):
    """Faz a crista nascer e morrer na base nas pontas (montanha isolada)."""
    out = []
    for x, y in pts:
        t = min(max((x - x0) / (x1 - x0), 0), 1)
        peso = math.sin(math.pi * t) ** expoente
        out.append((x, base - (base - y) * peso))
    return out


def morro(fn, x0=-20, x1=W + 20, passo=10):
    return [(x, fn(x)) for x in range(int(x0), int(x1) + 1, passo)]


def fechar_embaixo(pts, fundo=H + 10):
    return pts + [(pts[-1][0], fundo), (pts[0][0], fundo)]


# ---------------------------------------------------------------- Aurora boreal


def pinheiro(x, y, h):
    direita = []
    niveis = 4
    for k in range(1, niveis + 1):
        yk = y - h + k * h * 0.82 / niveis
        larg = h * (0.06 + 0.07 * k)
        direita.append((larg, yk))
        if k < niveis:
            direita.append((larg * 0.36, yk - h * 0.035))
    direita.append((h * 0.035, y - h * 0.16))
    direita.append((h * 0.035, y + 4))
    pts = [(x, y - h)] + [(x + dx, yy) for dx, yy in direita] + [(x - dx, yy) for dx, yy in reversed(direita)]
    return caminho(pts)


def cortina(r, grad, x0, x1, base, hmin, hmax, wmin, wmax, passo, opmin, opmax, fases=12, suave=0.05):
    """Uma cortina de aurora feita de raios verticais com o brilho embaixo.
    Cada raio recebe uma classe de fase (f0..f11): a fase anda com o x, entao uma onda
    de brilho percorre a cortina de um lado para o outro. `suave` e a fracao do comprimento
    em que a cortina vai sumindo em cada ponta, para nao terminar num corte reto."""
    raios = []
    x = x0
    while x < x1:
        w = r.uniform(wmin, wmax)
        yb = base(x + w / 2)
        borda = min((x - x0) / (x1 - x0), (x1 - x) / (x1 - x0)) / suave
        janela = 1 if borda >= 1 else 3 * borda ** 2 - 2 * borda ** 3
        h = r.uniform(hmin, hmax) * (0.35 + 0.65 * janela)
        op = r.uniform(opmin, opmax) * janela
        fase = int(((x - x0) / (x1 - x0)) * fases * 2 + r.uniform(-0.7, 0.7)) % fases
        raios.append(
            f'<rect class="f{fase}" x="{f(x)}" y="{f(yb - h)}" width="{f(w)}" height="{f(h)}" '
            f'fill="url(#{grad})" fill-opacity="{op:.2f}"/>'
        )
        x += passo * r.uniform(0.55, 1.25)
    return "".join(raios)


def aurora():
    r = random.Random(1859)
    defs = [
        degrade("ceu", [(0, "#02040b"), (0.36, "#060d22"), (0.66, "#0b1d38"), (0.84, "#123049"), (1, "#0e2337")]),
        radial("halo", [(0, "#2bd99b", 0.22), (0.55, "#1b8f8a", 0.08), (1, "#0b1d38", 0)]),
        radial("via", [(0, "#c9d8ff", 0.12), (0.6, "#8aa3e0", 0.05), (1, "#8aa3e0", 0)]),
        radial("chao", [(0, "#2a8f86", 0.28), (1, "#0e2337", 0)]),
        # raios: brilho na base (y=1) indo ate sumir no alto (y=0)
        degrade("gA", [(0, "#d9fff0", 0), (0.035, "#d4fff0", 0.95), (0.12, "#4dffb0", 0.85), (0.42, "#20d08e", 0.42),
                       (0.72, "#2a9d8f", 0.16), (0.88, "#8b5cff", 0.12), (1, "#8b5cff", 0)], y1=1, y2=0),
        degrade("gB", [(0, "#a6fff5", 0), (0.05, "#a6fff5", 0.65), (0.3, "#3fd9d2", 0.38), (0.7, "#3a6fd9", 0.14),
                       (1, "#3a6fd9", 0)], y1=1, y2=0),
        degrade("gC", [(0, "#ffb3ec", 0), (0.04, "#ffc2f0", 0.85), (0.12, "#ff6fd0", 0.5), (0.3, "#4dffb0", 0.45),
                       (0.65, "#23b58f", 0.18), (1, "#23b58f", 0)], y1=1, y2=0),
        '<linearGradient id="gm" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="170" y2="-55">'
        '<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#9fffe0" stop-opacity="0"/></linearGradient>',
    ]
    corpo = [f'<rect width="{W}" height="{H}" fill="url(#ceu)"/>']
    # via lactea discreta e um campo de estrelas finas ao longo dela
    corpo.append('<ellipse cx="820" cy="250" rx="980" ry="95" transform="rotate(-17 820 250)" fill="url(#via)"/>')
    via = []
    for _ in range(140):
        t = r.uniform(-1, 1)
        x = 820 + t * 950
        y = 250 - t * 950 * math.tan(math.radians(17)) + r.gauss(0, 34)
        via.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r.uniform(0.4, 0.9))}" fill-opacity="{r.uniform(0.25, 0.6):.2f}"/>')
    corpo.append(f'<g fill="#dfe8ff">{"".join(via)}</g>')
    corpo.append(f'<g fill="#ffffff">{estrelas(r, 170, 0, W, 0, 640, 0.5, 1.6, 0.35, 0.95, 0.24)}</g>')
    corpo.append('<ellipse cx="800" cy="330" rx="980" ry="250" fill="url(#halo)"/>')

    def base_a(x):
        return 300 + 70 * ((x - 800) / 900) ** 2 + 42 * math.sin(x / 280 + 0.6) + 18 * math.sin(x / 90 + 1.3)

    def base_b(x):
        return 228 + 36 * math.sin(x / 350 + 2.1) + 14 * math.sin(x / 120)

    def base_c(x):
        return 384 + 30 * math.sin(x / 200 + 0.4) + 10 * math.sin(x / 70)

    def base_d(x):
        return 400 + 26 * math.sin(x / 180 + 2.4)

    corpo.append('<g class="aurora">')
    corpo.append(f'<g class="cB">{cortina(r, "gB", -150, 1750, base_b, 80, 170, 14, 30, 15, 0.25, 0.65)}</g>')
    corpo.append(f'<g class="cA">{cortina(r, "gA", -180, 1780, base_a, 140, 290, 12, 26, 10, 0.35, 0.95)}</g>')
    corpo.append(f'<g class="cC">{cortina(r, "gC", 1000, 1760, base_c, 110, 220, 12, 24, 13, 0.3, 0.85, suave=0.3)}</g>')
    corpo.append(f'<g class="cD">{cortina(r, "gC", -160, 560, base_d, 90, 180, 12, 22, 14, 0.25, 0.7, suave=0.3)}</g>')
    corpo.append("</g>")
    # estrelas cadentes
    corpo.append('<g class="m1"><line x1="0" y1="0" x2="170" y2="-55" stroke="url(#gm)" stroke-width="2.2" stroke-linecap="round"/></g>')
    corpo.append('<g class="m2"><line x1="0" y1="0" x2="170" y2="-55" stroke="url(#gm)" stroke-width="1.8" stroke-linecap="round"/></g>')
    # luz da aurora no horizonte
    corpo.append('<ellipse cx="800" cy="720" rx="1100" ry="170" fill="url(#chao)"/>')
    # montanhas do fundo, com a crista acesa pela aurora
    fundo = serra(r, -20, W + 20, 610, 720, 0.55, 8)
    corpo.append(f'<path d="{caminho(fechar_embaixo(fundo))}" fill="#0b1828"/>')
    corpo.append(f'<path d="{caminho(fundo, False)}" fill="none" stroke="#7af5cf" stroke-opacity=".2" stroke-width="1.3"/>')
    meio = serra(r, -20, W + 20, 705, 790, 0.5, 7)
    corpo.append(f'<path d="{caminho(fechar_embaixo(meio))}" fill="#08121f"/>')

    def frente(x):
        return 868 + 38 * math.sin(x / 170) + 22 * math.sin(x / 61 + 1) + 46 * (1 - ((x - 800) / 800) ** 2)

    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(frente)))}" fill="#04080f"/>')
    pinhos = []
    for lado in ((-10, 540), (1060, W + 10)):
        x = lado[0]
        while x < lado[1]:
            perto_borda = abs(x - 800) / 800
            h = r.uniform(40, 105) * (0.75 + perto_borda * 0.7)
            pinhos.append(pinheiro(x, frente(x) + h * 0.17, h))
            x += r.uniform(13, 30)
    corpo.append(f'<path d="{"".join(pinhos)}" fill="#04080f"/>')

    fases = "".join(f".f{k}{{animation:pulso 10s ease-in-out -{k * 10 / 12:.2f}s infinite}}" for k in range(12))
    estilo = (
        PISCA + fases + "@keyframes pulso{0%,100%{opacity:.42}50%{opacity:1}}"
        ".cA,.cB,.cC,.cD{transform-box:fill-box;transform-origin:50% 100%}"
        ".cA{animation:balanca 19s ease-in-out infinite}"
        ".cB{animation:balanca2 27s ease-in-out infinite}"
        ".cC{animation:balanca 23s ease-in-out -8s infinite}"
        ".cD{animation:balanca2 21s ease-in-out -5s infinite}"
        "@keyframes balanca{0%,100%{transform:translateX(0) skewX(0deg)}50%{transform:translateX(-38px) skewX(-7deg)}}"
        "@keyframes balanca2{0%,100%{transform:translateX(0) skewX(0deg)}50%{transform:translateX(32px) skewX(5deg)}}"
        ".m1,.m2{opacity:0}"
        ".m1{animation:cai1 19s linear infinite}"
        ".m2{animation:cai2 31s linear -12s infinite}"
        "@keyframes cai1{0%,90%{opacity:0;transform:translate(1480px,70px)}91%{opacity:1}96%,100%{opacity:0;transform:translate(1130px,185px)}}"
        "@keyframes cai2{0%,93%{opacity:0;transform:translate(470px,60px)}94%{opacity:.9}98%,100%{opacity:0;transform:translate(230px,140px)}}"
    )
    return svg(estilo, "".join(defs), "".join(corpo))


# ---------------------------------------------------------------- Neon 84


def palmeira(r, xb, yb, altura, inclinacao, escala=1.0):
    partes = []
    # tronco: curva quadratica afinando para cima
    cx, cy = xb + inclinacao * 0.15, yb - altura * 0.55
    tx, ty = xb + inclinacao, yb - altura
    esq, dir_ = [], []
    for i in range(21):
        t = i / 20
        x = (1 - t) ** 2 * xb + 2 * (1 - t) * t * cx + t * t * tx
        y = (1 - t) ** 2 * yb + 2 * (1 - t) * t * cy + t * t * ty
        dx = 2 * (1 - t) * (cx - xb) + 2 * t * (tx - cx)
        dy = 2 * (1 - t) * (cy - yb) + 2 * t * (ty - cy)
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        larg = (15 - 8 * t) * escala / 2
        esq.append((x + nx * larg, y + ny * larg))
        dir_.append((x - nx * larg, y - ny * larg))
    partes.append(caminho(esq + list(reversed(dir_))))
    # folhas: curvas que saem da copa e caem nas pontas, com a borda de baixo recortada
    angulos = [-176, -156, -134, -110, -88, -64, -40, -18, 4, 24, 156]
    for a in angulos:
        comp = r.uniform(125, 170) * escala
        ar = math.radians(a + r.uniform(-6, 6))
        ux, uy = math.cos(ar), math.sin(ar)
        ponta = (tx + ux * comp, ty + uy * comp + comp * 0.5)
        ctrl = (tx + ux * comp * 0.55, ty + uy * comp * 0.55 - comp * 0.16)
        cima, baixo = [], []
        for i in range(23):
            t = i / 22
            x = (1 - t) ** 2 * tx + 2 * (1 - t) * t * ctrl[0] + t * t * ponta[0]
            y = (1 - t) ** 2 * ty + 2 * (1 - t) * t * ctrl[1] + t * t * ponta[1]
            dx = 2 * (1 - t) * (ctrl[0] - tx) + 2 * t * (ponta[0] - ctrl[0])
            dy = 2 * (1 - t) * (ctrl[1] - ty) + 2 * t * (ponta[1] - ctrl[1])
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n, dx / n
            if ny < 0:
                nx, ny = -nx, -ny
            larg = 13 * escala * math.sin(math.pi * min(t * 1.12, 1)) ** 0.8
            cima.append((x - nx * larg * 0.3, y - ny * larg * 0.3))
            recorte = 0.7 if i % 2 == 0 else 2.0
            baixo.append((x + nx * larg * recorte, y + ny * larg * recorte))
        partes.append(caminho(cima + list(reversed(baixo))))
    return "".join(partes)


def neon():
    r = random.Random(1984)
    hz = 640
    sx, sy, sr = 1230, 590, 205
    defs = [
        degrade("ceu", [(0, "#0b0220"), (0.3, "#1f0743"), (0.55, "#4a0c66"), (0.76, "#8e1576"), (0.9, "#e0306f"), (1, "#ff7a59")]),
        degrade("chaoG", [(0, "#2a0548"), (0.16, "#14022b"), (1, "#07010f")]),
        degrade("gsol", [(0, "#fff3a3"), (0.42, "#ffb347"), (0.72, "#ff5f6d"), (1, "#ff2f92")]),
        radial("halo", [(0, "#ff6ec7", 0.55), (0.45, "#ff3d81", 0.22), (1, "#ff3d81", 0)]),
        degrade("nevoa", [(0, "#ff3d81", 0.55), (1, "#ff3d81", 0)]),
        degrade("faixaHz", [(0, "#ff4fa3", 0), (0.5, "#ff4fa3", 0.45), (1, "#ff4fa3", 0)]),
        f'<linearGradient id="grade" gradientUnits="userSpaceOnUse" x1="0" y1="{hz}" x2="0" y2="{H}">'
        '<stop offset="0" stop-color="#ff2bd6" stop-opacity=".12"/><stop offset=".35" stop-color="#ff2bd6" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#ff5ce1" stop-opacity=".95"/></linearGradient>',
        f'<clipPath id="acima"><rect width="{W}" height="{hz}"/></clipPath>',
        f'<clipPath id="chao"><rect y="{hz}" width="{W}" height="{H - hz}"/></clipPath>',
    ]
    # faixas que descem pelo sol (mascara: preto esconde)
    faixas = "".join(
        f'<rect class="fx" style="animation-delay:-{k:.0f}s" x="{sx - sr - 10}" y="{sy - 72}" width="{2 * sr + 20}" height="16"/>'
        for k in range(7)
    )
    defs.append(
        f'<mask id="faixas" maskUnits="userSpaceOnUse" x="{sx - sr - 10}" y="{sy - sr - 10}" width="{2 * sr + 20}" height="{2 * sr + 20}">'
        f'<rect x="{sx - sr - 10}" y="{sy - sr - 10}" width="{2 * sr + 20}" height="{2 * sr + 20}" fill="#fff"/>'
        f'<g fill="#000">{faixas}</g></mask>'
    )
    corpo = [f'<rect width="{W}" height="{hz}" fill="url(#ceu)"/>']
    corpo.append(f'<g fill="#ffe6ff">{estrelas(r, 110, 0, W, 0, 430, 0.5, 1.5, 0.3, 0.9, 0.25, lambda y: 1 - y / 520)}</g>')
    corpo.append(
        f'<g class="sol"><circle class="halo" cx="{sx}" cy="{sy}" r="430" fill="url(#halo)"/>'
        f'<g clip-path="url(#acima)"><circle cx="{sx}" cy="{sy}" r="{sr}" fill="url(#gsol)" mask="url(#faixas)"/></g></g>'
    )
    # montanhas: cordilheira baixa ao fundo, serra grande a esquerda e morros na frente do sol
    longe = serra(r, -20, W + 20, 560, 612, 0.5, 6)
    corpo.append(f'<path d="{caminho(longe + [(W + 20, hz + 2), (-20, hz + 2)])}" fill="#2b0a4d"/>')
    corpo.append(f'<path d="{caminho(longe, False)}" fill="none" stroke="#ff4fd8" stroke-opacity=".5" stroke-width="1.4"/>')
    grande = janela_suave(serra(r, -60, 720, 420, 560, 0.52, 6), -60, 720, hz + 2)
    corpo.append(f'<path d="{caminho(grande + [(720, hz + 2), (-60, hz + 2)])}" fill="#160530"/>')
    fios = []
    for i in range(4, len(grande) - 4, 6):
        x, y = grande[i]
        fios.append(f"M{f(x)} {f(y)}L{f(x + (x - 330) * 0.25)} {hz}")
    corpo.append(f'<path d="{"".join(fios)}" fill="none" stroke="#3ee6ff" stroke-opacity=".18" stroke-width="1"/>')
    corpo.append(f'<path d="{caminho(grande, False)}" fill="none" stroke="#3ee6ff" stroke-opacity=".9" stroke-width="2"/>')
    perto_sol = janela_suave(serra(r, 1150, 1680, 582, 626, 0.5, 5), 1150, 1680, hz + 2, 0.4)
    corpo.append(f'<path d="{caminho(perto_sol + [(1680, hz + 2), (1150, hz + 2)])}" fill="#1c0638"/>')
    corpo.append(f'<path d="{caminho(perto_sol, False)}" fill="none" stroke="#ff4fd8" stroke-opacity=".8" stroke-width="1.6"/>')
    # chao com a grade
    corpo.append(f'<rect y="{hz}" width="{W}" height="{H - hz}" fill="url(#chaoG)"/>')
    verticais = "".join(f"M{f(800 + k * 3.2)} {hz}L{f(800 + k * 80)} {H}" for k in range(-26, 27))
    horizontais = "".join(
        f'<rect class="hz" style="animation-delay:-{k * 0.5:.2f}s" x="-100" y="{hz}" width="{W + 200}" height="2.2"/>'
        for k in range(14)
    )
    corpo.append(
        f'<g clip-path="url(#chao)"><path d="{verticais}" fill="none" stroke="url(#grade)" stroke-width="1.5"/>'
        f'<g fill="#ff3ec9">{horizontais}</g></g>'
    )
    corpo.append(f'<rect y="{hz}" width="{W}" height="90" fill="url(#nevoa)"/>')
    corpo.append(f'<rect y="{hz - 60}" width="{W}" height="120" fill="url(#faixaHz)"/>')
    corpo.append(f'<rect y="{hz - 1.5}" width="{W}" height="3" fill="#ffb3f0"/>')
    # palmeiras nas pontas
    corpo.append(f'<g class="palma1" fill="#0b0118"><path d="{palmeira(r, 140, 770, 330, 40)}"/></g>')
    corpo.append(f'<g class="palma2" fill="#0b0118"><path d="{palmeira(r, 1505, 800, 300, -50, 0.92)}"/></g>')

    estilo = (
        PISCA +
        ".halo{animation:halo 6s ease-in-out infinite}@keyframes halo{0%,100%{opacity:.72}50%{opacity:1}}"
        ".fx{transform-box:fill-box;transform-origin:50% 0;animation:faixa 7s linear infinite}"
        "@keyframes faixa{0%{transform:translateY(0) scaleY(.12)}100%{transform:translateY(124px) scaleY(1)}}"
        ".hz{transform-box:fill-box;transform-origin:50% 0;animation:linha 7s cubic-bezier(.7,0,.84,0) infinite}"
        "@keyframes linha{0%{transform:translateY(0) scaleY(.4);opacity:0}6%{opacity:.6}100%{transform:translateY(362px) scaleY(2.4);opacity:1}}"
        ".palma1,.palma2{transform-box:view-box}"
        ".palma1{transform-origin:140px 770px;animation:palma 8s ease-in-out infinite}"
        ".palma2{transform-origin:1505px 800px;animation:palma 9.5s ease-in-out -3s infinite}"
        "@keyframes palma{0%,100%{transform:rotate(0deg)}50%{transform:rotate(1.4deg)}}"
        "@media (max-aspect-ratio:5/4){.sol{transform:translateX(-180px)}}"
        "@media (max-aspect-ratio:4/5){.sol{transform:translateX(-430px)}}"
    )
    return svg(estilo, "".join(defs), "".join(corpo))


# ---------------------------------------------------------------- Sertao ao entardecer


def mandacaru(x, yb, h, w, bracos, costelas=False):
    """Mandacaru em silhueta: coluna central e bracos em L com ponta arredondada.
    Cada braco e (altura_do_cotovelo, lado, alcance, subida, largura)."""
    partes = [
        f'<rect x="{f(x - w / 2)}" y="{f(yb - h)}" width="{f(w)}" height="{f(h + 4)}" rx="{f(w / 2)}"/>'
    ]
    for (alt, lado, alcance, subida, aw) in bracos:
        yc = yb - alt
        xe = x + lado * alcance
        x_ini = min(x, xe)
        partes.append(f'<rect x="{f(x_ini)}" y="{f(yc - aw / 2)}" width="{f(abs(xe - x))}" height="{f(aw)}" rx="{f(aw / 2)}"/>')
        partes.append(f'<rect x="{f(xe - aw / 2)}" y="{f(yc - subida)}" width="{f(aw)}" height="{f(subida + aw / 2)}" rx="{f(aw / 2)}"/>')
    if costelas:
        linhas = "".join(f"M{f(x + d)} {f(yb - h + w * 0.6)}V{f(yb)}" for d in (-w * 0.28, 0, w * 0.28))
        partes.append(f'<path d="{linhas}" fill="none" stroke="#2c1422" stroke-opacity=".8" stroke-width="1.2"/>')
    return "".join(partes)


def galhos(r, x, y, ang, comp, larg, nivel, out):
    """Arvore da caatinga sem folha: cada galho e um poligono afinando, com curva leve."""
    x2 = x + comp * math.cos(ang)
    y2 = y - comp * math.sin(ang)
    curva = r.uniform(-0.25, 0.25) * comp
    cx = (x + x2) / 2 + curva * math.sin(ang)
    cy = (y + y2) / 2 + curva * math.cos(ang)
    lado1, lado2 = [], []
    for i in range(6):
        t = i / 5
        px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * x2
        py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * y2
        lg = larg * (1 - 0.35 * t) / 2
        lado1.append((px + lg * math.sin(ang), py + lg * math.cos(ang)))
        lado2.append((px - lg * math.sin(ang), py - lg * math.cos(ang)))
    out.append(caminho(lado1 + list(reversed(lado2))))
    if nivel == 0:
        return
    filhos = 2 if r.random() < 0.65 else 3
    abertura = r.uniform(0.45, 0.8)
    for k in range(filhos):
        desvio = (k - (filhos - 1) / 2) * abertura + r.uniform(-0.2, 0.2)
        galhos(r, x2, y2, ang + desvio, comp * r.uniform(0.66, 0.82), larg * 0.66, nivel - 1, out)


def catavento(x, ychao, altura):
    """Cata-vento de fazenda: torre trelicada, rotor de 16 pas (gira) e o leme."""
    hx, hy = x, ychao - altura
    base, topo = 26, 5
    pernas = f"M{f(x - base)} {f(ychao)}L{f(x - topo)} {f(hy + 14)}M{f(x + base)} {f(ychao)}L{f(x + topo)} {f(hy + 14)}"
    travessas = []
    n = 7
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        ya, yb_ = ychao - (altura - 14) * t0, ychao - (altura - 14) * t1
        la, lb = base - (base - topo) * t0, base - (base - topo) * t1
        travessas.append(f"M{f(x - la)} {f(ya)}L{f(x + lb)} {f(yb_)}M{f(x + la)} {f(ya)}L{f(x - lb)} {f(yb_)}")
        travessas.append(f"M{f(x - lb)} {f(yb_)}H{f(x + lb)}")
    torre = f'<path d="{pernas}{"".join(travessas)}" fill="none" stroke="#1a0b15" stroke-width="2.2"/>'
    leme = (
        f'<path d="M{f(hx)} {f(hy)}L{f(hx + 64)} {f(hy - 1)}" stroke="#1a0b15" stroke-width="2.4"/>'
        f'<path d="M{f(hx + 50)} {f(hy - 13)}L{f(hx + 78)} {f(hy - 9)}L{f(hx + 78)} {f(hy + 8)}L{f(hx + 50)} {f(hy + 5)}Z" fill="#1a0b15"/>'
    )
    pas = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        a1, a2 = a - 0.05, a + 0.11
        r1, r2 = 9, 52
        pts = [
            (hx + r1 * math.cos(a1), hy + r1 * math.sin(a1)),
            (hx + r2 * math.cos(a1), hy + r2 * math.sin(a1)),
            (hx + r2 * math.cos(a2), hy + r2 * math.sin(a2)),
            (hx + r1 * math.cos(a + 0.02), hy + r1 * math.sin(a + 0.02)),
        ]
        pas.append(caminho(pts))
    rotor = (
        f'<g class="rotor"><path d="{"".join(pas)}" fill="#1a0b15"/>'
        f'<circle cx="{f(hx)}" cy="{f(hy)}" r="52" fill="none" stroke="#1a0b15" stroke-width="1.6"/>'
        f'<circle cx="{f(hx)}" cy="{f(hy)}" r="31" fill="none" stroke="#1a0b15" stroke-width="1.2"/>'
        f'<circle cx="{f(hx)}" cy="{f(hy)}" r="7" fill="#1a0b15"/></g>'
    )
    return torre + leme + rotor


def nuvem(r, cx, cy, w, h):
    partes = []
    for _ in range(4):
        dx = r.uniform(-w * 0.35, w * 0.35)
        dy = r.uniform(-h * 0.4, h * 0.3)
        partes.append(
            f'<ellipse cx="{f(cx + dx)}" cy="{f(cy + dy)}" rx="{f(w * r.uniform(0.35, 0.6))}" ry="{f(h * r.uniform(0.5, 0.9))}"/>'
        )
    return "".join(partes)


def sertao():
    r = random.Random(1947)
    sx, sy, sr = 1150, 652, 92
    defs = [
        degrade("ceu", [(0, "#1b1238"), (0.18, "#33205c"), (0.36, "#643071"), (0.5, "#a8456a"), (0.6, "#d9604f"),
                        (0.67, "#f08a4b"), (0.73, "#f8b25e"), (0.79, "#ffd27f"), (1, "#ffe2a0")]),
        radial("disco", [(0, "#fffbe0"), (0.55, "#ffe08a"), (0.85, "#ffb24d"), (1, "#ff8a3d")]),
        radial("brilho", [(0, "#ffd36b", 0.6), (0.3, "#ff9a4d", 0.28), (1, "#ff9a4d", 0)]),
        radial("lua", [(0, "#fff3d6", 0.35), (1, "#fff3d6", 0)]),
        radial("vaga", [(0, "#fff1a0", 0.9), (0.4, "#ffd75e", 0.35), (1, "#ffd75e", 0)]),
        radial("luz", [(0, "#ffcf6b", 0.55), (1, "#ffcf6b", 0)]),
        degrade("nuvemG", [(0, "#5e3466"), (0.6, "#b05a6c"), (1, "#ffb07a")]),
        degrade("chapadaG", [(0, "#c0687a"), (1, "#8a4260")]),
        degrade("mormaco", [(0, "#ffc070", 0), (0.55, "#ffc070", 0.32), (1, "#ffc070", 0)]),
        '<mask id="crescente"><rect width="1600" height="1000" fill="#fff"/><circle cx="312" cy="160" r="25" fill="#000"/></mask>',
    ]
    corpo = [f'<rect width="{W}" height="{H}" fill="url(#ceu)"/>']
    corpo.append(f'<g fill="#fff6e8">{estrelas(r, 90, 0, W, 0, 340, 0.5, 1.4, 0.4, 0.95, 0.3, lambda y: max(0, 1 - y / 360))}</g>')
    # lua crescente
    corpo.append('<circle cx="300" cy="168" r="80" fill="url(#lua)"/>')
    corpo.append('<circle cx="300" cy="168" r="26" fill="#fff3d6" mask="url(#crescente)"/>')
    # sol descendo devagar, com o brilho em volta
    corpo.append(
        f'<g class="sol"><circle cx="{sx}" cy="{sy}" r="540" fill="url(#brilho)"/>'
        f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="url(#disco)"/></g>'
    )
    # nuvens compridas acesas por baixo
    direita = "".join(nuvem(r, *c) for c in ((1330, 468, 270, 26), (1490, 522, 210, 20), (1190, 405, 180, 15)))
    esquerda = "".join(nuvem(r, *c) for c in ((230, 430, 250, 24), (430, 505, 175, 18)))
    corpo.append(f'<g class="nuvens1" fill="url(#nuvemG)" opacity=".85">{direita}</g>')
    corpo.append(f'<g class="nuvens2" fill="url(#nuvemG)" opacity=".8">{esquerda}</g>')
    corpo.append(f'<rect y="590" width="{W}" height="150" fill="url(#mormaco)"/>')

    # chapada ao longe: dois plateaus de topo reto; o sol se poe atras do segundo
    def topo_chapada(x):
        if x < 90:
            return 735 - (x + 20) / 110 * 59
        if x < 930:
            return 676 + 2.5 * math.sin(x / 47)
        if x < 1040:
            return 676 + (x - 930) / 110 * 64
        if x < 1095:
            return 740 - (x - 1040) / 55 * 42
        return 698 + 2 * math.sin(x / 39)

    chapada = morro(topo_chapada, passo=8)
    corpo.append(f'<path d="{caminho(fechar_embaixo(chapada))}" fill="url(#chapadaG)"/>')
    borda = [(x, y) for x, y in chapada if 90 <= x <= 930 or x >= 1095]
    corpo.append(f'<path d="{caminho([p for p in borda if p[0] <= 930], False)}" fill="none" stroke="#ffb38a" stroke-opacity=".45" stroke-width="1.5"/>')
    corpo.append(f'<path d="{caminho([p for p in borda if p[0] >= 1095], False)}" fill="none" stroke="#ffc29a" stroke-opacity=".55" stroke-width="1.5"/>')

    def meio(x):
        return 792 + 18 * math.sin(x / 140) + 12 * math.sin(x / 53 + 2)

    def perto(x):
        return 882 + 15 * math.sin(x / 210 + 1) + 8 * math.sin(x / 71)

    def frente(x):
        return 952 + 12 * math.sin(x / 120) + 6 * math.sin(x / 37)

    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(meio)))}" fill="#5e2b47"/>')
    # casinha com a janela acesa e a cerca, no morro do meio, a esquerda
    gx = 150
    gy = meio(gx) + 3
    corpo.append(
        f'<g fill="#3d1d33"><rect x="{f(gx - 34)}" y="{f(gy - 38)}" width="68" height="40"/>'
        f'<path d="M{f(gx - 44)} {f(gy - 36)}L{f(gx)} {f(gy - 64)}L{f(gx + 44)} {f(gy - 36)}Z" fill="#2e1527"/>'
        f'<rect x="{f(gx - 24)}" y="{f(gy - 26)}" width="11" height="28" fill="#2a1224"/></g>'
        f'<g class="janela"><circle cx="{f(gx + 15)}" cy="{f(gy - 21)}" r="26" fill="url(#luz)"/>'
        f'<rect x="{f(gx + 9)}" y="{f(gy - 27)}" width="12" height="11" fill="#ffcf6b"/></g>'
    )
    postes = "".join(f'<rect x="{f(x)}" y="{f(meio(x) - 18)}" width="3" height="20"/>' for x in range(205, 545, 24))
    arame = [(x + 1.5, meio(x) - 13) for x in range(205, 545, 24)]
    arame2 = [(x + 1.5, meio(x) - 7) for x in range(205, 545, 24)]
    corpo.append(
        f'<g fill="#3a1b30">{postes}</g><path d="{caminho(arame, False)}{caminho(arame2, False)}" fill="none" stroke="#3a1b30" stroke-width=".9"/>'
    )
    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(perto)))}" fill="#2b1324"/>')
    # cata-vento girando na direita
    corpo.append(catavento(1305, perto(1305) + 4, 252))
    # arvore seca da caatinga na esquerda
    ramos = []
    galhos(r, 470, perto(470) + 6, math.radians(86), 78, 15, 6, ramos)
    corpo.append(f'<path d="{"".join(ramos)}" fill="#160a12"/>')
    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(frente)))}" fill="#170a12"/>')
    # mandacarus e touceiras de xique-xique
    corpo.append(
        '<g fill="#120710">'
        + mandacaru(1462, frente(1462) + 6, 330, 36, [(150, 1, 46, 120, 26), (110, -1, 50, 95, 24), (205, -1, 34, 60, 20)], True)
        + mandacaru(232, frente(232) + 6, 238, 28, [(95, 1, 38, 85, 20), (130, -1, 34, 70, 18)], True)
        + "".join(
            mandacaru(x, frente(x) + 6, h, 9, [])
            for x, h in ((352, 42), (364, 30), (341, 26), (1372, 38), (1386, 52), (1398, 30), (612, 24), (1012, 22))
        )
        + "</g>"
    )
    # passaros: um bando atravessando o ceu e um urubu planando em circulo
    passaro = "M-11 0Q-5.5-7 0 0Q5.5-7 11 0"
    bando = "".join(
        f'<g transform="translate({dx} {dy}) scale({s})"><path class="asa" style="animation-delay:-{r.uniform(0, 0.9):.2f}s" d="{passaro}"/></g>'
        for dx, dy, s in ((0, 0, 1), (-42, 15, 0.9), (-80, -9, 0.85), (-118, 22, 0.8), (-158, 4, 0.75), (34, -20, 0.9))
    )
    corpo.append(f'<g class="bando" fill="none" stroke="#2b1631" stroke-width="2.2" stroke-linecap="round">{bando}</g>')
    # o grupo de fora da a volta; o de dentro gira ao contrario, entao o urubu nao tomba
    corpo.append(
        '<g class="urubu"><g class="urubu-corpo">'
        '<path d="M432 238Q446 230 458 236Q470 230 484 238Q470 236 458 241Q446 236 432 238Z" fill="#2b1631"/></g></g>'
    )
    # vaga-lumes nas laterais, perto do chao
    vagas = []
    for k in range(26):
        x = r.uniform(20, 560) if k % 2 == 0 else r.uniform(1040, 1580)
        y = r.uniform(820, 975)
        vagas.append(
            f'<g class="v{k % 3}" style="animation-delay:-{r.uniform(0, 6):.1f}s">'
            f'<circle cx="{f(x)}" cy="{f(y)}" r="10" fill="url(#vaga)"/><circle cx="{f(x)}" cy="{f(y)}" r="1.8" fill="#fff6c2"/></g>'
        )
    corpo.append("".join(vagas))

    estilo = (
        PISCA +
        ".sol{animation:poente 90s ease-in-out infinite alternate}"
        "@keyframes poente{from{transform:translateY(0)}to{transform:translateY(30px)}}"
        ".nuvens1{animation:nuvem1 70s ease-in-out infinite alternate}"
        ".nuvens2{animation:nuvem2 85s ease-in-out infinite alternate}"
        "@keyframes nuvem1{from{transform:translateX(0)}to{transform:translateX(40px)}}"
        "@keyframes nuvem2{from{transform:translateX(0)}to{transform:translateX(-30px)}}"
        ".janela{animation:lamparina 4s steps(8) infinite}"
        "@keyframes lamparina{0%,100%{opacity:1}30%{opacity:.82}55%{opacity:.95}70%{opacity:.78}}"
        ".rotor{transform-box:fill-box;transform-origin:center;animation:gira 16s linear infinite}"
        "@keyframes gira{to{transform:rotate(360deg)}}"
        ".bando{animation:voo 48s linear infinite}"
        "@keyframes voo{0%{transform:translate(-260px,300px)}100%{transform:translate(1860px,185px)}}"
        ".asa{transform-box:fill-box;transform-origin:50% 100%;animation:bate .9s ease-in-out infinite alternate}"
        "@keyframes bate{from{transform:scaleY(1)}to{transform:scaleY(-.45)}}"
        ".urubu{transform-box:view-box;transform-origin:390px 250px;animation:circula 34s linear infinite}"
        ".urubu-corpo{transform-box:fill-box;transform-origin:center;animation:destomba 34s linear infinite}"
        "@keyframes circula{to{transform:rotate(360deg)}}"
        "@keyframes destomba{to{transform:rotate(-360deg)}}"
        ".v0,.v1,.v2{opacity:0}"
        ".v0{animation:vaga 3.6s ease-in-out infinite}.v1{animation:vaga 4.9s ease-in-out infinite}.v2{animation:vaga 6.1s ease-in-out infinite}"
        "@keyframes vaga{0%,38%{opacity:0;transform:translate(0,0)}55%{opacity:1;transform:translate(6px,-8px)}"
        "75%{opacity:.85;transform:translate(12px,-4px)}92%,100%{opacity:0;transform:translate(16px,2px)}}"
        "@media (max-aspect-ratio:5/4){.sol{animation:none;transform:translateX(-120px)}}"
        "@media (max-aspect-ratio:4/5){.sol{transform:translateX(-350px)}}"
    )
    return svg(estilo, "".join(defs), "".join(corpo))


# ---------------------------------------------------------------- Cerrado de manha


def ramos(r, x, y, ang, comp, larg, nivel, out, pontas, abre=(0.45, 0.8), encolhe=(0.66, 0.82)):
    """Galhos torcidos como os de `galhos`, guardando em `pontas` onde cada galho fino termina."""
    x2 = x + comp * math.cos(ang)
    y2 = y - comp * math.sin(ang)
    curva = r.uniform(-0.35, 0.35) * comp
    cx = (x + x2) / 2 + curva * math.sin(ang)
    cy = (y + y2) / 2 + curva * math.cos(ang)
    lado1, lado2 = [], []
    for i in range(6):
        t = i / 5
        px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * x2
        py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * y2
        lg = larg * (1 - 0.35 * t) / 2
        lado1.append((px + lg * math.sin(ang), py + lg * math.cos(ang)))
        lado2.append((px - lg * math.sin(ang), py - lg * math.cos(ang)))
    out.append(caminho(lado1 + list(reversed(lado2))))
    if nivel == 0:
        pontas.append((x2, y2))
        return
    filhos = 2 if r.random() < 0.7 else 3
    abertura = r.uniform(*abre)
    for k in range(filhos):
        desvio = (k - (filhos - 1) / 2) * abertura + r.uniform(-0.2, 0.2)
        ramos(r, x2, y2, ang + desvio, comp * r.uniform(*encolhe), larg * 0.64, nivel - 1, out, pontas, abre, encolhe)


def copa(r, pontas, raio, espalha, n_por_ponta):
    """Tufos redondos em volta das pontas dos galhos: a copa de folha ou de flor."""
    out = []
    for px, py in pontas:
        for _ in range(n_por_ponta):
            out.append(
                f'<circle cx="{f(px + r.uniform(-espalha, espalha))}" cy="{f(py + r.uniform(-espalha * 0.7, espalha * 0.4))}" '
                f'r="{f(raio * r.uniform(0.6, 1.15))}"/>'
            )
    return "".join(out)


def buriti(r, x, yb, h, escala=1.0):
    """Buriti da vereda: tronco reto e liso, coroa de folhas em leque e a saia de folhas secas."""
    tx, ty = x + r.uniform(-6, 6), yb - h
    tronco = caminho([(x - 7 * escala, yb + 4), (tx - 4.5 * escala, ty + 10), (tx + 4.5 * escala, ty + 10), (x + 7 * escala, yb + 4)])
    saia = []
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 17 + r.uniform(-5, 5))
        comp = r.uniform(34, 50) * escala
        bx, by = tx + math.cos(a) * 6, ty + 14
        ponta = (bx + math.cos(a) * comp * 0.35, by + comp)
        saia.append(caminho([(bx - 4 * escala, by), ponta, (bx + 4 * escala, by)]))
    hastes, leques = [], []
    for k in range(13):
        a = math.radians(-180 + k * 15 + r.uniform(-5, 5))
        haste = r.uniform(42, 60) * escala
        cx = tx + math.cos(a) * haste
        cy = ty + math.sin(a) * haste * 0.8 + abs(math.cos(a)) * 16 * escala
        hastes.append(f"M{f(tx)} {f(ty + 2)}Q{f((tx + cx) / 2)} {f(min(ty, cy) - 8 * escala)} {f(cx)} {f(cy)}")
        # o leque: segmentos finos abrindo a partir do fim da haste, pendendo nas pontas
        leque = []
        abre = math.radians(70)
        n = 9
        for i in range(n + 1):
            b = a - abre / 2 + abre * i / n
            raio = (r.uniform(40, 52) if i % 2 == 0 else r.uniform(28, 36)) * escala
            leque.append((cx + math.cos(b) * raio, cy + math.sin(b) * raio * 0.75 + raio * 0.28))
        leques.append(caminho([(cx, cy)] + leque))
    return (
        f'<path d="{tronco}" fill="#3a3a2c"/>'
        f'<path d="{"".join(saia)}" fill="#7a5a32"/>'
        f'<path d="{"".join(hastes)}" fill="none" stroke="#24452c" stroke-width="{f(2.2 * escala)}"/>'
        f'<path d="{"".join(leques)}" fill="#2f5e36"/>'
    )


def cupinzeiro(x, yb, h, w):
    """Cupinzeiro: monte de terra vermelha, arredondado e meio torto."""
    return (
        f'<path d="M{f(x - w / 2)} {f(yb + 3)}C{f(x - w * 0.45)} {f(yb - h * 0.55)} {f(x - w * 0.25)} {f(yb - h)} {f(x + w * 0.02)} {f(yb - h)}'
        f'C{f(x + w * 0.3)} {f(yb - h * 0.98)} {f(x + w * 0.42)} {f(yb - h * 0.5)} {f(x + w / 2)} {f(yb + 3)}Z"/>'
    )


def capim(r, x0, x1, chao, n, hmin, hmax, classes=("c0", "c1", "c2")):
    """Touceiras de capim dourado: hastes curvas finas, cada touceira balanca com fase propria."""
    out = []
    for _ in range(n):
        x = r.uniform(x0, x1)
        y = chao(x) + r.uniform(2, 10)
        hastes = []
        for _ in range(r.randint(5, 9)):
            h = r.uniform(hmin, hmax)
            dx = r.uniform(-h * 0.35, h * 0.35)
            hastes.append(f"M{f(x + r.uniform(-4, 4))} {f(y)}Q{f(x + dx * 0.2)} {f(y - h * 0.6)} {f(x + dx)} {f(y - h)}")
        cor = r.choice(("#d9a441", "#e6b856", "#c99432"))
        out.append(
            f'<path class="{r.choice(classes)}" style="animation-delay:-{r.uniform(0, 5):.1f}s" '
            f'd="{"".join(hastes)}" stroke="{cor}"/>'
        )
    return "".join(out)


def arara(cor_dorso, cor_peito):
    """Arara de perfil voando para a direita, com a cauda comprida; a asa bate (classe asa)."""
    return (
        f'<path d="M-46 4Q-20 2 0 -2Q10 -6 18 -4Q24 -2 22 2Q16 6 4 6Q-18 8 -46 4Z" fill="{cor_dorso}"/>'
        f'<path d="M-6 4Q6 8 16 3Q8 9 -4 8Z" fill="{cor_peito}"/>'
        f'<path d="M-50 3L-78 7L-48 6Z" fill="{cor_dorso}"/>'
        f'<circle cx="17" cy="-2" r="1.4" fill="#111"/>'
        f'<path d="M21 -3Q27 -1 24 3Q22 1 21 -1Z" fill="#222"/>'
        f'<path class="asa" d="M-14 0Q-4 -30 14 -40Q4 -18 6 -1Z" fill="{cor_dorso}"/>'
    )


def cerrado():
    r = random.Random(1960)
    sx, sy, sr = 330, 600, 70
    defs = [
        degrade("ceu", [(0, "#4f86c6"), (0.28, "#7fa9d6"), (0.5, "#b4cbe0"), (0.64, "#e6d4b8"), (0.72, "#f6cf96"),
                        (0.8, "#fbe2b4"), (1, "#fcebc8")]),
        radial("disco", [(0, "#fffdf2"), (0.6, "#fff1c4"), (1, "#ffd98a")]),
        radial("brilho", [(0, "#fff0c0", 0.75), (0.25, "#ffd98a", 0.35), (1, "#ffd98a", 0)]),
        degrade("nuvemG", [(0, "#ffffff", 0.95), (1, "#f3dcc0", 0.85)]),
        degrade("chapadaG", [(0, "#a58ea6"), (1, "#c3a7a4")]),
        degrade("serraG", [(0, "#8d8a6a"), (1, "#a3986e")]),
        degrade("bruma", [(0, "#fbe6c2", 0), (0.5, "#fbe6c2", 0.55), (1, "#fbe6c2", 0)]),
        degrade("veredaG", [(0, "#6f8a48"), (1, "#56743a")]),
        degrade("campoG", [(0, "#b4924a"), (1, "#9a7a3a")]),
        degrade("frenteG", [(0, "#7d5a2c"), (1, "#5e4220")]),
        degrade("aguaG", [(0, "#cfe0e6"), (1, "#9fbfcc")]),
    ]
    corpo = [f'<rect width="{W}" height="{H}" fill="url(#ceu)"/>']
    # sol nascendo baixo, a esquerda, com o brilho largo da manha
    corpo.append(
        f'<g class="sol"><circle cx="{sx}" cy="{sy}" r="460" fill="url(#brilho)"/>'
        f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="url(#disco)"/></g>'
    )
    # nuvens altas de tempo seco
    alto = "".join(nuvem(r, *c) for c in ((1240, 150, 260, 30), (1460, 230, 190, 22), (980, 95, 170, 18)))
    baixo = "".join(nuvem(r, *c) for c in ((160, 250, 230, 26), (520, 175, 150, 16)))
    corpo.append(f'<g class="nuvens1" fill="url(#nuvemG)" opacity=".9">{alto}</g>')
    corpo.append(f'<g class="nuvens2" fill="url(#nuvemG)" opacity=".8">{baixo}</g>')

    # chapada ao longe: topo reto e paredao, azulada pela distancia
    def topo_chapada(x):
        if x < 520:
            return 640 + 2 * math.sin(x / 41)
        if x < 600:
            return 640 + (x - 520) / 80 * 46
        if x < 1080:
            return 686 + 6 * math.sin(x / 90)
        if x < 1150:
            return 690 - (x - 1080) / 70 * 62
        return 628 + 2 * math.sin(x / 37)

    chapada = morro(topo_chapada, passo=8)
    corpo.append(f'<path d="{caminho(fechar_embaixo(chapada))}" fill="url(#chapadaG)"/>')
    corpo.append(f'<path d="{caminho([p for p in chapada if p[0] < 520], False)}" fill="none" stroke="#fff0d8" stroke-opacity=".55" stroke-width="1.5"/>')
    corpo.append(f'<path d="{caminho([p for p in chapada if p[0] > 1150], False)}" fill="none" stroke="#fff0d8" stroke-opacity=".55" stroke-width="1.5"/>')
    corpo.append(f'<rect y="610" width="{W}" height="130" fill="url(#bruma)"/>')

    def meio(x):
        return 742 + 14 * math.sin(x / 160) + 8 * math.sin(x / 57 + 1)

    def campo(x):
        return 830 + 16 * math.sin(x / 230 + 2) + 7 * math.sin(x / 63)

    def frente(x):
        return 940 + 14 * math.sin(x / 140) + 6 * math.sin(x / 41)

    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(meio)))}" fill="url(#serraG)"/>')
    # arvorezinhas torcidas espalhadas no meio: o cerrado visto de longe
    longe_tr, longe_cp = [], []
    for x in list(range(30, 560, 44)) + list(range(1060, 1590, 44)):
        x += r.uniform(-14, 14)
        y = meio(x) + 2
        pts = []
        ramos(r, x, y, math.radians(90 + r.uniform(-12, 12)), r.uniform(10, 15), 3, 1, longe_tr, pts)
        longe_cp.append(copa(r, pts, r.uniform(5, 7), 5, 2))
    corpo.append(f'<path d="{"".join(longe_tr)}" fill="#5a4a32"/><g fill="#6b7d45">{"".join(longe_cp)}</g>')
    # vereda: faixa verde com um fio de agua, na direita, onde ficam os buritis
    corpo.append(f'<path d="M860 850C960 830 1020 {f(meio(1060) + 8)} 1120 {f(meio(1120) + 4)}Q1360 {f(meio(1360) - 4)} 1610 {f(meio(1600) + 4)}L1610 840Q1250 830 860 850Z" fill="url(#veredaG)"/>')
    corpo.append('<path d="M1000 838Q1180 812 1340 818Q1480 822 1610 806L1610 814Q1480 830 1340 826Q1180 822 1010 842Z" fill="url(#aguaG)" opacity=".85"/>')
    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(campo)))}" fill="url(#campoG)"/>')
    # buritis na vereda: os menores atras, os maiores perto da borda
    corpo.append('<g class="buritis">')
    for k, (x, h, e) in enumerate(((1180, 210, 0.8), (1250, 240, 0.85), (1340, 190, 0.75), (1450, 280, 0.95), (1545, 330, 1.05))):
        corpo.append(f'<g class="b{k % 3}">{buriti(r, x, campo(x) - 6, h, e)}</g>')
    corpo.append("</g>")
    # cupinzeiros no campo
    corpo.append(
        '<g fill="#a5532e">'
        + cupinzeiro(640, campo(640) + 2, 34, 30)
        + cupinzeiro(905, campo(905) + 2, 22, 22)
        + cupinzeiro(1010, campo(1010) + 2, 46, 36)
        + "</g>"
    )
    corpo.append(f'<path d="{caminho(fechar_embaixo(morro(frente)))}" fill="url(#frenteG)"/>')
    # ipe-amarelo florido na esquerda: tronco torto, copa de flor e as flores caindo
    tronco, pontas = [], []
    ramos(r, 205, frente(205) + 8, math.radians(80), 105, 22, 4, tronco, pontas, abre=(0.55, 0.9), encolhe=(0.62, 0.78))
    corpo.append(f'<path d="{"".join(tronco)}" fill="#3b2a1e"/>')
    corpo.append(f'<g class="ipe"><g fill="#e8a91c">{copa(r, pontas, 15, 13, 3)}</g><g fill="#ffd23f">{copa(r, pontas, 11, 11, 3)}</g>'
                 f'<g fill="#fff1a6" fill-opacity=".8">{copa(r, pontas[::2], 4, 9, 2)}</g></g>')
    xs = [p[0] for p in pontas]
    ys = [p[1] for p in pontas]
    flores = []
    for k in range(16):
        x = r.uniform(min(xs), max(xs))
        y = r.uniform(min(ys) + 10, max(ys) + 20)
        flores.append(
            f'<ellipse class="q{k % 3}" style="animation-delay:-{r.uniform(0, 9):.1f}s" cx="{f(x)}" cy="{f(y)}" rx="4.5" ry="2.6"/>'
        )
    corpo.append(f'<g fill="#ffcf2e">{"".join(flores)}</g>')
    # pequizeiro baixo e torcido na direita, na frente
    tronco2, pontas2 = [], []
    ramos(r, 1050, frente(1050) + 6, math.radians(96), 66, 15, 3, tronco2, pontas2, abre=(0.7, 1.05), encolhe=(0.6, 0.75))
    corpo.append(f'<path d="{"".join(tronco2)}" fill="#3a2c20"/>')
    corpo.append(f'<g fill="#3f5f2c">{copa(r, pontas2, 13, 12, 3)}</g><g fill="#5a7d3a">{copa(r, pontas2, 9, 10, 2)}</g>')
    # capim dourado: no campo (miudo) e na frente (alto), so nas laterais
    corpo.append(
        '<g fill="none" stroke-width="1.6" stroke-linecap="round">'
        + capim(r, 560, 1100, campo, 26, 12, 22)
        + capim(r, 0, 620, frente, 34, 30, 62)
        + capim(r, 980, 1600, frente, 34, 30, 62)
        + "</g>"
    )
    # um casal de araras-caninde atravessando o ceu
    corpo.append(
        f'<g class="araras"><g>{arara("#2f7fd0", "#f4c430")}</g>'
        f'<g transform="translate(-70 26) scale(.9)">{arara("#2f7fd0", "#f4c430")}</g></g>'
    )
    # passarinhos ao longe sobre a chapada
    passaro = "M-8 0Q-4-5 0 0Q4-5 8 0"
    bando = "".join(
        f'<g transform="translate({dx} {dy}) scale({s})"><path class="bate" style="animation-delay:-{r.uniform(0, 0.8):.2f}s" d="{passaro}"/></g>'
        for dx, dy, s in ((0, 0, 1), (-30, 12, 0.85), (-58, -6, 0.8), (24, -14, 0.8))
    )
    corpo.append(f'<g class="bando" fill="none" stroke="#5a5550" stroke-width="1.8" stroke-linecap="round">{bando}</g>')

    estilo = (
        ".sol{animation:nasce 90s ease-in-out infinite alternate}"
        "@keyframes nasce{from{transform:translateY(0)}to{transform:translateY(-26px)}}"
        ".nuvens1{animation:nuvem1 80s ease-in-out infinite alternate}"
        ".nuvens2{animation:nuvem2 95s ease-in-out infinite alternate}"
        "@keyframes nuvem1{from{transform:translateX(0)}to{transform:translateX(-50px)}}"
        "@keyframes nuvem2{from{transform:translateX(0)}to{transform:translateX(36px)}}"
        ".c0,.c1,.c2{transform-box:fill-box;transform-origin:50% 100%}"
        ".c0{animation:capim 5s ease-in-out infinite}.c1{animation:capim 6.5s ease-in-out infinite}.c2{animation:capim 4.2s ease-in-out infinite}"
        "@keyframes capim{0%,100%{transform:skewX(0deg)}50%{transform:skewX(-9deg)}}"
        ".b0,.b1,.b2{transform-box:fill-box;transform-origin:50% 100%}"
        ".b0{animation:buriti 9s ease-in-out infinite}.b1{animation:buriti 11s ease-in-out -4s infinite}.b2{animation:buriti 10s ease-in-out -7s infinite}"
        "@keyframes buriti{0%,100%{transform:rotate(0deg)}50%{transform:rotate(.8deg)}}"
        ".ipe{transform-box:fill-box;transform-origin:50% 100%;animation:ipe 8s ease-in-out infinite}"
        "@keyframes ipe{0%,100%{transform:rotate(0deg)}50%{transform:rotate(-.7deg)}}"
        ".q0,.q1,.q2{opacity:0;transform-box:fill-box;transform-origin:center}"
        ".q0{animation:cai 9s linear infinite}.q1{animation:cai 11.5s linear infinite}.q2{animation:cai2 13s linear infinite}"
        "@keyframes cai{0%{opacity:0;transform:translate(0,0) rotate(0deg)}8%{opacity:1}50%{transform:translate(38px,120px) rotate(200deg)}"
        "90%{opacity:.9}100%{opacity:0;transform:translate(70px,250px) rotate(420deg)}}"
        "@keyframes cai2{0%{opacity:0;transform:translate(0,0) rotate(0deg)}8%{opacity:1}50%{transform:translate(-20px,130px) rotate(-180deg)}"
        "90%{opacity:.9}100%{opacity:0;transform:translate(30px,260px) rotate(-380deg)}}"
        ".araras{animation:araras 40s linear infinite}"
        "@keyframes araras{0%{transform:translate(-160px,330px)}100%{transform:translate(1820px,140px)}}"
        ".asa{transform-box:fill-box;transform-origin:50% 100%;animation:asa .7s ease-in-out infinite alternate}"
        "@keyframes asa{from{transform:scaleY(1)}to{transform:scaleY(-.6)}}"
        ".bando{animation:voo 60s linear -20s infinite}"
        "@keyframes voo{0%{transform:translate(1700px,420px)}100%{transform:translate(-200px,360px)}}"
        ".bate{transform-box:fill-box;transform-origin:50% 100%;animation:bate .8s ease-in-out infinite alternate}"
        "@keyframes bate{from{transform:scaleY(1)}to{transform:scaleY(-.45)}}"
        "@media (max-aspect-ratio:5/4){.sol{animation:none;transform:translateX(120px)}}"
        "@media (max-aspect-ratio:4/5){.sol{transform:translateX(330px)}}"
    )
    return svg(estilo, "".join(defs), "".join(corpo))


CENAS = {
    "aurora": (aurora, "Céu noturno com cortinas de aurora boreal verde e violeta ondulando sobre montanhas e pinheiros"),
    "neon": (neon, "Paisagem retrô dos anos 80: sol listrado no horizonte, montanhas com contorno neon, palmeiras e uma grade de luz que corre no chão"),
    "sertao": (sertao, "Sertão ao entardecer: sol se pondo atrás da chapada, mandacarus, um cata-vento girando, pássaros voando e vaga-lumes"),
    "cerrado": (cerrado, "Cerrado de manhã: sol nascendo atrás da chapada, ipê-amarelo florido soltando flores, buritis na vereda, cupinzeiros, capim dourado balançando e araras voando"),
}


def main():
    previas = sys.argv[1] if len(sys.argv) > 1 else None
    linhas = [
        "// cenas.js: as quatro cenas animadas do mod, uma por fundo, em SVG com animação CSS.",
        "// Gerado por fontes/gera_cenas.py; para mudar uma cena, mude o gerador e rode de novo.",
        "export const CENAS = {",
    ]
    for nome, (desenha, alt) in CENAS.items():
        texto = desenha()
        if len(texto) >= LIMITE:
            raise SystemExit(f"{nome}: {len(texto)} caracteres, acima do limite de {LIMITE}")
        print(f"{nome}: {len(texto)} caracteres")
        linhas.append(f"  {nome}: {{ svg: {json.dumps(texto)}, alt: {json.dumps(alt, ensure_ascii=False)} }},")
        if previas:
            os.makedirs(previas, exist_ok=True)
            with open(os.path.join(previas, f"{nome}.svg"), "w", encoding="utf-8", newline="") as arq:
                arq.write(texto)
    linhas.append("}")
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as arq:
        arq.write("\n".join(linhas) + "\n")
    print("gravado", SAIDA)


if __name__ == "__main__":
    main()
