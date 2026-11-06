"""Deterministic illustrated story scenes, no API keys or external assets required."""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SIZE = (720, 1280)
SKY = [(17, 27, 73), (23, 32, 86), (18, 52, 83), (30, 44, 94), (38, 45, 102), (25, 33, 82)]


def generate_scene(index, destination, seed=17):
    """Draw six distinct, coherent illustrated fox-and-star scenes."""
    if index not in range(1, 7):
        raise ValueError("Illustrated sample supports scenes 1 through 6")
    rng = random.Random(seed)
    w, h = SIZE
    image = Image.new("RGB", SIZE)
    pixels = image.load()
    top = SKY[index - 1]
    for y in range(h):
        t = y / h
        for x in range(w):
            pixels[x, y] = tuple(min(255, int(c + t * k)) for c, k in zip(top, (45, 31, 36)))
    d = ImageDraw.Draw(image, "RGBA")
    # Distant stars and a moon, fixed random layout across all scenes.
    for _ in range(110):
        x, y = rng.randrange(25, 695), rng.randrange(35, 700)
        r = rng.choice((1, 2, 3))
        d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 242, 197, rng.randrange(100, 235)))
    d.ellipse((490, 105, 635, 250), fill=(255, 244, 201, 240))
    d.ellipse((540, 88, 666, 228), fill=(*top, 255))
    # Each scene has its own composition.
    hill = [845, 910, 880, 775, 970, 920][index - 1]
    if index == 3:
        for x in (30, 145, 590, 695):
            d.rectangle((x-24, 340, x+24, 1120), fill=(36, 43, 67, 255))
            for j in range(4):
                yy = 370 + j * 115
                d.polygon([(x, yy-100), (x-95, yy+90), (x+95, yy+90)], fill=(28, 78, 76, 240))
    if index == 4:
        d.polygon([(0, 1050), (420, 650), (720, 1040)], fill=(43, 78, 101, 255))
    d.ellipse((-200, hill, 930, 1510), fill=(44, 113, 105, 255))
    d.ellipse((-180, hill+90, 890, 1560), fill=(38, 91, 87, 255))
    # Consistent fox silhouette, with deliberate scene-specific position.
    fx, fy = [(350, 810), (300, 860), (370, 875), (385, 740), (270, 900), (355, 860)][index - 1]
    # Tail, body, ears, face, eyes.
    d.ellipse((fx-205, fy+155, fx+10, fy+300), fill=(211, 95, 39, 255))
    d.polygon([(fx-190, fy+235), (fx-250, fy+195), (fx-198, fy+185)], fill=(255, 229, 191, 255))
    d.ellipse((fx-100, fy+110, fx+110, fy+345), fill=(232, 118, 46, 255))
    d.ellipse((fx-52, fy+178, fx+60, fy+338), fill=(255, 220, 175, 255))
    d.polygon([(fx-100, fy+35), (fx-95, fy-100), (fx-14, fy+5)], fill=(224, 108, 40, 255))
    d.polygon([(fx+95, fy+35), (fx+95, fy-100), (fx+14, fy+5)], fill=(224, 108, 40, 255))
    d.polygon([(fx-78, fy+18), (fx-76, fy-60), (fx-25, fy+10)], fill=(248, 174, 141, 255))
    d.polygon([(fx+78, fy+18), (fx+76, fy-60), (fx+25, fy+10)], fill=(248, 174, 141, 255))
    d.ellipse((fx-105, fy-5, fx+105, fy+185), fill=(239, 126, 51, 255))
    d.polygon([(fx-95, fy+95), (fx, fy+195), (fx+95, fy+95)], fill=(255, 223, 186, 255))
    for ex in (fx-40, fx+40):
        d.ellipse((ex-8, fy+62, ex+8, fy+82), fill=(30, 36, 48, 255))
    d.ellipse((fx-11, fy+122, fx+11, fy+135), fill=(35, 36, 42, 255))
    # Star moves from meadow to sky over the story.
    sx, sy = [(490, 970), (510, 820), (500, 780), (540, 600), (405, 340), (440, 215)][index - 1]
    glow = Image.new("RGBA", SIZE)
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse((sx-115, sy-115, sx+115, sy+115), fill=(255, 210, 75, 135))
    glow = glow.filter(ImageFilter.GaussianBlur(65))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    d = ImageDraw.Draw(image, "RGBA")
    points = []
    for k in range(10):
        angle = -math.pi/2 + k*math.pi/5
        radius = 67 if k % 2 == 0 else 28
        points.append((sx + math.cos(angle)*radius, sy + math.sin(angle)*radius))
    d.polygon(points, fill=(255, 223, 102, 255))
    d.line(points + [points[0]], fill=(255, 248, 202, 255), width=5)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(destination)
    return Path(destination)
