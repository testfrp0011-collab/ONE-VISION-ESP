#!/usr/bin/env python3
"""Build apply_fixed.py translation map for approved Warren Report biographies.

Inputs:
  1) Biographies_1_75.csv from compare_bio_batch.py
  2) Approved_Biographies_1_75.json (the approved revised Spanish text)
  3) Existing corrections.json (preserved and merged)
Output:
  biographies_1_75_translations.json

The map contains keys for BOTH English originals and the current previous-Spanish
strings, so apply_fixed.py can update either form while retaining all other
translated text in OneVision_USRDIR_Translated.
"""
import csv, json, sys, re
from pathlib import Path
from export import norm, key

EXPECTED_XLC = {
 1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,
 11:16,12:17,13:18,14:19,15:20,
 16:21,17:22,18:23,19:24,20:25,21:26,22:27,23:28,24:29,25:30,
 26:31,27:33,28:34,29:35,30:36,31:37,32:39,33:40,34:41,35:42,
 36:45,37:46,38:47,39:48,40:49,41:50,42:51,43:52,44:53,45:54,
 46:55,47:58,48:59,49:60,50:61,51:62,52:64,53:65,54:66,55:67,
 56:68,57:69,58:73,59:74,60:75,61:76,62:77,63:78,64:88,65:89,
 66:90,67:91,68:92,69:93,70:95,71:96,72:97,73:103,74:104,75:105,
}
PLACEHOLDER = re.compile(r'\{[^}]*\}')

def body(text):
    return norm(text)[2]

def add(mapping, k, value, label):
    old = mapping.get(k)
    if old is not None and old != value:
        raise SystemExit(f'KEY COLLISION: {label}; key={k}; existing={old!r}; new={value!r}')
    mapping[k] = value

def main():
    if len(sys.argv) != 5:
        raise SystemExit('Uso: python build_biography_translations.py Biographies_1_75.csv Approved_Biographies_1_75.json corrections.json OUTPUT.json')
    csv_path, revisions_path, base_json_path, out_path = map(Path, sys.argv[1:])
    with open(revisions_path, encoding='utf-8-sig') as f:
        approved = json.load(f)
    items = approved['items']
    if len(items) != 75:
        raise SystemExit(f'Se esperaban 75 revisiones; hay {len(items)}')
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        source_rows = list(csv.DictReader(f))
    src = {int(r['biography_number']): r for r in source_rows}
    missing = sorted(set(range(1,76)) - set(src))
    if missing:
        raise SystemExit(f'Faltan biografías en el CSV fuente: {missing}')
    with open(base_json_path, encoding='utf-8-sig') as f:
        mapping = json.load(f)
    if not isinstance(mapping, dict):
        raise SystemExit('corrections.json debe ser un diccionario JSON')
    before = len(mapping)
    added = 0
    for item in items:
        n = int(item['biography_number'])
        expected_row = EXPECTED_XLC[n]
        item_row = int(item['xlc_row'])
        source_row = int(src[n]['resource_row'])
        if item_row != expected_row or source_row != expected_row:
            raise SystemExit(f'Fila XLC incorrecta en biografía {n}: esperada {expected_row}; JSON={item_row}; CSV={source_row}')
        english = src[n]['biography_english']
        previous = src[n].get('biography_spanish','') or ''
        revised = item['revised_spanish']
        if not english.strip():
            raise SystemExit(f'Inglés original vacío en biografía {n}')
        if not revised.strip():
            raise SystemExit(f'Revisión española vacía en biografía {n}')
        en_body = body(english)
        rev_body = body(revised)
        en_tags = sorted(PLACEHOLDER.findall(en_body))
        rev_tags = sorted(PLACEHOLDER.findall(rev_body))
        if en_tags != rev_tags:
            raise SystemExit(f'PLACEHOLDERS NO COINCIDEN en biografía {n}: EN={en_tags}; ES={rev_tags}')
        add(mapping, key(en_body), revised, f'bio {n} inglés')
        if previous.strip():
            add(mapping, key(body(previous)), revised, f'bio {n} español anterior')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path,'w',encoding='utf-8') as f:
        json.dump(mapping,f,ensure_ascii=False,indent=2)
    print('DICCIONARIO CREADO:',out_path)
    print('Entradas existentes preservadas:',before)
    print('Entradas finales:',len(mapping))
    print('Biografías incorporadas:',len(items))
    print('Claves nuevas aproximadas:',len(mapping)-before)
    print('Se añadieron claves de inglés y, cuando existe, español anterior.')

if __name__ == '__main__':
    main()
