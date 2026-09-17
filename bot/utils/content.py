import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(lang: str) -> dict:
    file_path = DATA_DIR / f"{lang}.json"
    if not file_path.exists():
        file_path = DATA_DIR / "ru.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_content(lang: str) -> dict:
    return _load_json(lang)


def find_item(content: dict, item_id: str) -> dict | None:
    """Recursively find a category or subcategory of any level by its id."""
    for cat in content.get("categories", []):
        found = _search_in_tree(cat, item_id)
        if found:
            return found
    return None


def _search_in_tree(node: dict, item_id: str) -> dict | None:
    if node.get("id") == item_id:
        return node
    for child in node.get("subcategories", []):
        found = _search_in_tree(child, item_id)
        if found:
            return found
    return None


def get_parent_id(item_id: str) -> str:
    """Parent id of a nested item: '1.1.1' -> '1.1', '1.1' -> '1', '1' -> ''."""
    if "." in item_id:
        return item_id.rsplit(".", 1)[0]
    return ""
