
import sys
import csv
from pathlib import Path

sys.path.insert(
    0,
    r"E:\Tactics ogre\FrenchTools\outils"
)

from xlc_fixed import parse_xlc
from codec import decode
from export import norm

source = Path(
    r"E:\Tactics ogre\Gibbed_Extracted"
    r"\WarrenReport\WarrenReport\people.xlc"
)

output = Path(
    r"E:\Tactics ogre\USA_Export_Fixed"
    r"\Warren_Report_Biographies.csv"
)

if not source.exists():
    raise FileNotFoundError(source)

data = source.read_bytes()
info = parse_xlc(data)

if not info:
    raise RuntimeError("No se pudo interpretar people.xlc")

def get_text(column, row):
    offset = info["cols"][column][row]

    if not offset:
        return ""

    decoded, _ = decode(data, offset)
    _, _, body = norm(decoded)
    return body

records = []

for row in range(info["n"]):
    name = get_text(12, row)
    label = get_text(16, row)
    biography = get_text(20, row)

    if biography.strip() and biography.strip().lower() != "nothing":
        records.append({
            "row": row,
            "name": name,
            "label": label,
            "biography": biography
        })

with output.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["row", "name", "label", "biography"]
    )
    writer.writeheader()
    writer.writerows(records)

print("ARCHIVO:", source)
print("FILAS TOTALES:", info["n"])
print("BIOGRAFIAS ENCONTRADAS:", len(records))
print("CSV CREADO:", output)

print("\n========== PRIMERAS 12 BIOGRAFIAS ==========")

for item in records[:12]:
    print("\nFILA:", item["row"])
    print("NOMBRE:", item["name"])
    print("ETIQUETA:", item["label"])
    print("BIOGRAFIA:", item["biography"][:350])
