
from pathlib import Path
import sys

sys.path.insert(
    0,
    r"E:\Tactics ogre\FrenchTools\outils"
)

from xlc_fixed import parse_xlc

root = Path(r"E:\Tactics ogre\Gibbed_Extracted\WarrenReport")
files = sorted(root.rglob("*.xlc"))

print("ARCHIVOS XLC EN WARREN REPORT:", len(files))

for path in files:
    data = path.read_bytes()

    try:
        info = parse_xlc(data)

        if info is None:
            print(
                "\nNO RECONOCIDO:",
                path.relative_to(root),
                "TAMAÑO:",
                len(data)
            )
            continue

        print("\n================================")
        print("ARCHIVO:", path.relative_to(root))
        print("TAMAÑO:", len(data))
        print("FILAS:", info["n"])
        print("COLUMNAS DE TEXTO:", info["strcols"])
        print("TEXTOS:", len(info["slots"]))

        for slot in info["slots"][:4]:
            print("TEXTO:", repr(slot["text"][:180]))

    except Exception as error:
        print("\nERROR:", path.relative_to(root), repr(error))
