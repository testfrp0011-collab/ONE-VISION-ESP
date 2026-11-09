
import json
import csv
from pathlib import Path

base = Path(r"E:\Tactics ogre")

old_file = base / "USA_Translated_Export" / "units.json"
new_file = base / "USA_Export_Fixed" / "units.json"
csv_file = base / "USA_Translated_Export" / "Existing_Translations.csv"
report_file = base / "USA_Export_Fixed" / "newly_recovered_strings.csv"

for p in (old_file, new_file, csv_file):
    if not p.exists():
        raise FileNotFoundError(f"Falta el archivo: {p}")

with old_file.open(encoding="utf-8") as f:
    old = json.load(f)

with new_file.open(encoding="utf-8") as f:
    new = json.load(f)

with csv_file.open(encoding="utf-8-sig", newline="") as f:
    old_translations = list(csv.DictReader(f))

old_keys = {u["k"] for u in old}
new_keys = {u["k"] for u in new}
csv_keys = {
    r["key"].strip()
    for r in old_translations
    if r.get("key")
}

added = [u for u in new if u["k"] not in old_keys]
matched = [u for u in added if u["k"] in csv_keys]

csv_matches = csv_keys & new_keys
csv_missing = csv_keys - new_keys

fields = [
    "key", "kind", "count", "contexts",
    "source", "in_existing_translations_csv"
]

with report_file.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for u in added:
        writer.writerow({
            "key": u["k"],
            "kind": u.get("kind", ""),
            "count": u.get("n", 0),
            "contexts": " | ".join(u.get("ctx", [])),
            "source": u.get("src", ""),
            "in_existing_translations_csv":
                "YES" if u["k"] in csv_keys else "NO"
        })

print("========== COMPARACION ==========")
print("CATALOGO ANTERIOR:", len(old))
print("CATALOGO NUEVO:", len(new))
print("TEXTOS NUEVOS:", len(added))
print()
print("REGISTROS CSV ANTERIOR:", len(old_translations))
print("CLAVES CSV EN CATALOGO NUEVO:", len(csv_matches))
print("CLAVES CSV NO ENCONTRADAS:", len(csv_missing))
print("TEXTOS NUEVOS YA REGISTRADOS EN CSV:", len(matched))
print("TEXTOS NUEVOS NO REGISTRADOS EN CSV:", len(added) - len(matched))
print()
print("INFORME COMPLETO:", report_file)
print()
print("========== PRIMEROS 30 TEXTOS NUEVOS ==========")

for i, u in enumerate(added[:30], 1):
    src = u.get("src", "").replace("\n", " ")
    print(
        f"{i}. [{u.get('kind')}] "
        f"{u['k']} | {src[:160]!r}"
    )
