from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CALLBACK_LANG = "lang_"
CALLBACK_CATEGORY = "cat_"
CALLBACK_SUBCATEGORY = "subcat_"
CALLBACK_BACK_TO_MENU = "back_to_menu"
CALLBACK_BACK_TO_CATEGORIES = "back_to_categories"
CALLBACK_BACK_TO_SUBCATEGORY = "back_to_sub_"


def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="\u0420\u0443\u0441\u0441\u043A\u0438\u0439", callback_data=f"{CALLBACK_LANG}ru"),
                InlineKeyboardButton(text="English", callback_data=f"{CALLBACK_LANG}en"),
            ]
        ]
    )


def get_subcategories_keyboard(
    subcategories: list[dict],
    back_text: str,
    back_callback_data: str = CALLBACK_BACK_TO_MENU,
) -> InlineKeyboardMarkup:
    buttons = []
    for sub in subcategories:
        buttons.append(
            [InlineKeyboardButton(text=sub["title"], callback_data=f"{CALLBACK_SUBCATEGORY}{sub['id']}")]
        )
    buttons.append([InlineKeyboardButton(text=back_text, callback_data=back_callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)