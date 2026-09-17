import json

from bot.utils.content import DATA_DIR, find_item


def _file_path(lang: str):
    return DATA_DIR / f"{lang}.json"


def _load(lang: str) -> dict:
    with open(_file_path(lang), "r", encoding="utf-8") as f:
        return json.load(f)


def _save(lang: str, data: dict) -> None:
    with open(_file_path(lang), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_message_text(
    lang: str,
    text: str,
    *,
    category: str | None = None,
    subcategory: str | None = None,
    feedback_type: str | None = None,
) -> None:
    """Сохраняет новый текст в JSON-контент нужного языка."""
    data = _load(lang)

    if feedback_type:
        key = "question_received" if feedback_type == "question" else "suggestion_received"
        data[key] = text
    elif category and subcategory:
        node = find_item(data, subcategory)
        if node is None:
            raise ValueError(f"подкатегория {subcategory} не найдена")
        node["text"] = text
    elif category:
        data["secret_meme"] = text
    else:
        raise ValueError("не указана цель редактирования")

    _save(lang, data)