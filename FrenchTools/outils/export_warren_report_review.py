#!/usr/bin/env python3
"""Export Warren Report XLC text from original and translated USRDIR trees.

Read-only: does not modify BIN files or ISOs.

Usage:
  python export_warren_report_review.py ORIGINAL_USRDIR TRANSLATED_USRDIR OUTPUT_DIR

Exports all XLC resources in 700/1/* (Warren Report entries) into a CSV with
English original and current Spanish paired by resource, row, and text column.
Also exports the related Warren Report help text in 700/0/6 to a second CSV.
Uses xlc_fixed first, with the legacy XLC parser as a fallback.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tree import Game  # type: ignore
from xlc import parse_xlc as parse_xlc_legacy  # type: ignore
from xlc_fixed import parse_xlc as parse_xlc_fixed  # type: ignore
from codec import decode  # type: ignore
from export import norm  # type: ignore

PLACEHOLDER_RE = re.compile(r"\{[^}]*\}")


def leaves_by_path(usrdir: Path):
    game = Game(str(usrdir))
    return {tuple(path): blob for path, blob in game.leaves()}


def parse_string_columns(blob: bytes, path: tuple[int, ...]):
    """Parse XLC and identify pointer columns which contain decodable strings."""
    # Prefer the corrected parser. The legacy parser can reject valid XLC
    # resources outside 700/0/3 (for example Warren Report resource 700/1/5).
    # Keep the legacy parser as a compatibility fallback for unusual files.
    info = None
    parser_errors = []
    for parser_name, parser in (
        ("xlc_fixed", parse_xlc_fixed),
        ("xlc", parse_xlc_legacy),
    ):
        try:
            info = parser(blob)
        except Exception as exc:
            parser_errors.append(f"{parser_name}: {type(exc).__name__}: {exc}")
            info = None
        if info:
            break

    if not info:
        detail = "; ".join(parser_errors) if parser_errors else "ambos parsers devolvieron None"
        raise RuntimeError(f"No se pudo interpretar el XLC {path} ({detail})")

    cols = info.get("cols")
    if not isinstance(cols, dict):
        raise RuntimeError(f"El parser no devolvió columnas para {path}")

    # xlc_fixed supplies validated string-pointer columns. The legacy parser
    # may not include this field, so retain the generic validation fallback.
    strcols = info.get("strcols")
    if strcols:
        return info, sorted(strcols)

    # Compatibility fallback matching the validation used by xlc_fixed.py.
    hend = info.get("hend")
    if hend is None:
        n, es = info["n"], info["es"]
        hend = 16 + n * es

    valid_cols = []
    for col, values in cols.items():
        nonzero = {v for v in values if v}
        if not nonzero:
            continue
        valid = all(
            hend <= v < len(blob)
            and (v == hend or blob[v - 1] == 0 or blob[v] == 0)
            for v in nonzero
        )
        if not valid:
            continue
        try:
            for off in nonzero:
                decode(blob, off)
        except Exception:
            continue
        valid_cols.append(col)

    if not valid_cols:
        raise RuntimeError(f"No se detectaron columnas de texto en {path}")
    return info, sorted(valid_cols)


def cell_text(blob: bytes, info: dict, col: int, row: int) -> str:
    off = info["cols"][col][row]
    if not off:
        return ""
    decoded, _ = decode(blob, off)
    # Keep exactly the normalized body used by apply_fixed.py's key function.
    return norm(decoded)[2]


def placeholder_status(english: str, spanish: str) -> str:
    en = sorted(PLACEHOLDER_RE.findall(english))
    es = sorted(PLACEHOLDER_RE.findall(spanish))
    return "COINCIDEN" if en == es else "REVISAR"


def export_group(original: dict, translated: dict, paths: list[tuple[int, ...]], out_path: Path):
    fields = [
        "recurso", "fila_xlc", "columna_xlc", "ingles_original", "espanol_actual",
        "caracteres_ingles", "caracteres_espanol", "marcadores", "estado"
    ]
    rows = []
    resource_stats = Counter()

    for path in sorted(paths):
        if path not in translated:
            raise RuntimeError(
                f"Falta el recurso {path} en el USRDIR traducido. No se generó el CSV."
            )
        orig_blob = original[path]
        tr_blob = translated[path]
        orig_info, orig_cols = parse_string_columns(orig_blob, path)
        tr_info, tr_cols = parse_string_columns(tr_blob, path)

        if orig_info["n"] != tr_info["n"] or orig_info["es"] != tr_info["es"]:
            raise RuntimeError(
                f"Estructura XLC distinta en {path}: original n/es="
                f"{orig_info['n']}/{orig_info['es']}, traducido="
                f"{tr_info['n']}/{tr_info['es']}"
            )
        if orig_cols != tr_cols:
            raise RuntimeError(
                f"Columnas de texto distintas en {path}: original={orig_cols}, traducido={tr_cols}"
            )

        resource = "/".join(map(str, path))
        for col in orig_cols:
            for row in range(orig_info["n"]):
                english = cell_text(orig_blob, orig_info, col, row)
                spanish = cell_text(tr_blob, tr_info, col, row)
                if not english.strip() and not spanish.strip():
                    continue
                if english.strip().lower() == "nothing" and not spanish.strip():
                    continue
                if english.strip().upper() == "NOT USED" and spanish.strip().upper() == "NOT USED":
                    continue
                status = "SIN TRADUCCIÓN" if not spanish.strip() else "CON TEXTO ACTUAL"
                rows.append({
                    "recurso": resource,
                    "fila_xlc": row,
                    "columna_xlc": col,
                    "ingles_original": english,
                    "espanol_actual": spanish,
                    "caracteres_ingles": len(english),
                    "caracteres_espanol": len(spanish),
                    "marcadores": placeholder_status(english, spanish),
                    "estado": status,
                })
                resource_stats[resource] += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    return rows, resource_stats


def main():
    if len(sys.argv) != 4:
        raise SystemExit(
            "Uso: python export_warren_report_review.py ORIGINAL_USRDIR "
            "TRANSLATED_USRDIR OUTPUT_DIR"
        )

    original_dir, translated_dir, output_dir = map(Path, sys.argv[1:])
    for folder in (original_dir, translated_dir):
        if not folder.is_dir():
            raise FileNotFoundError(f"No existe la carpeta: {folder}")

    print("Leyendo USRDIR original...")
    original = leaves_by_path(original_dir)
    print("Leyendo USRDIR traducido...")
    translated = leaves_by_path(translated_dir)

    # Main Warren Report content: all 700/1/* XLC resources.
    main_paths = [
        p for p, b in original.items()
        if p[:2] == (700, 1) and b[:4] == b"xlce"
    ]
    if not main_paths:
        raise RuntimeError("No se encontraron recursos XLC 700/1/* en el USRDIR original")

    main_csv = output_dir / "Warren_Report_Contenido.csv"
    main_rows, main_stats = export_group(original, translated, main_paths, main_csv)

    # Warren Report help entry: 700/0/6. Export only if present in both trees.
    help_path = (700, 0, 6)
    help_csv = None
    help_count = 0
    if help_path in original:
        if help_path not in translated:
            raise RuntimeError("Falta 700/0/6 en el USRDIR traducido")
        help_csv = output_dir / "Warren_Report_Ayuda.csv"
        help_rows, _ = export_group(original, translated, [help_path], help_csv)
        help_count = len(help_rows)

    summary = output_dir / "Warren_Report_Export_Resumen.txt"
    with summary.open("w", encoding="utf-8") as f:
        f.write("EXPORTACIÓN DE WARREN REPORT — SOLO LECTURA\n")
        f.write(f"USRDIR original: {original_dir}\n")
        f.write(f"USRDIR traducido: {translated_dir}\n\n")
        f.write(f"Recursos 700/1 encontrados: {len(main_paths)}\n")
        f.write(f"Celdas de texto exportadas: {len(main_rows)}\n")
        for resource, count in sorted(main_stats.items()):
            f.write(f"  {resource}: {count} celdas\n")
        f.write(f"\nAyuda Warren Report 700/0/6: {help_count} celdas\n")
        f.write("\nNo se modificó ningún BIN ni ISO.\n")

    print("\nEXPORTACIÓN COMPLETADA")
    print("Contenido:", main_csv)
    print("Celdas de contenido:", len(main_rows))
    for resource, count in sorted(main_stats.items()):
        print(f"  {resource}: {count}")
    if help_csv:
        print("Ayuda:", help_csv, f"({help_count} celdas)")
    print("Resumen:", summary)
    print("No se modificó ningún BIN ni ISO.")


if __name__ == "__main__":
    main()
