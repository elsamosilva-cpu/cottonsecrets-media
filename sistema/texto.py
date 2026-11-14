"""Texto chamativo Cotton Secrets, sem tapar caras nem produto.
feed : <base>_feedbar.jpg (1080x1110) + faixa creme 240px com texto -> 1080x1350
story: <base>_story.jpg (foto sobre fundo desfocado) + texto na zona superior livre
Uso: python3 -I texto.py feed|story <img> <saida> "<PT>" "<EN>"
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

F = "/home/claude/fonts/x/package/files/"
SERIF_I = F + "playfair-display-latin-400-italic.woff"
SERIF_B = F + "playfair-display-latin-700-normal.woff"
CREAM, BROWN, CARAMEL = (246, 239, 228), (74, 52, 38), (160, 118, 82)

def balanced(d, text, font, maxw):
    if d.textlength(text, font=font) <= maxw: return [text]
    w = text.split(); best = None
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        m = max(d.textlength(a, font=font), d.textlength(b, font=font))
        if m <= maxw and (best is None or m < best[0]): best = (m, [a, b])
    return best[1] if best else [text]

def center(d, W, y, t, f, fill):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill)

def feed(img, out, pt, en):
    ph = Image.open(img).convert("RGB")
    W = 1080; im = Image.new("RGB", (W, 1350), CREAM); im.paste(ph, (0, 0))
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(SERIF_I, 50); f2 = ImageFont.truetype(SERIF_I, 30)
    f3 = ImageFont.truetype(SERIF_B, 19)
    l1 = balanced(d, pt, f1, W * 0.88)
    if len(l1) > 1: f1 = ImageFont.truetype(SERIF_I, 42); l1 = balanced(d, pt, f1, W * 0.9)
    y = 1110 + (36 if len(l1) == 1 else 22)
    for t in l1: center(d, W, y, t, f1, BROWN); y += int(f1.size * 1.2)
    y += 4; center(d, W, y, en, f2, CARAMEL); y += 58
    d.line([(W / 2 - 40, y), (W / 2 + 40, y)], fill=CARAMEL, width=1); y += 12
    center(d, W, y, "C O T T O N   S E C R E T S", f3, BROWN)
    im.save(out, quality=92, optimize=True, progressive=True)

def story(img, out, pt, en):
    im = Image.open(img).convert("RGB"); W = im.width
    txt = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    f1 = ImageFont.truetype(SERIF_I, 72); f2 = ImageFont.truetype(SERIF_I, 40)
    f3 = ImageFont.truetype(SERIF_B, 24)
    l1 = balanced(d, pt, f1, W * 0.86); y = 110
    for t in l1: center(d, W, y, t, f1, (255, 250, 242, 255)); y += 88
    y += 14; center(d, W, y, en, f2, (248, 232, 212, 255)); y += 70
    center(d, W, y, "COTTONSECRETS.PT", f3, (255, 250, 242, 235))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste((30, 18, 10, 170), mask=txt.split()[3].filter(ImageFilter.GaussianBlur(7)))
    im = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), sh), txt)
    im.convert("RGB").save(out, quality=92, optimize=True, progressive=True)

def _faces(im):
    """Caras de frente + perfil (ambos os lados); tambem parte superior do corpo se nada for encontrado."""
    import numpy as np, cv2
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY); W = g.shape[1]
    H0 = cv2.data.haarcascades
    found = []
    for name, mn in (("haarcascade_frontalface_default.xml", 6), ("haarcascade_profileface.xml", 9)):
        cc = cv2.CascadeClassifier(H0 + name)
        for flip in (False, True):
            gg = cv2.flip(g, 1) if flip else g
            for x, y, w, h in cc.detectMultiScale(gg, 1.08, mn, minSize=(60, 60)):
                if flip: x = W - x - w
                found.append((int(x), int(y), int(w), int(h)))
    if found:
        big = max(r[2] for r in found)
        return [r for r in found if r[2] >= 0.45 * big]
    cc = cv2.CascadeClassifier(H0 + "haarcascade_upperbody.xml")
    ub = cc.detectMultiScale(g, 1.05, 3, minSize=(200, 200))
    return [(int(x), int(y), int(w), int(h * 0.45)) for x, y, w, h in ub]

def _busy(im, box):
    import numpy as np, cv2
    g = cv2.cvtColor(np.array(im.crop(box)), cv2.COLOR_RGB2GRAY)
    return cv2.Canny(g, 60, 160).mean()

def over(img, out, pt, en):
    """Texto SOBRE a foto, na zona livre (parede/fundo): nunca sobre caras nem corpo."""
    im = Image.open(img).convert("RGB"); W, H = im.size
    fs = _faces(im)
    # mascara aproximada das pessoas: cara + corpo por baixo
    people = [(x - int(w * 0.9), y - int(h * 0.4), x + w + int(w * 0.9), H) for x, y, w, h in fs]
    top_free = min([p[1] for p in people], default=H // 2)
    left_free = min([p[0] for p in people], default=0)
    right_free = W - max([p[2] for p in people], default=W)
    zones = []
    if top_free > 230: zones.append(("top", (0, 0, W, top_free)))
    if left_free > W * 0.42: zones.append(("left", (0, 0, left_free, H)))
    if right_free > W * 0.42: zones.append(("right", (W - right_free, 0, W, H)))
    if not fs:   # sem caras (detalhe): faixa superior ou inferior, a mais limpa
        b = int(H * 0.24)
        zones = [("top", (0, 0, W, b)), ("bottom", (0, H - b, W, H))]
    if not zones: zones = [("top", (0, 0, W, max(top_free, 200)))]
    # escolher a zona mais limpa, preferindo maior
    name, (x0, y0, x1, y1) = min(zones, key=lambda z: _busy(im, z[1]) - 0.00002 * (z[1][2] - z[1][0]) * (z[1][3] - z[1][1]))
    zw = x1 - x0
    d0 = ImageDraw.Draw(im)
    s1 = max(46, min(66, int(zw * 0.075)))
    f1 = ImageFont.truetype(SERIF_I, s1); f2 = ImageFont.truetype(SERIF_I, int(s1 * 0.56))
    f3 = ImageFont.truetype(SERIF_B, max(16, int(s1 * 0.34)))
    maxw = zw * 0.86
    l1 = wrap_lines(d0, pt, f1, maxw); l2 = wrap_lines(d0, en, f2, maxw)
    lh1, lh2 = int(s1 * 1.2), int(f2.size * 1.35)
    block = len(l1) * lh1 + 10 + len(l2) * lh2 + 18 + f3.size
    if name == "top": y = max(40, (y1 - block) // 2 - 10)
    elif name == "bottom": y = H - block - 60
    else: y = int(H * 0.08)
    cx = (x0 + x1) / 2; ytop = y
    txt = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    def ln(t, f, yy, fill):
        d.text((cx - d.textlength(t, font=f) / 2, yy), t, font=f, fill=fill)
    for t in l1: ln(t, f1, y, (255, 250, 242, 255)); y += lh1
    y += 10
    for t in l2: ln(t, f2, y, (250, 236, 216, 255)); y += lh2
    y += 18; ln("COTTONSECRETS.PT", f3, y, (255, 250, 242, 235))
    # veu suave por tras do bloco de texto (legibilidade)
    yb0, yb1 = ytop - 40, y + f3.size + 50
    veil = Image.new("L", im.size, 0); vd = ImageDraw.Draw(veil)
    vd.rectangle([x0, max(0, yb0), x1, yb1], fill=105)
    veil = veil.filter(ImageFilter.GaussianBlur(45))
    base = im.copy(); base.paste(Image.new("RGB", im.size, (45, 30, 18)), (0, 0), veil)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste((35, 22, 12, 200), mask=txt.split()[3].filter(ImageFilter.GaussianBlur(8)))
    res = Image.alpha_composite(Image.alpha_composite(base.convert("RGBA"), sh), txt).convert("RGB")
    res.save(out, quality=92, optimize=True, progressive=True)
    return name

def wrap_lines(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    if len(lines) == 2 and len(lines[1].split()) == 1:   # evitar palavra solta
        lines = balanced(d, text, font, maxw * 1.05)
    return lines

if __name__ == "__main__":
    r = {"feed": feed, "story": story, "over": over}[sys.argv[1]](*sys.argv[2:6])
    if r: print(r)
