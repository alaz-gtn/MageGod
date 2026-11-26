"""Dibuja las texturas de los procs del mago (las de Missile Barrage salen de make_lightning.py).

- ring_glow.tga y ring_core.tga: 16 fotogramas (4x4 de 256x128) de un anillo de trazos visto en el
  suelo, girando un octavo de vuelta: con ocho trazos iguales, la vuelta empalma. Clearcasting.
- ring_base.tga: el círculo quieto en el suelo: un círculo fino y cuatro marcas.
- ember_glow.tga y ember_core.tga: 16 fotogramas (4x4 de 64x256) de brasas que suben y titilan; en una
  vuelta cada brasa sube una o dos alturas enteras y titila un número entero de veces. Heating Up.
- frost_glow.tga y frost_core.tga: 16 fotogramas (4x4 de 128x128) de un copo de hielo de seis brazos
  girando un sexto de vuelta: con seis brazos iguales, la vuelta empalma. Fingers of Frost.
- proc_aura.tga: un brillo alargado detrás de cada columna de brasas.
- proc_spot.tga: un brillo redondo para los destellos del anillo y de los copos.

Todo en blanco: el color lo pone el juego (SetVertexColor) y la transparencia es la intensidad.
Uso: python -I make_procs.py <carpeta media del addon>
Necesita: pip install pillow
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 4  # se dibuja grande y se reduce para suavizar bordes
COLS, ROWS = 4, 4
FRAMES = COLS * ROWS

EFW, EFH = 64, 256  # un fotograma de las brasas: estrecho, una columna
FFW = 128  # un fotograma del copo, cuadrado
RFW, RFH = 256, 128  # un fotograma del anillo
SQUASH = 0.38  # un círculo en el suelo, visto desde la cámara: más ancho que alto
RX = 106  # radio del anillo en píxeles finales, a lo ancho


def stretch(img, gain):
    """Sube la intensidad sin pasar de 255"""
    return img.point(lambda v: min(255, int(v * gain)))


def white(alpha):
    img = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    img.putalpha(alpha)
    return img


def brush(d, pts, widths, power):
    """Una línea de grosor variable: tramos cortos con las puntas redondas"""
    fill = int(255 * power)
    for (ax, ay), (bx, by), w in zip(pts, pts[1:], widths):
        if w <= 0.2:
            continue
        d.line((ax, ay, bx, by), fill=fill, width=max(1, round(w)))
        r = w / 2
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=fill)


# ---------------------------------------------------------------- Brasas

def sparks(seed):
    """Las brasas de una columna: dónde, lo largas, lo gruesas, lo rápidas y cómo titilan"""
    rng = random.Random(seed)
    out = []
    for i in range(13):
        out.append(dict(
            x=rng.uniform(-17, 17),
            length=rng.uniform(7, 20),
            width=rng.uniform(2.2, 3.8),
            laps=1 if i % 3 else 2,  # alturas enteras por vuelta: la animación empalma
            phase=rng.uniform(0, 1),
            sway=rng.uniform(2.0, 5.5),
            wobble=rng.uniform(0, math.tau),
            flicker=rng.choice((2, 3, 4)),  # veces por vuelta: también empalma
            flick=rng.uniform(0, math.tau),
            power=rng.uniform(0.6, 1.0),
        ))
    return out


def ember_layer(ss, t, scale, power=1.0):
    """Las brasas en el momento t (0 a 1 de la vuelta), con el grosor por scale"""
    w, h = EFW * SS, EFH * SS
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for s in ss:
        head = ((s["phase"] - s["laps"] * t) % 1.0) * h  # sube: la y baja con el tiempo
        length = s["length"] * SS
        glow = 0.55 + 0.45 * math.sin(math.tau * s["flicker"] * t + s["flick"])
        for shift in (-h, 0, h):  # la que sale por arriba entra por abajo
            top = head + shift
            if top > h or top + length < 0:
                continue
            n = 10
            pts, widths = [], []
            for k in range(n + 1):
                f = k / n
                y = top + f * length
                x = w / 2 + s["x"] * SS + s["sway"] * SS * math.sin(math.tau * 2 * y / h + s["wobble"])
                pts.append((x, y))
                # Una cabeza redonda y una cola corta que se afila
                widths.append(s["width"] * scale * SS * (1 - 0.8 * f))
            brush(d, pts, widths[1:], s["power"] * power * glow)
    return img


def fade_ends(img, low=0.35, high=0.12):
    """Las brasas nacen suaves abajo y se apagan antes de llegar arriba"""
    mask = Image.new("L", (1, img.size[1]))
    for y in range(img.size[1]):
        t = y / (img.size[1] - 1)  # 0 arriba, 1 abajo
        e = min(t / low, (1 - t) / high, 1.0)
        mask.putpixel((0, y), int(255 * max(0.0, e) ** 1.4))
    return ImageChops.multiply(img, mask.resize(img.size))


def ember_frame(ss, t):
    glow = ImageChops.add(stretch(ember_layer(ss, t, 3.4).filter(ImageFilter.GaussianBlur(3.5 * SS)), 2.4),
                          stretch(ember_layer(ss, t, 2.0).filter(ImageFilter.GaussianBlur(1.5 * SS)), 1.4))
    core = ImageChops.add(ember_layer(ss, t, 1.0).filter(ImageFilter.GaussianBlur(0.3 * SS)),
                          ember_layer(ss, t, 1.8, 0.45).filter(ImageFilter.GaussianBlur(0.8 * SS)))
    return [fade_ends(layer).resize((EFW, EFH), Image.LANCZOS) for layer in (glow, core)]


def ember_sheets():
    ss = sparks(5151)
    glow_sheet = Image.new("L", (EFW * COLS, EFH * ROWS), 0)
    core_sheet = Image.new("L", (EFW * COLS, EFH * ROWS), 0)
    for n in range(FRAMES):
        glow, core = ember_frame(ss, n / FRAMES)
        x, y = (n % COLS) * EFW, (n // COLS) * EFH
        glow_sheet.paste(glow, (x, y))
        core_sheet.paste(core, (x, y))
    return white(glow_sheet), white(core_sheet)


# ---------------------------------------------------------------- Copo de hielo

def flake_layer(turn, scale, power=1.0):
    """Un copo de seis brazos, girado turn (0 a 1 de un sexto de vuelta)"""
    c = FFW * SS / 2
    img = Image.new("L", (FFW * SS, FFW * SS), 0)
    d = ImageDraw.Draw(img)
    fill = int(255 * power)
    r = 0.40 * FFW * SS  # largo de cada brazo

    def line(a, r0, r1, w, x0=0.0, y0=0.0):
        ax, ay = c + x0 + r0 * math.cos(a), c + y0 + r0 * math.sin(a)
        bx, by = c + x0 + r1 * math.cos(a), c + y0 + r1 * math.sin(a)
        brush(d, [(ax, ay), (bx, by)], [w], power)

    for i in range(6):
        a = (i + turn) * math.tau / 6 - math.pi / 2
        line(a, 0, r, 2.2 * scale * SS)
        # Dos pares de ramas en V, más cortas hacia la punta
        for at, length in ((0.42, 0.30), (0.70, 0.20)):
            bx, by = at * r * math.cos(a), at * r * math.sin(a)
            for side in (-1, 1):
                line(a + side * math.pi / 3, 0, length * r, 1.6 * scale * SS, bx, by)
        # Una punta de diamante
        tip = r * 1.04
        tx, ty = c + tip * math.cos(a), c + tip * math.sin(a)
        k = 2.6 * scale * SS
        d.polygon([(tx + k * math.cos(a), ty + k * math.sin(a)),
                   (tx + k * 0.6 * math.cos(a + 1.6), ty + k * 0.6 * math.sin(a + 1.6)),
                   (tx - k * math.cos(a), ty - k * math.sin(a)),
                   (tx + k * 0.6 * math.cos(a - 1.6), ty + k * 0.6 * math.sin(a - 1.6))], fill=fill)
    # Un hexágono pequeño en el centro
    hexr = 0.09 * FFW * SS
    pts = [(c + hexr * math.cos((k + turn) * math.tau / 6), c + hexr * math.sin((k + turn) * math.tau / 6))
           for k in range(6)]
    d.polygon(pts, outline=fill, width=max(1, round(1.6 * scale * SS)))
    return img


def flake_frame(turn):
    glow = ImageChops.add(stretch(flake_layer(turn, 3.0).filter(ImageFilter.GaussianBlur(4 * SS)), 2.0),
                          stretch(flake_layer(turn, 1.8).filter(ImageFilter.GaussianBlur(1.4 * SS)), 1.3))
    core = ImageChops.add(flake_layer(turn, 1.0).filter(ImageFilter.GaussianBlur(0.3 * SS)),
                          flake_layer(turn, 1.7, 0.4).filter(ImageFilter.GaussianBlur(0.8 * SS)))
    return [layer.resize((FFW, FFW), Image.LANCZOS) for layer in (glow, core)]


def flake_sheets():
    glow_sheet = Image.new("L", (FFW * COLS, FFW * ROWS), 0)
    core_sheet = Image.new("L", (FFW * COLS, FFW * ROWS), 0)
    for n in range(FRAMES):
        glow, core = flake_frame(n / FRAMES)
        x, y = (n % COLS) * FFW, (n // COLS) * FFW
        glow_sheet.paste(glow, (x, y))
        core_sheet.paste(core, (x, y))
    return white(glow_sheet), white(core_sheet)


# ---------------------------------------------------------------- Anillo

def ground(angle, radius):
    """Un punto del círculo del suelo, visto desde la cámara (y hacia abajo)"""
    return (RFW / 2 + RX * radius * math.cos(angle)) * SS, (RFH / 2 + RX * SQUASH * radius * math.sin(angle)) * SS


def depth(angle):
    """Lo de delante (abajo) un poco más grueso y fuerte que lo de detrás"""
    return 0.78 + 0.22 * (1 + math.sin(angle))


def arc(d, a0, a1, radius, width, power, steps=24):
    pts = [ground(a0 + (a1 - a0) * k / steps, radius) for k in range(steps + 1)]
    mids = [a0 + (a1 - a0) * (k + 0.5) / steps for k in range(steps)]
    widths = [width * SS * depth(a) for a in mids]
    fill_power = power * sum(depth(a) for a in mids) / len(mids) / 1.22
    brush(d, pts, widths, min(1.0, fill_power))


def dashes_layer(turn, scale, power=1.0):
    """Ocho trazos en el borde, girados turn (0 a 1 de un octavo de vuelta)"""
    img = Image.new("L", (RFW * SS, RFH * SS), 0)
    d = ImageDraw.Draw(img)
    step = math.tau / 8
    for i in range(8):
        a0 = i * step + turn * step
        arc(d, a0, a0 + step * 0.55, 1.0, 2.6 * scale, power)
        # Una punta fina detrás de cada trazo, como una estela
        arc(d, a0 - step * 0.16, a0 - step * 0.02, 1.0, 1.1 * scale, power * 0.6, 8)
    return img


def ring_frame(turn):
    glow = ImageChops.add(stretch(dashes_layer(turn, 3.2).filter(ImageFilter.GaussianBlur(4 * SS)), 2.2),
                          stretch(dashes_layer(turn, 1.8).filter(ImageFilter.GaussianBlur(1.4 * SS)), 1.3))
    core = ImageChops.add(dashes_layer(turn, 1.0).filter(ImageFilter.GaussianBlur(0.3 * SS)),
                          dashes_layer(turn, 1.7, 0.4).filter(ImageFilter.GaussianBlur(0.8 * SS)))
    return [layer.resize((RFW, RFH), Image.LANCZOS) for layer in (glow, core)]


def ring_sheets():
    glow_sheet = Image.new("L", (RFW * COLS, RFH * ROWS), 0)
    core_sheet = Image.new("L", (RFW * COLS, RFH * ROWS), 0)
    for n in range(FRAMES):
        glow, core = ring_frame(n / FRAMES)
        x, y = (n % COLS) * RFW, (n // COLS) * RFH
        glow_sheet.paste(glow, (x, y))
        core_sheet.paste(core, (x, y))
    return white(glow_sheet), white(core_sheet)


def ring_base():
    """La mira quieta: un círculo fino por dentro y cuatro marcas que apuntan al centro"""
    def layer(scale, power=1.0):
        img = Image.new("L", (RFW * SS, RFH * SS), 0)
        d = ImageDraw.Draw(img)
        arc(d, 0, math.tau, 0.56, 1.1 * scale, power * 0.8, 120)
        for i in range(4):
            a = i * math.tau / 4
            (ax, ay), (bx, by) = ground(a, 0.66), ground(a, 0.88)
            w = 2.4 * scale * SS * depth(a)
            d.line((ax, ay, bx, by), fill=int(255 * power), width=max(1, round(w)))
            for x, y in ((ax, ay), (bx, by)):
                d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=int(255 * power))
        return img
    glow = stretch(layer(3.0).filter(ImageFilter.GaussianBlur(3.5 * SS)), 1.6)
    core = layer(1.0).filter(ImageFilter.GaussianBlur(0.3 * SS))
    return white(ImageChops.add(glow, core).resize((RFW, RFH), Image.LANCZOS))


# ---------------------------------------------------------------- Brillos

def soft(w, h, sx, sy):
    """Una campana suave que llega a cero en los bordes"""
    alpha = Image.new("L", (w, h))
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            bell = math.exp(-(dx * dx) / sx - (dy * dy) / sy)
            edge = max(0.0, 1 - dx * dx) * max(0.0, 1 - dy * dy)
            alpha.putpixel((x, y), int(255 * bell * edge))
    return white(alpha)


if __name__ == "__main__":
    media = Path(sys.argv[1])
    glow, core = ring_sheets()
    glow.save(media / "ring_glow.tga")
    core.save(media / "ring_core.tga")
    ring_base().save(media / "ring_base.tga")
    glow, core = ember_sheets()
    glow.save(media / "ember_glow.tga")
    core.save(media / "ember_core.tga")
    glow, core = flake_sheets()
    glow.save(media / "frost_glow.tga")
    core.save(media / "frost_core.tga")
    soft(64, 256, 0.16, 0.3).save(media / "proc_aura.tga")
    soft(128, 128, 0.22, 0.22).save(media / "proc_spot.tga")
    print("ring_glow, ring_core, ring_base, ember_glow, ember_core, frost_glow, frost_core, proc_aura, proc_spot")
