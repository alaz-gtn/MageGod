"""Dibuja las texturas de los rayos de Andanada de misiles (Missile Barrage).

- bolts_glow.tga y bolts_core.tga: 8 fotogramas de rayos (4 columnas x 2 filas de 128x256) para una
  animación FlipBook. El brillo y el núcleo van aparte para teñir el brillo con el color que elijas y
  dejar el núcleo casi blanco. Los dos llevan los mismos rayos, así que se animan a la vez.
- aura.tga: un brillo suave y alargado detrás de cada columna de rayos.

Todo en blanco: el color lo pone el juego (SetVertexColor) y la transparencia es la intensidad.
Uso: python -I make_lightning.py <carpeta media del addon>
Necesita: pip install pillow
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

FW, FH = 128, 256  # un fotograma
COLS, ROWS = 4, 2
SS = 4  # se dibuja grande y se reduce para suavizar bordes
W, H = FW * SS, FH * SS
REACH = 40  # lo más que se separa un rayo del centro del fotograma, para que su brillo no se corte

# Cada fotograma: qué rayo (los repetidos son el mismo rayo apagándose) y lo fuerte que se ve.
# Así el rayo parpadea como uno de verdad: un golpe, su resplandor y otro golpe
FRAMES = [(0, 1.0), (0, 0.55), (1, 1.0), (2, 0.9), (2, 0.4), (3, 1.0), (4, 0.85), (4, 0.3)]


def zigzag(rng, a, b, rough, depth):
    """Una línea quebrada de a a b: cada tramo se parte por la mitad y el punto medio se desvía"""
    pts = [a, b]
    for _ in range(depth):
        new = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy) or 1
            off = rng.uniform(-rough, rough)
            new += [((ax + bx) / 2 - dy / length * off, (ay + by) / 2 + dx / length * off), (bx, by)]
        pts = new
        rough *= 0.6
    return pts


def strike(seed):
    """Un rayo de arriba abajo con dos o tres ramas: [(puntos, grosor, fuerza)]"""
    rng = random.Random(seed)
    cx = W / 2
    main = zigzag(rng, (cx + rng.uniform(-10, 10) * SS, -8 * SS),
                  (cx + rng.uniform(-14, 14) * SS, H + 8 * SS), 34 * SS, 7)
    lines = [(main, 1.0, 1.0)]
    for _ in range(rng.choice((2, 3, 3))):
        i = rng.randrange(len(main) // 7, len(main) * 3 // 4)
        sx, sy = main[i]
        side = rng.choice((-1, 1))
        end = (sx + side * rng.uniform(22, 38) * SS, sy + rng.uniform(34, 80) * SS)
        branch = zigzag(rng, (sx, sy), end, 9 * SS, 5)
        lines.append((branch, 0.55, 0.6))
        if rng.random() < 0.5:
            j = rng.randrange(len(branch) // 3, len(branch) - 1)
            bx, by = branch[j]
            twig = zigzag(rng, (bx, by), (bx + side * rng.uniform(8, 16) * SS, by + rng.uniform(14, 30) * SS), 5 * SS, 4)
            lines.append((twig, 0.35, 0.4))
    # Que quepa: se encoge hacia el centro lo que se salga
    far = max(abs(x - cx) for pts, _, _ in lines for x, _ in pts)
    squeeze = min(1.0, REACH * SS / far)
    return [([(cx + (x - cx) * squeeze, y) for x, y in pts], width, power) for pts, width, power in lines]


def stroke(lines, width, blur, power=1.0):
    """Los rayos en gris (L), con el grosor dado en píxeles finales, y difuminados"""
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for pts, w, p in lines:
        d.line(pts, fill=int(255 * p * power), width=max(1, round(width * w * SS)), joint="curve")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur * SS))
    return img


def stretch(img, gain):
    """Sube la intensidad sin pasar de 255"""
    return img.point(lambda v: min(255, int(v * gain)))


def fade_ends(img):
    """Se apaga suave arriba y abajo, para que la columna no acabe en un corte"""
    mask = Image.new("L", (1, FH * SS))
    for y in range(FH * SS):
        t = y / (FH * SS - 1)
        edge = min(t, 1 - t) / 0.14
        mask.putpixel((0, y), int(255 * min(1.0, edge) ** 1.5))
    return ImageChops.multiply(img, mask.resize(img.size))


def frame(lines, strength):
    glow = ImageChops.add(stretch(stroke(lines, 9, 7), 2.6), stretch(stroke(lines, 4, 2.5), 1.6))
    core = ImageChops.add(stroke(lines, 4.5, 0.8, 0.55), stroke(lines, 1.8, 0.4))
    out = []
    for layer in (glow, core):
        layer = fade_ends(layer).point(lambda v: int(v * strength))
        out.append(layer.resize((FW, FH), Image.LANCZOS))
    return out


def white(alpha):
    img = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    img.putalpha(alpha)
    return img


def sheets():
    glow_sheet = Image.new("L", (FW * COLS, FH * ROWS), 0)
    core_sheet = Image.new("L", (FW * COLS, FH * ROWS), 0)
    strikes = {}
    for n, (which, strength) in enumerate(FRAMES):
        lines = strikes.setdefault(which, strike(1000 + which * 17))
        glow, core = frame(lines, strength)
        x, y = (n % COLS) * FW, (n // COLS) * FH
        glow_sheet.paste(glow, (x, y))
        core_sheet.paste(core, (x, y))
    return white(glow_sheet), white(core_sheet)


def aura():
    """Un brillo alargado: campana suave que llega a cero en los bordes"""
    w, h = 128, 256
    alpha = Image.new("L", (w, h))
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            bell = math.exp(-(dx * dx) / 0.16 - (dy * dy) / 0.3)
            edge = max(0.0, 1 - dx * dx) * max(0.0, 1 - dy * dy)
            alpha.putpixel((x, y), int(255 * bell * edge))
    return white(alpha)


if __name__ == "__main__":
    media = Path(sys.argv[1])
    glow, core = sheets()
    glow.save(media / "bolts_glow.tga")
    core.save(media / "bolts_core.tga")
    aura().save(media / "aura.tga")
    print("bolts_glow.tga, bolts_core.tga, aura.tga")
