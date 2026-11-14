"""Coloca o logo Cotton Secrets, discreto, num canto livre (sem caras, longe do texto do topo).
Uso: python3 -I logo.py <imagem_entrada> <imagem_saida> [feed|story]
Precisa de /home/claude/scripts/logo_cs.png (logo com fundo transparente).
"""
import sys, os
import numpy as np, cv2
from PIL import Image, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(D, "logo_cs.png")

def preparar_logo(src, dst):
    """Remove o fundo branco do logo original e guarda PNG transparente (cor original)."""
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    dist = 255 - a.min(axis=2)                      # quanto se afasta do branco
    alpha = np.clip(dist * 3.2, 0, 255)
    rgba = np.dstack([a, alpha]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    out = out.crop(out.getbbox())
    out = out.resize((out.width * 4, out.height * 4), Image.LANCZOS)
    out.save(dst)

def _faces(im):
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    res = []
    for name, mn in (("haarcascade_frontalface_default.xml", 6), ("haarcascade_profileface.xml", 9)):
        cc = cv2.CascadeClassifier(cv2.data.haarcascades + name)
        for flip in (False, True):
            gg = cv2.flip(g, 1) if flip else g
            for x, y, w, h in cc.detectMultiScale(gg, 1.08, mn, minSize=(60, 60)):
                if flip: x = g.shape[1] - x - w
                res.append((x, y, w, h))
    return res

def aplicar(src, dst, modo="feed"):
    im = Image.open(src).convert("RGB"); W, H = im.size
    logo = Image.open(LOGO).convert("RGBA")
    lw = int(W * (0.085 if modo == "feed" else 0.075))
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    m = int(W * 0.035)
    # cantos candidatos: em baixo (o texto fica em cima); em story tambem em cima-direita nao
    cands = {"baixo-dir": (W - lw - m, H - logo.height - m), "baixo-esq": (m, H - logo.height - m)}
    if modo == "reel":    # zonas seguras do Reel (fora da interface do Instagram)
        cands = {"topo-esq": (m + 10, 250), "topo-dir": (W - lw - m - 10, 250), "meio-esq": (m + 10, H - 620)}
    if modo == "story":   # zona desfocada entre o texto e a foto (foto 4:5 comeca em y=510)
        cands = {"centro": ((W - lw) // 2, 510 - logo.height - 8)}
    fs = _faces(im)
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    def custo(pos):
        x, y = pos; box = (x - 20, y - 20, x + lw + 20, y + logo.height + 20)
        for fx, fy, fw, fh in fs:
            if not (box[2] < fx or box[0] > fx + fw or box[3] < fy or box[1] > fy + fh): return 1e9
        reg = g[max(0, box[1]):box[3], max(0, box[0]):box[2]]
        return cv2.Canny(reg, 60, 160).mean()
    pos = min(cands.values(), key=custo)
    # halo suave claro por tras para ler em fundos escuros ou estampados
    a = logo.split()[3]
    halo = Image.new("RGBA", logo.size, (255, 250, 242, 0))
    halo.putalpha(a.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.55)))
    logo.putalpha(a.point(lambda v: int(v * 0.92)))
    base = im.convert("RGBA")
    base.alpha_composite(halo, pos); base.alpha_composite(logo, pos)
    base.convert("RGB").save(dst, quality=92, optimize=True, progressive=True)

if __name__ == "__main__":
    if sys.argv[1] == "preparar":
        preparar_logo(sys.argv[2], LOGO); print("logo pronto", LOGO)
    else:
        aplicar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "feed")
