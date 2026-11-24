"""Dibuja el logo de MageGod: el de CurseForge (512x512 PNG) y el icono del minimapa (64x64 TGA).

Un bastón de mago con un orbe arcano en la punta, en diagonal como el arco de HunterGod y el pico
de FarmGod, sobre un fondo arcano con rayos y un aro de escarcha. (Hasta el 2026-11-24 era una gema
de maná, pero se leía como un diamante cualquiera.)
Uso: python -I make_logo.py <logo.png> <icono.tga>
Necesita: pip install pillow
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter

S = 2048  # se dibuja grande y se reduce para suavizar bordes
C = S / 2

ICE = (200, 244, 255, 255)
CYAN = (96, 206, 244, 255)
BLUE = (44, 128, 214, 255)
DEEP = (26, 72, 164, 255)
NIGHT = (16, 40, 110, 255)
SILVER = (214, 236, 248, 255)
SILVER_DARK = (90, 130, 170, 255)
OUTLINE = (8, 12, 30, 255)


def background():
    # Cuadrado redondeado azul noche con un brillo violeta en el centro
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow = Image.new("RGBA", (S, S), (12, 16, 40, 255))
    g = ImageDraw.Draw(glow)
    for i in range(60, 0, -1):
        r = C * 1.45 * i / 60
        t = 1 - i / 60
        col = (int(12 + 58 * t), int(16 + 46 * t), int(40 + 110 * t), 255)
        g.ellipse((C - r, C - r, C + r, C + r), fill=col)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=380, fill=255)
    img.paste(glow, (0, 0), mask)
    return img


def rays(img):
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = 24
    for i in range(n):
        a = 2 * math.pi * i / n
        long = i % 2 == 0
        r0, r1 = 560, 1000 if long else 860
        half = math.radians(3.2 if long else 2.2)
        d.polygon([(C + r0 * math.cos(a - half), C + r0 * math.sin(a - half)),
                   (C + r1 * math.cos(a), C + r1 * math.sin(a)),
                   (C + r0 * math.cos(a + half), C + r0 * math.sin(a + half))],
                  fill=(150, 225, 255, 120 if long else 80))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(3)))


def halo(img):
    d = ImageDraw.Draw(img)
    r = 600
    d.ellipse((C - r - 22, C - r - 22, C + r + 22, C + r + 22), outline=OUTLINE, width=100)
    d.ellipse((C - r, C - r, C + r, C + r), outline=SILVER_DARK, width=56)
    d.ellipse((C - r + 8, C - r + 8, C + r - 8, C + r - 8), outline=SILVER, width=34)


def glow_behind(img):
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((C - 470, C - 470, C + 470, C + 470), fill=(110, 210, 255, 150))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(90)))


STAFF_SILVER_DARK = (120, 150, 180, 255)
WOOD = (122, 74, 40, 255)
WOOD_LIGHT = (164, 108, 62, 255)
CLOTH = (63, 199, 235, 255)  # el azul de mago, #3FC7EB


def thick_line(d, a, b, width, colour, edge=34):
    d.line([a, b], fill=OUTLINE, width=width + edge)
    for p in (a, b):
        r = (width + edge) / 2
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=OUTLINE)
    d.line([a, b], fill=colour, width=width)
    for p in (a, b):
        r = width / 2
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=colour)


def along(t, a, b):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


FOOT, TOP = (C - 470, C + 470), (C + 150, C - 150)
L = math.dist(FOOT, TOP)
U = ((TOP[0] - FOOT[0]) / L, (TOP[1] - FOOT[1]) / L)  # a lo largo de la vara
V = (-U[1], U[0])  # de través
ORB = (TOP[0] + U[0] * 200, TOP[1] + U[1] * 200)
ORB_R = 185


def band(d, centre, length, width, colour, edge=22):
    def rect(l, w):
        hl, hw = l / 2, w / 2
        return [(centre[0] + U[0] * a + V[0] * b, centre[1] + U[1] * a + V[1] * b)
                for a, b in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
    d.polygon(rect(length + edge, width + edge), fill=OUTLINE)
    d.polygon(rect(length, width), fill=colour)


def staff(img):
    d = ImageDraw.Draw(img)
    thick_line(d, FOOT, TOP, 112, WOOD)
    d.line([along(0.03, FOOT, TOP), along(0.97, FOOT, TOP)], fill=WOOD_LIGHT, width=26)
    # Dos vendas finas de tela azul en la empuñadura
    for t in (0.36, 0.47):
        band(d, along(t, FOOT, TOP), 44, 150, CLOTH)
    # La abrazadera de plata bajo el orbe: un collar y una copa que se abre hacia él
    band(d, along(0.97, FOOT, TOP), 60, 170, STAFF_SILVER_DARK)
    cup_base = (TOP[0] + U[0] * 20, TOP[1] + U[1] * 20)
    cup_top = (ORB[0] - U[0] * (ORB_R - 40), ORB[1] - U[1] * (ORB_R - 40))
    cup = [(cup_base[0] + V[0] * 80, cup_base[1] + V[1] * 80), (cup_top[0] + V[0] * 170, cup_top[1] + V[1] * 170),
           (cup_top[0] - V[0] * 170, cup_top[1] - V[1] * 170), (cup_base[0] - V[0] * 80, cup_base[1] - V[1] * 80)]
    d.polygon(cup, fill=SILVER, outline=OUTLINE, width=24)


def orb_glow(img):
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((ORB[0] - 360, ORB[1] - 360, ORB[0] + 360, ORB[1] + 360), fill=(160, 120, 255, 160))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(75)))
    d = ImageDraw.Draw(img)
    r = ORB_R
    d.ellipse((ORB[0] - r - 22, ORB[1] - r - 22, ORB[0] + r + 22, ORB[1] + r + 22), fill=OUTLINE)
    for k, col in ((1.0, (96, 64, 210, 255)), (0.86, (134, 100, 245, 255)), (0.64, (150, 205, 255, 255)),
                   (0.36, (238, 250, 255, 255))):
        rr = r * k
        d.ellipse((ORB[0] - rr, ORB[1] - rr, ORB[0] + rr, ORB[1] + rr), fill=col)
    d.ellipse((ORB[0] - r * 0.7, ORB[1] - r * 0.7, ORB[0] - r * 0.3, ORB[1] - r * 0.3), fill=(255, 255, 255, 230))


def sparkle(img, x, y, size):
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    thin = size * 0.18
    d.polygon([(x, y - size), (x + thin, y - thin), (x + size, y), (x + thin, y + thin),
               (x, y + size), (x - thin, y + thin), (x - size, y), (x - thin, y - thin)], fill=(255, 255, 255, 240))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2)))


img = background()
rays(img)
halo(img)
glow_behind(img)
staff(img)
orb_glow(img)
sparkle(img, C - 330, C - 300, 110)
sparkle(img, C + 390, C + 240, 80)
sparkle(img, C - 150, C + 420, 50)
img.resize((512, 512), Image.LANCZOS).save(sys.argv[1])

# Icono del minimapa: el centro del logo en un círculo, para el botón redondo
icon = img.crop((int(C - 760), int(C - 760), int(C + 760), int(C + 760))).resize((64, 64), Image.LANCZOS)
mask = Image.new("L", (256, 256), 0)
ImageDraw.Draw(mask).ellipse((2, 2, 253, 253), fill=255)
alpha = Image.composite(icon.getchannel("A"), Image.new("L", (64, 64), 0), mask.resize((64, 64), Image.LANCZOS))
icon.putalpha(alpha)
icon.save(sys.argv[2])
print("logo ->", sys.argv[1], "| icono ->", sys.argv[2])
