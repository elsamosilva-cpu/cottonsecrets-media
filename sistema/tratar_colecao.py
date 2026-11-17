"""Trata em lote as fotos copiadas e guarda versoes leves no repositorio (colecao/).
Para cada foto: <DSC>_feed.jpg (4:5), <DSC>_story.jpg (9:16 story), <DSC>_reel.jpg (9:16 recorte para Reels).
Apaga o original copiado depois de tratado. Uso: python3 -I tratar_colecao.py <pasta_entrada> <pasta_saida>
"""
import sys, os, glob
sys.path.insert(0, "/home/claude/scripts")
from tratar import load, faces_box, grade, smart_crop, finish
from PIL import Image, ImageEnhance, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
import json
alvo = set(json.load(open("/home/claude/work/restantes.json")))
ok = 0
for f in sorted(glob.glob(os.path.join(src, "DSC*.JPG"))):
    b = os.path.splitext(os.path.basename(f))[0]
    if "Cópia" in b or b.endswith("_1") or b not in alvo:
        continue
    if os.path.exists(f"{dst}/{b}_reel.jpg"):
        os.remove(f); continue
    im = load(f); box = faces_box(im); g = grade(im)
    finish(smart_crop(g, 4 / 5, box), (1080, 1350)).save(f"{dst}/{b}_feed.jpg", quality=88, optimize=True, progressive=True)
    finish(smart_crop(g, 9 / 16, box), (1080, 1920)).save(f"{dst}/{b}_reel.jpg", quality=86, optimize=True, progressive=True)
    bg = smart_crop(g, 9 / 16, box).resize((1080, 1920), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.85)
    s4 = g if g.width / g.height > 0.75 else smart_crop(g, 4 / 5, box)
    fg = finish(s4, (1080, int(1080 * s4.height / s4.width)))
    bg.paste(fg, (0, 1920 - fg.height - 60 if fg.height > 1000 else (1920 - fg.height) // 2 + 180))
    bg.save(f"{dst}/{b}_story.jpg", quality=86, optimize=True, progressive=True)
    os.remove(f); ok += 1
print("tratadas", ok)
