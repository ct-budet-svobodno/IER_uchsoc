from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard(categories: list[dict]) -> ReplyKeyboardMarkup:
    buttons = []
    row = []
    for i, cat in enumerate(categories, start=1):
        row.append(KeyboardButton(text=cat["title"]))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)