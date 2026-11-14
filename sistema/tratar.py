"""Cotton Secrets - tratamento de fotos para Instagram.
Apenas ajustes GLOBAIS (cor, luz, contraste, nitidez) + recorte.
Sem retoque local: faces e corpos nao sao alterados.
Uso: python3 -I tratar.py <foto> <pasta_saida>
"""
import sys, os
import numpy as np
import cv2
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def load(path):
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")

def faces_box(im):
    """Devolve caixa (x0,y0,x1,y1) que contem todas as caras, ou None."""
    small = im.copy(); small.thumbnail((1200, 1200))
    s = im.width / small.width
    g = cv2.cvtColor(np.array(small), cv2.COLOR_RGB2GRAY)
    cc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    f = cc.detectMultiScale(g, 1.1, 6, minSize=(40, 40))
    if len(f) == 0:
        return None
    big = max(w for x, y, w, h in f)
    f = [r for r in f if r[2] >= 0.5 * big]   # ignora falsos positivos pequenos
    x0 = min(x for x, y, w, h in f); y0 = min(y for x, y, w, h in f)
    x1 = max(x + w for x, y, w, h in f); y1 = max(y + h for x, y, w, h in f)
    return [int(v * s) for v in (x0, y0, x1, y1)]

def smart_crop(im, ratio, box):
    """Recorta para ratio (w/h) mantendo as caras com margem de cabeca."""
    W, H = im.size
    if W / H > ratio:   # largo demais -> cortar lados
        cw, ch = int(H * ratio), H
        cx = (box[0] + box[2]) / 2 if box else W / 2
        x = int(min(max(cx - cw / 2, 0), W - cw)); y = 0
    else:               # alto demais -> cortar cima/baixo
        cw, ch = W, int(W / ratio)
        if box:
            head_top = box[1] - (box[3] - box[1]) * 0.9   # espaco acima da cabeca
            y = int(min(max(head_top - ch * 0.06, 0), H - ch))
        else:
            y = (H - ch) // 2
        x = 0
    return im.crop((x, y, x + cw, y + ch))

def grade(im):
    """Look 'warm family': quente, suave, luminoso. Global."""
    a = np.asarray(im).astype(np.float32) / 255.0
    # levantar sombras ligeiramente + curva S suave
    a = a + 0.04 * (1 - a) ** 2
    a = a + 0.06 * (a - 0.5) * (1 - np.abs(2 * a - 1))
    # aquecer: +vermelho/amarelo, -azul (ligeiro)
    a[..., 0] *= 1.025; a[..., 1] *= 1.008; a[..., 2] *= 0.965
    a = np.clip(a, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8))
    im = ImageEnhance.Color(im).enhance(1.04)
    return im

def finish(im, size):
    im = im.resize(size, Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))

def process(path, out):
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    im = load(path)
    box = faces_box(im)
    g = grade(im)
    feed = finish(smart_crop(g, 4 / 5, box), (1080, 1350))
    # versao para faixa de texto (foto um pouco mais baixa: 1080x1110 + faixa 240)
    finish(smart_crop(g, 1080 / 1110, box), (1080, 1110)).save(
        f"{out}/{base}_feedbar.jpg", quality=94)
    if True:   # story: foto inteira (4:5) sobre fundo desfocado -> espaco livre para texto
        bg = smart_crop(g, 9 / 16, box).resize((1080, 1920), Image.LANCZOS)
        bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.85)
        src = g if g.width / g.height > 0.75 else smart_crop(g, 4 / 5, box)
        fg = finish(src, (1080, int(1080 * src.height / src.width)))
        bg.paste(fg, (0, 1920 - fg.height - 60 if fg.height > 1000 else (1920 - fg.height) // 2 + 180))
        story = bg
    else:
        story = finish(smart_crop(g, 9 / 16, box), (1080, 1920))
    feed.save(f"{out}/{base}_feed.jpg", quality=92, optimize=True, progressive=True)
    story.save(f"{out}/{base}_story.jpg", quality=92, optimize=True, progressive=True)
    return base, box

if __name__ == "__main__":
    print(process(sys.argv[1], sys.argv[2]))
