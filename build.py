#!/usr/bin/env python3
"""
Compilatore di regole XPath per LlamaLab Automate.
Legge detection_criteria.json e genera:
- android_ads_skip_watchlist.json
- android_ads_skip_watchlist.hjson

Progettato specificamente per le prestazioni del motore Saxon-HE di Automate.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent


def validate_regex(pattern: str, name: str) -> None:
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Regex non valida in {name}: '{pattern}' -> {e}")


def build_xpath():
    criteria_path = ROOT / "detection_criteria.json"
    with open(criteria_path, "r", encoding="utf-8") as f:
        criteria = json.load(f)

    # 1. Regole per i bottoni di skip / chiusura
    skip_rules = criteria.get("ad_skip_buttons", []) + criteria.get("extra_clickables", [])
    skip_texts = [r["text"] for r in skip_rules if "text" in r]
    skip_ids = [r["id"] for r in skip_rules if "id" in r]

    # 2. Regole per gli indicatori di riproduzione annuncio (audio muting)
    playing_rules = criteria.get("ad_playing_indicators", [])
    playing_texts = [r["text"] for r in playing_rules if "text" in r]
    playing_ids = [r["id"] for r in playing_rules if "id" in r]

    def compile_matcher(texts, ids, clickable=False):
        conds = []
        if clickable:
            # Filtro rapido: in Automate i controlli booleani semplici devono
            # precedere fn:matches per sfruttare il short-circuit evaluation
            conds.append("@android:clickable='true'")
        conds.append("@android:enabled='true'")

        sub_conditions = []
        if texts:
            regex_text = "^(" + "|".join(texts) + ")$"
            validate_regex(regex_text, "text rule")
            sub_conditions.append(
                f'(fn:matches(@android:contentDescription|@android:text[not(../@android:editable=\'true\')], "{regex_text}"))'
            )

        if ids:
            regex_id = "^@(" + "|".join(ids) + ")$"
            validate_regex(regex_id, "id rule")
            sub_conditions.append(f"(fn:matches(@android:id, '{regex_id}'))")

        conds.append("(" + " or ".join(sub_conditions) + ")")
        inner_expr = " and ".join(conds)

        # fn:reverse assicura che Automate riceva il nodo bersaglio come primo elemento,
        # risalendo poi agli antenati per trovare il container cliccabile corretto.
        return f"fn:reverse((.//*[{inner_expr}])[1]/ancestor-or-self::*)"

    skip_xpath = compile_matcher(skip_texts, skip_ids, clickable=True)
    playing_xpath = compile_matcher(playing_texts, playing_ids, clickable=False)

    watchlist = {
        "ad_skip_buttons_xpath": skip_xpath,
        "ad_playing_indicators_xpath": playing_xpath,
        "xpaths_parse_successful": ["true"],
    }

    # Scrittura JSON
    json_path = ROOT / "android_ads_skip_watchlist.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, indent=2, ensure_ascii=False)

    # Scrittura HJSON (Human-friendly JSON supportato dal flusso Automate)
    hjson_content = (
        "{\n"
        "  ad_skip_buttons_xpath: \n"
        "    '''\n"
        f"    {skip_xpath}\n"
        "    ''',\n"
        "  ad_playing_indicators_xpath: \n"
        "    '''\n"
        f"    {playing_xpath}\n"
        "    ''',\n"
        '  xpaths_parse_successful: ["true"]\n'
        "}\n"
    )
    hjson_path = ROOT / "android_ads_skip_watchlist.hjson"
    with open(hjson_path, "w", encoding="utf-8") as f:
        f.write(hjson_content)

    print(f"Compilazione completata con successo:")
    print(f" - {json_path.name} (lunghezza XPath skip: {len(skip_xpath)} caratteri)")
    print(f" - {hjson_path.name} (lunghezza XPath mute: {len(playing_xpath)} caratteri)")
    return watchlist


if __name__ == "__main__":
    build_xpath()
