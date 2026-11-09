import sys
import csv
from pathlib import Path

sys.path.insert(0, r"E:\Tactics ogre\FrenchTools\outils")

from tree import Game
from xlc_fixed import parse_xlc
from codec import decode
from export import norm

BASE = Path(r"E:\Tactics ogre")

catalog = BASE / "USA_Export_Fixed" / "Warren_Report_Biographies.csv"

with catalog.open(encoding="utf-8-sig", newline="") as f:
    biographies = list(csv.DictReader(f))

selected = biographies[10:15]

if len(selected) != 5:
    raise RuntimeError("No se encontraron las cinco biografías.")

def load(folder):
    leaves = dict(Game(str(BASE / folder)).leaves())
    data = leaves[(700, 0, 3)]
    info = parse_xlc(data)

    if info is None:
        raise RuntimeError("No se pudo interpretar people.xlc.")

    return data, info

en, ei = load("OneVision_USRDIR_English")
es, si = load("OneVision_USRDIR_Translated")

if ei["n"] != si["n"] or ei["es"] != si["es"]:
    raise RuntimeError("Las estructuras no coinciden.")

def get_text(data, info, column, row):
    offset = info["cols"][column][row]
    if not offset:
        return ""
    return norm(decode(data, offset)[0])[2]

records = []

for number, item in enumerate(selected, 11):
    row = int(item["row"])

    record = {
        "biography_number": number,
        "resource_row": row,
        "english": get_text(en, ei, 20, row),
        "spanish": get_text(es, si, 20, row)
    }

    if not record["english"] or not record["spanish"]:
        raise RuntimeError(
            f"Biografía {number} vacía. Fila XLC: {row}"
        )

    records.append(record)

output = BASE / "USA_Export_Fixed" / "Biographies_11_15.csv"

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

for item in records:
    print("\n========== BIOGRAFÍA", item["biography_number"], "==========")
    print("\nINGLÉS ORIGINAL:\n" + item["english"])
    print("\nESPAÑOL ACTUAL:\n" + item["spanish"])

print("\nCOMPARACIÓN COMPLETA:", output)
print("BIOGRAFÍAS:", len(records))