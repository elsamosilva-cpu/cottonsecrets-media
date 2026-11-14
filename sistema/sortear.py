"""Sorteia as fotos de uma semana sem repetir (registo em usadas.json).
Uso: python3 -I sortear.py <seed> > semana.json
Estrutura: 7 fotos unicas, 4 carrosseis (4 fotos seguidas da mesma sessao), 2 reels (5 fotos).
"""
import json, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
todas = [f"DSC{n}" for n in open(f"{D}/fotos.txt").read().split()]
usadas = set(json.load(open(f"{D}/usadas.json"))) if os.path.exists(f"{D}/usadas.json") else set()
livres = [f for f in todas if f not in usadas]
rnd = random.Random(int(sys.argv[1]))
escolhidas = set()

def seguidas(k):
    """k fotos livres seguidas (mesmo coordenado / sessao)."""
    for _ in range(500):
        i = rnd.randrange(len(livres) - k)
        grupo = livres[i:i + k]
        if all(g not in escolhidas for g in grupo) and int(grupo[-1][3:]) - int(grupo[0][3:]) <= 12:
            escolhidas.update(grupo); return grupo
    raise SystemExit("Sem fotos suficientes")

def unica():
    for _ in range(500):
        f = rnd.choice(livres)
        if f not in escolhidas: escolhidas.add(f); return f
    raise SystemExit("Sem fotos suficientes")

out = {"carrosseis": [seguidas(4) for _ in range(4)],
       "reels": [seguidas(5) for _ in range(2)],
       "unicas": [unica() for _ in range(7)],
       "livres_restantes": len(livres) - 33}
print(json.dumps(out, indent=1))
