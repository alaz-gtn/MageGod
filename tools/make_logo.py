"""Dibuja el logo de MageGod: el de CurseForge (512x512 PNG) y el icono del minimapa (64x64 TGA).

Una gema de maná tallada sobre un fondo arcano, con rayos y un aro de escarcha.
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


def gem(img):
    d = ImageDraw.Draw(img)
    oy = 40  # un poco por debajo del centro, que la punta pesa
    girdle, top, tip = -130 + oy, -400 + oy, 540 + oy
    wide, crown, table = 500, 290, 150

    def p(x, y):
        return (C + x, C + y)

    facets = [
        # Corona: la mesa arriba, más clara, y dos faldones
        ([p(-wide, girdle), p(-crown, top), p(-table, girdle)], CYAN),
        ([p(-crown, top), p(crown, top), p(table, girdle), p(-table, girdle)], ICE),
        ([p(crown, top), p(wide, girdle), p(table, girdle)], BLUE),
        # Pabellón: hacia la punta, más oscuro
        ([p(-wide, girdle), p(-table, girdle), p(0, tip)], BLUE),
        ([p(-table, girdle), p(table, girdle), p(0, tip)], CYAN),
        ([p(table, girdle), p(wide, girdle), p(0, tip)], DEEP),
    ]
    outline = [p(-wide, girdle), p(-crown, top), p(crown, top), p(wide, girdle), p(0, tip)]
    d.polygon(outline, fill=NIGHT, outline=OUTLINE, width=44)
    for points, colour in facets:
        d.polygon(points, fill=colour)
    for points, _ in facets:
        d.line(points + [points[0]], fill=NIGHT, width=12, joint="curve")
    d.line(outline + [outline[0]], fill=OUTLINE, width=36, joint="curve")
    # Un brillo en la mesa
    d.polygon([p(-crown + 60, top + 40), p(-crown + 200, top + 40), p(-table - 10, girdle - 40), p(-table - 110, girdle - 40)],
              fill=(255, 255, 255, 170))


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
gem(img)
sparkle(img, C + 330, C - 330, 120)
sparkle(img, C - 380, C + 260, 80)
sparkle(img, C + 250, C + 360, 55)
img.resize((512, 512), Image.LANCZOS).save(sys.argv[1])

# Icono del minimapa: el centro del logo en un círculo, para el botón redondo
icon = img.crop((int(C - 760), int(C - 760), int(C + 760), int(C + 760))).resize((64, 64), Image.LANCZOS)
mask = Image.new("L", (256, 256), 0)
ImageDraw.Draw(mask).ellipse((2, 2, 253, 253), fill=255)
alpha = Image.composite(icon.getchannel("A"), Image.new("L", (64, 64), 0), mask.resize((64, 64), Image.LANCZOS))
icon.putalpha(alpha)
icon.save(sys.argv[2])
print("logo ->", sys.argv[1], "| icono ->", sys.argv[2])
