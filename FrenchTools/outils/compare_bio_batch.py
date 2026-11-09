
import sys
import csv
from pathlib import Path

sys.path.insert(0, r"E:\Tactics ogre\FrenchTools\outils")

from tree import Game
from xlc_fixed import parse_xlc
from codec import decode
from export import norm

BASE = Path(r"E:\Tactics ogre")

start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end = int(sys.argv[2]) if len(sys.argv) > 2 else 5

if start < 1 or end < start:
    raise ValueError("Rango de biografías no válido")

source_csv = BASE / "USA_Export_Fixed" / "Warren_Report_Biographies.csv"

with source_csv.open(encoding="utf-8-sig", newline="") as f:
    all_bios = list(csv.DictReader(f))

selected = all_bios[start - 1:end]

if not selected:
    raise RuntimeError("No se encontraron biografías en ese rango")

def load(folder):
    leaves = dict(Game(str(BASE / folder)).leaves())
    data = leaves[(700, 0, 3)]
    info = parse_xlc(data)

    if info is None:
        raise RuntimeError("No se pudo interpretar people.xlc")

    return data, info

english, ei = load("OneVision_USRDIR_English")
spanish, si = load("OneVision_USRDIR_Translated")

if ei["n"] != si["n"] or ei["es"] != si["es"]:
    raise RuntimeError("Las estructuras inglesa y española no coinciden")

def get_text(data, info, column, row):
    offset = info["cols"][column][row]

    if not offset:
        return ""

    return norm(decode(data, offset)[0])[2]

records = []

for number, item in enumerate(selected, start):
    row = int(item["row"])

    record = {
        "biography_number": number,
        "resource_row": row,
        "name_english": get_text(english, ei, 12, row),
        "name_spanish": get_text(spanish, si, 12, row),
        "label_english": get_text(english, ei, 16, row),
        "label_spanish": get_text(spanish, si, 16, row),
        "biography_english": get_text(english, ei, 20, row),
        "biography_spanish": get_text(spanish, si, 20, row),
    }

    records.append(record)

output = BASE / "USA_Export_Fixed" / (
    f"Biographies_{start:02d}_{end:02d}.csv"
)

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

for r in records:
    print("\n" + "=" * 70)
    print("BIOGRAFÍA:", r["biography_number"])
    print("FILA REAL XLC:", r["resource_row"])
    print("\nINGLÉS ORIGINAL:")
    print(r["biography_english"])
    print("\nESPAÑOL ACTUAL:")
    print(r["biography_spanish"])

print("\nBIografías encontradas:", len(records))
print("ARCHIVO GUARDADO:", output)
