"""Reel 9:16 a partir de fotos (zoom lento + transicoes suaves), sem musica.
Uso: python3 -I reel.py <saida.mp4> "<PT>" "<EN>" foto1 foto2 ...
"""
import sys, os, subprocess, tempfile
sys.path.insert(0, "/home/claude/scripts")
from tratar import load, faces_box, grade, smart_crop, finish
from texto import over
from logo import aplicar as logo_aplicar

out, pt, en, fotos = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
tmp = tempfile.mkdtemp()
frames = []
for i, f in enumerate(fotos):
    im = load(f); box = faces_box(im); g = grade(im)
    fr = finish(smart_crop(g, 9 / 16, box), (1080, 1920))
    p = f"{tmp}/f{i}.jpg"; fr.save(p, quality=93)
    if i == 0:   # gancho de texto no primeiro plano
        over(p, p, pt, en)
    logo_aplicar(p, p, "reel")
    frames.append(p)

D, X = 2.6, 0.5   # duracao por foto, transicao
inputs, filt = [], []
for i, p in enumerate(frames):
    inputs += ["-i", p]
    n = int((D + X) * 30)
    filt.append(f"[{i}:v]scale=1296:2304,zoompan=z='min(1+0.0009*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30,setsar=1[v{i}]")
prev = "v0"; off = D
for i in range(1, len(frames)):
    filt.append(f"[{prev}][v{i}]xfade=transition=fade:duration={X}:offset={off:.2f}[x{i}]")
    prev = f"x{i}"; off += D
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", f"[{prev}]",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(out)
