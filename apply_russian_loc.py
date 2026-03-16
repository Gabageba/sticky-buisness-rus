#!/usr/bin/env python3
"""
Скрипт копирует JSON из containers в новую папку, подставляет русскую локализацию
из extracted (ключ -> русское значение), и для ключа LANGUAGE_ENGLISH в Menus
заменяет все значения языков на 'Русский'.
"""

import json
import shutil
from pathlib import Path

CONTAINERS_DIR = Path(__file__).parent / "containers"
EXTRACTED_DIR = Path(__file__).parent / "extracted"
OUTPUT_DIR = Path(__file__).parent / "containers_ru"

# Имя файла Menus (без пути) для особой обработки LANGUAGE_ENGLISH
MENUS_FILENAME = "Menus-resources.assets-939.json"

RUSSIAN_LANGUAGE_LABEL = "Русский"


def load_extracted_mapping(txt_path: Path) -> dict[str, str]:
    """Читает extracted .txt: строки 'key: value', возвращает словарь key -> value."""
    if not txt_path.exists():
        return {}
    result = {}
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if ": " not in line:
                continue
            idx = line.index(": ")
            key = line[:idx]
            value = line[idx + 2 :]  # после первого ": "
            result[key] = value
    return result


def apply_russian_to_entry(entry: dict, key: str, russian: str | None, is_menus: bool) -> None:
    """
    Модифицирует entry: подставляет русский в первый язык (первый Variant, первый Lang).
    Для Menus и ключа LANGUAGE_ENGLISH — заменяет все значения во всех языках на 'Русский'.
    """
    variants_node = entry.get("Variants")
    if not variants_node:
        return
    m_values = variants_node.get("m_values") or {}
    variants_arr = m_values.get("Array") or []

    if is_menus and key == "LANGUAGE_ENGLISH":
        for variant in variants_arr:
            lang_node = variant.get("Lang")
            if not lang_node:
                continue
            lang_values = lang_node.get("m_values") or {}
            lang_arr = lang_values.get("Array") or []
            for item in lang_arr:
                if "Value" in item:
                    item["Value"] = RUSSIAN_LANGUAGE_LABEL
        return

    if russian is None:
        return
    if not variants_arr:
        return
    first_variant = variants_arr[0]
    lang_node = first_variant.get("Lang")
    if not lang_node:
        return
    lang_values = lang_node.get("m_values") or {}
    lang_arr = lang_values.get("Array") or []
    if not lang_arr:
        return
    lang_arr[0]["Value"] = russian


def process_container(json_path: Path, out_path: Path, extracted_map: dict[str, str], is_menus: bool) -> None:
    """Читает JSON, подставляет русскую локализацию, сохраняет в out_path."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keys_node = data.get("Keys")
    if not keys_node:
        return
    m_values = keys_node.get("m_values") or {}
    entries = m_values.get("Array") or []

    for entry in entries:
        key = entry.get("Key")
        if not key:
            continue
        russian = extracted_map.get(key)
        apply_russian_to_entry(entry, key, russian, is_menus)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    for json_path in sorted(CONTAINERS_DIR.glob("*.json")):
        stem = json_path.stem
        extracted_path = EXTRACTED_DIR / (stem + ".txt")
        out_path = OUTPUT_DIR / json_path.name

        # Копируем файл, затем перезаписываем с заменой локализации
        shutil.copy2(json_path, out_path)

        extracted_map = load_extracted_mapping(extracted_path)
        is_menus = json_path.name == MENUS_FILENAME

        process_container(json_path, out_path, extracted_map, is_menus)
        print(f"  {json_path.name} -> {out_path} (ключей из extracted: {len(extracted_map)})")

    print(f"\nГотово. Результат в: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
