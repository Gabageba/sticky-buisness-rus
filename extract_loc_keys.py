#!/usr/bin/env python3
"""
Скрипт извлекает из JSON-контейнеров локализации пары:
ключ : английское значение
и сохраняет в .txt файл с тем же именем в папке extracted/
"""

import json
import os
from pathlib import Path

CONTAINERS_DIR = Path(__file__).parent / "containers"
OUTPUT_DIR = Path(__file__).parent / "extracted"


def get_english_value(entry: dict) -> str | None:
    """Достаёт английское значение из записи (первый язык в списке)."""
    try:
        variants = entry.get("Variants") or {}
        m_values = variants.get("m_values") or {}
        arr = m_values.get("Array") or []
        if not arr:
            return None
        first_variant = arr[0]
        lang = first_variant.get("Lang") or {}
        lang_values = lang.get("m_values") or {}
        lang_arr = lang_values.get("Array") or []
        if not lang_arr:
            return None
        return (lang_arr[0].get("Value") or "").strip()
    except (IndexError, KeyError, TypeError):
        return None


def process_file(json_path: Path) -> list[tuple[str, str]]:
    """Читает JSON и возвращает список (ключ, английское значение)."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keys_node = data.get("Keys")
    if not keys_node:
        return []

    m_values = keys_node.get("m_values") or {}
    entries = m_values.get("Array") or []
    result = []

    for entry in entries:
        key = entry.get("Key")
        if not key:
            continue
        value = get_english_value(entry)
        if value is None:
            value = ""
        result.append((key, value))

    return result


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    for json_path in sorted(CONTAINERS_DIR.glob("*.json")):
        pairs = process_file(json_path)
        if not pairs:
            print(f"  [skip] {json_path.name} — нет ключей")
            continue

        out_path = OUTPUT_DIR / (json_path.stem + ".txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for key, value in pairs:
                # Экранируем переводы строк в значении для одной строки на пару
                value_flat = value.replace("\n", " ").replace("\r", "")
                f.write(f"{key}: {value_flat}\n")

        print(f"  {json_path.name} -> {out_path.name} ({len(pairs)} записей)")

    print(f"\nГотово. Файлы в: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
