import sys, csv
from pathlib import Path

sys.path.insert(0, r"E:\Tactics ogre\FrenchTools\outils")

from tree import Game
from xlc_fixed import parse_xlc
from codec import decode
from export import norm

base = Path(r"E:\Tactics ogre")

def load(folder):
    b = dict(Game(str(base / folder)).leaves())[(700, 0, 3)]
    return b, parse_xlc(b)

en, ei = load("OneVision_USRDIR_English")
es, si = load("OneVision_USRDIR_Translated")

if ei["n"] != si["n"]:
    raise ValueError("Las filas no coinciden")

def get(data, info, col, row):
    off = info["cols"][col][row]
    if not off:
        return ""
    return norm(decode(data, off)[0])[2]

rows = []

for r in range(6, 11):
    rows.append({
        "fila": r,
        "nombre_ingles": get(en, ei, 12, r),
        "nombre_espanol": get(es, si, 12, r),
        "edad_ingles": get(en, ei, 16, r),
        "edad_espanol": get(es, si, 16, r),
        "biografia_ingles": get(en, ei, 20, r),
        "biografia_espanol": get(es, si, 20, r)
    })

out = base / "USA_Export_Fixed" / "Biographies_06_10.csv"

with out.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Comparación creada:", out)
print("Biografías completas:", len(rows))
print("No se ha recortado ningún texto.")