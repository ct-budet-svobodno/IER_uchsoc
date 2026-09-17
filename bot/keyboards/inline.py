from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CALLBACK_LANG = "lang_"
CALLBACK_SUBCATEGORY = "subcat_"
CALLBACK_BACK_TO_MENU = "back_to_menu"
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


# --- Супер-админ: callback-константы ---

SA_CHAT_QUESTIONS = "SA_chat_q"
SA_CHAT_SUGGESTIONS = "SA_chat_s"
SA_ROLE_GRANT = "SA_role_grant"
SA_ROLE_REVOKE = "SA_role_revoke"
SA_EDIT_LANG_PREFIX = "SA_lang_"
SA_EDIT_CAT_PREFIX = "SA_cat_"
SA_EDIT_SUB_PREFIX = "SA_sub_"
SA_EDIT_FB_PREFIX = "SA_fb_"
SA_EDIT_BACK = "SA_back"
SA_EDIT_CANCEL = "SA_cancel"


def get_chat_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❓ Чат активистов РГ (вопросы)", callback_data=SA_CHAT_QUESTIONS)],
            [InlineKeyboardButton(text="💬 Чат руководителей (предложения)", callback_data=SA_CHAT_SUGGESTIONS)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=SA_EDIT_CANCEL)],
        ]
    )


def get_role_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выдать роль", callback_data=SA_ROLE_GRANT)],
            [InlineKeyboardButton(text="❌ Забрать роль", callback_data=SA_ROLE_REVOKE)],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=SA_EDIT_CANCEL)],
        ]
    )


def get_sa_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data=f"{SA_EDIT_LANG_PREFIX}ru"),
                InlineKeyboardButton(text="English", callback_data=f"{SA_EDIT_LANG_PREFIX}en"),
            ]
        ]
    )


def get_sa_categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"✏️ {cat['title']}", callback_data=f"{SA_EDIT_CAT_PREFIX}{cat['id']}")]
        for cat in categories
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=SA_EDIT_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sa_subcategories_keyboard(subcategories: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"✏️ {sub['title']}", callback_data=f"{SA_EDIT_SUB_PREFIX}{sub['id']}")]
        for sub in subcategories
    ]
    buttons.append(
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data=SA_EDIT_BACK),
            InlineKeyboardButton(text="❌ Отмена", callback_data=SA_EDIT_CANCEL),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sa_feedback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Подтверждение вопроса", callback_data=f"{SA_EDIT_FB_PREFIX}question")],
            [InlineKeyboardButton(text="✏️ Подтверждение предложения", callback_data=f"{SA_EDIT_FB_PREFIX}suggestion")],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=SA_EDIT_BACK),
                InlineKeyboardButton(text="❌ Отмена", callback_data=SA_EDIT_CANCEL),
            ],
        ]
    )