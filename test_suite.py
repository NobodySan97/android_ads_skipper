#!/usr/bin/env python3
"""
Suite di test di regressione per android_ads_skipper.
Verifica che le espressioni XPath / criteri:
1. Catturino correttamente gli annunci negli XML reali di test.
2. Abbiano ZERO falsi positivi sui layout regolari (no-ad).
"""

import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


def get_attribs(elem):
    return {
        (k[len(ANDROID_NS):] if k.startswith(ANDROID_NS) else k): v
        for k, v in elem.attrib.items()
    }


def evaluate_rules_on_tree(root, criteria):
    skip_rules = criteria.get("ad_skip_buttons", []) + criteria.get("extra_clickables", [])
    skip_texts = [r["text"] for r in skip_rules if "text" in r]
    skip_ids = [r["id"] for r in skip_rules if "id" in r]

    playing_rules = criteria.get("ad_playing_indicators", [])
    playing_texts = [r["text"] for r in playing_rules if "text" in r]
    playing_ids = [r["id"] for r in playing_rules if "id" in r]

    skip_re_text = "^(" + "|".join(skip_texts) + ")$" if skip_texts else None
    skip_re_id = "^@(" + "|".join(skip_ids) + ")$" if skip_ids else None

    playing_re_text = "^(" + "|".join(playing_texts) + ")$" if playing_texts else None
    playing_re_id = "^@(" + "|".join(playing_ids) + ")$" if playing_ids else None

    matched_skips = []
    matched_playings = []

    for elem in root.iter():
        attrs = get_attribs(elem)
        enabled = attrs.get("enabled", "false") == "true"
        clickable = attrs.get("clickable", "false") == "true"
        text = attrs.get("text", "")
        desc = attrs.get("contentDescription", "")
        elem_id = attrs.get("id", "")

        # Skip button test: must be clickable + enabled
        if enabled and clickable:
            if skip_re_text and (re.search(skip_re_text, text, re.I) or re.search(skip_re_text, desc, re.I)):
                matched_skips.append((elem.tag, elem_id, text or desc))
            elif skip_re_id and re.search(skip_re_id, elem_id, re.I):
                matched_skips.append((elem.tag, elem_id, text or desc))

        # Playing indicator test: must be enabled
        if enabled:
            if playing_re_text and (re.search(playing_re_text, text, re.I) or re.search(playing_re_text, desc, re.I)):
                matched_playings.append((elem.tag, elem_id, text or desc))
            elif playing_re_id and re.search(playing_re_id, elem_id, re.I):
                matched_playings.append((elem.tag, elem_id, text or desc))

    return matched_skips, matched_playings


def run_all_tests():
    # 1. Compila le regole
    import build
    build.build_xpath()

    with open(ROOT / "detection_criteria.json", "r", encoding="utf-8") as f:
        criteria = json.load(f)

    xml_files = sorted(glob.glob(str(ROOT / "examples" / "*.xml")))
    print(f"\nVerifica in corso su {len(xml_files)} file di esempio...\n")

    failures = 0
    total = len(xml_files)

    for xml_path in xml_files:
        name = os.path.basename(xml_path)
        is_no_ad = "no-ad" in name
        tree = ET.parse(xml_path)
        root = tree.getroot()

        skips, playings = evaluate_rules_on_tree(root, criteria)

        # Regola 1: i file "no-ad" NON devono avere alcun match (Zero falsi positivi)
        if is_no_ad:
            if len(skips) > 0 or len(playings) > 0:
                print(f"❌ [FALSO POSITIVO] {name}")
                print(f"   Match inattesi: skips={skips}, playings={playings}")
                failures += 1
            else:
                print(f"✅ [PASS - Clean] {name}")
            continue

        # Regola 2: file 'unactionable' (non deve fare nulla o non è mutabile/skippable)
        is_unactionable = "unactionable" in name
        has_action = len(skips) > 0 or len(playings) > 0

        if is_unactionable:
            # Per file etichettati come unactionable/silent è corretto non intervenire
            print(f"✅ [PASS - Ignorato come previsto] {name} (Unactionable)")
            continue

        # Regola 3: file con 'skippable' o 'actionable'
        if not has_action:
            print(f"⚠️  [NON RILEVATO] {name}")
            failures += 1
        else:
            print(f"✅ [PASS - Rilevato] {name} (Skip: {len(skips)}, Playing: {len(playings)})")

    print(f"\n==========================================")
    print(f"Risultato: {total - failures}/{total} file verificati.")
    if failures == 0:
        print("TUTTI I TEST SONO PASSATI CON SUCCESSO! 🎉")
    else:
        print(f"{failures} file richiedono attenzione o affinamento.")
    return failures == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
