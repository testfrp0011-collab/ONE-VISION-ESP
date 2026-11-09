
import sys
import csv
from pathlib import Path

sys.path.insert(
    0,
    r"E:\Tactics ogre\FrenchTools\outils"
)

from tree import Game
from xlc import parse_xlc
from xlc_fixed import parse_xlc as parse_xlc_fixed
from codec import decode
from export import norm, key

base = Path(r"E:\Tactics ogre")

english_dir = base / "OneVision_USRDIR_English"
spanish_dir = base / "OneVision_USRDIR_Translated"

output = base / "USA_Export_Fixed" / "Bilingual_XLC_Comparison.csv"

english = dict(Game(str(english_dir)).leaves())
spanish = dict(Game(str(spanish_dir)).leaves())

print("ENGLISH RESOURCES:", len(english))
print("SPANISH RESOURCES:", len(spanish))
print("MISSING IN ENGLISH:", len(spanish.keys() - english.keys()))
print("EXTRA IN ENGLISH:", len(english.keys() - spanish.keys()))

records = []
compared_files = 0
compared_slots = 0
skipped_files = 0

for path in sorted(english.keys() & spanish.keys()):
    eb = english[path]
    sb = spanish[path]

    if eb[:4] != b'xlce' or sb[:4] != b'xlce':
        continue

    parser = (
        parse_xlc_fixed
        if path == (700, 0, 3)
        else parse_xlc
    )

    ei = parser(eb)
    si = parser(sb)

    if ei is None or si is None:
        skipped_files += 1
        continue

    compared_files += 1

    if ei["n"] != si["n"] or ei["es"] != si["es"]:
        print("STRUCTURE MISMATCH:", path)
        continue

    columns = sorted(
        set(ei["strcols"]) & set(si["strcols"])
    )

    for col in columns:
        for row in range(ei["n"]):
            eo = ei["cols"][col][row]
            so = si["cols"][col][row]

            if not eo and not so:
                continue

            et_raw = decode(eb, eo)[0] if eo else ""
            st_raw = decode(sb, so)[0] if so else ""

            _, _, et = norm(et_raw)
            _, _, st = norm(st_raw)

            compared_slots += 1

            if et == st:
                continue

            records.append({
                "resource": "/".join(map(str, path)),
                "row": row,
                "column": col,
                "english_key": key(et),
                "english": et,
                "spanish_current": st,
                "english_raw": et_raw,
                "spanish_raw": st_raw
            })

fields = [
    "resource",
    "row",
    "column",
    "english_key",
    "english",
    "spanish_current",
    "english_raw",
    "spanish_raw"
]

with output.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)

print("\n========== COMPARISON RESULTS ==========")
print("XLC FILES COMPARED:", compared_files)
print("XLC FILES SKIPPED:", skipped_files)
print("TEXT SLOTS COMPARED:", compared_slots)
print("DIFFERENT TEXT SLOTS:", len(records))
print("OUTPUT:", output)

print("\n========== WARREN REPORT PEOPLE ==========")

for item in records:
    if item["resource"] == "700/0/3" and item["column"] in (12, 16, 20):
        print("\nROW:", item["row"], "COLUMN:", item["column"])
        print("ENGLISH:", item["english"][:250])
        print("SPANISH:", item["spanish_current"][:250])
