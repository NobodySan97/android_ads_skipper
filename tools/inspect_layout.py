#!/usr/bin/env python3
"""
Tool di ispezione layout per Android / LlamaLab Automate.
Analizza dump XML dell'UI Android per verificare il matching delle regole
o estrarre automaticamente candidati per pulsanti di skip e indicatori pubblicitari.

Uso:
  python tools/inspect_layout.py file.xml
  python tools/inspect_layout.py --adb
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


def get_attribs(elem):
    return {
        (k[len(ANDROID_NS):] if k.startswith(ANDROID_NS) else k): v
        for k, v in elem.attrib.items()
    }


def get_adb_cmd():
    import shutil
    adb_path = shutil.which("adb")
    if adb_path:
        return adb_path
    fallback = Path(r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe")
    if fallback.exists():
        return str(fallback)
    return "adb"


def dump_via_adb():
    adb_cmd = get_adb_cmd()
    print(f"Tentativo di estrazione del layout tramite ADB ({adb_cmd})...")
    try:
        # Verifica dispositivi connessi
        res = subprocess.run([adb_cmd, "devices"], capture_output=True, text=True, check=True)
        lines = [l for l in res.stdout.strip().splitlines() if "\tdevice" in l]
        if not lines:
            print("Nessun dispositivo Android connesso con debug USB autorizzato.")
            sys.exit(1)

        print(f"Dispositivo rilevato: {lines[0].split()[0]}")
        # Esegue il dump
        subprocess.run([adb_cmd, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], check=True)
        dump_proc = subprocess.run([adb_cmd, "shell", "cat", "/sdcard/window_dump.xml"], capture_output=True, text=True, check=True)
        xml_content = dump_proc.stdout
        return ET.fromstring(xml_content)
    except FileNotFoundError:
        print("Errore: 'adb' non è installato o non si trova nel PATH di sistema.")
        sys.exit(1)
    except Exception as e:
        print(f"Errore durante l'estrazione ADB: {e}")
        sys.exit(1)


def inspect_xml(root):
    from test_suite import evaluate_rules_on_tree

    with open(ROOT / "detection_criteria.json", "r", encoding="utf-8") as f:
        criteria = json.load(f)

    skips, playings = evaluate_rules_on_tree(root, criteria)

    print("================ RISULTATO ANALISI ================")
    if skips:
        print(f"🎯 RILEVATO PULSANTE DI SKIP ({len(skips)} elemento/i):")
        for s in skips:
            print(f"   Tag: {s[0]} | ID: {s[1]} | Testo/Desc: {s[2]}")
    else:
        print("⚪ Nessun pulsante di skip rilevato dalle regole correnti.")

    if playings:
        print(f"\n🔊 RILEVATO INDICATORE PUBBLICITARIO ({len(playings)} elemento/i):")
        for p in playings:
            print(f"   Tag: {p[0]} | ID: {p[1]} | Testo/Desc: {p[2]}")
    else:
        print("⚪ Nessun indicatore di riproduzione annuncio rilevato.")

    if not skips and not playings:
        print("\n🔍 CANDIDATI POTENZIALI TROVATI NEL LAYOUT (Elementi cliccabili o con testo):")
        candidates = []
        for elem in root.iter():
            attrs = get_attribs(elem)
            clickable = attrs.get("clickable") == "true"
            enabled = attrs.get("enabled", "true") == "true"
            txt = attrs.get("text", "") or attrs.get("contentDescription", "")
            elem_id = attrs.get("id", "")
            tag_name = elem.tag.split(".")[-1]

            if enabled and (clickable or "ad" in elem_id.lower() or "close" in elem_id.lower()):
                if txt or elem_id:
                    candidates.append((tag_name, elem_id, txt, clickable))

        for c in candidates[:15]:
            print(f"   - <{c[0]}> id='{c[1]}' text='{c[2]}' clickable={c[3]}")

        print("\n💡 Suggerimento:")
        print("   Se un elemento sopra corrisponde alla chiusura dell'annuncio,")
        print("   aggiungi il suo ID o testo in detection_criteria.json ed esegui 'python build.py'.")
    print("====================================================")


def main():
    parser = argparse.ArgumentParser(description="Ispeziona layout Android per identificare annunci e pulsanti skip")
    parser.add_argument("file", nargs="?", help="Percorso del file XML da analizzare")
    parser.add_argument("--adb", action="store_true", help="Cattura il layout in tempo reale dal dispositivo collegato via ADB")
    args = parser.parse_args()

    if args.adb:
        root = dump_via_adb()
    elif args.file:
        if not os.path.exists(args.file):
            print(f"File non trovato: {args.file}")
            sys.exit(1)
        tree = ET.parse(args.file)
        root = tree.getroot()
    else:
        parser.print_help()
        sys.exit(1)

    inspect_xml(root)


if __name__ == "__main__":
    main()
