import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import config
from bot.keyboards.inline import (
    SA_CHAT_QUESTIONS,
    SA_CHAT_SUGGESTIONS,
    SA_EDIT_BACK,
    SA_EDIT_CANCEL,
    SA_EDIT_CAT_PREFIX,
    SA_EDIT_FB_PREFIX,
    SA_EDIT_LANG_PREFIX,
    SA_EDIT_SUB_PREFIX,
    SA_ROLE_GRANT,
    SA_ROLE_REVOKE,
    get_chat_type_keyboard,
    get_role_action_keyboard,
    get_sa_categories_keyboard,
    get_sa_feedback_keyboard,
    get_sa_lang_keyboard,
    get_sa_subcategories_keyboard,
)
from bot.utils import env_manager
from bot.utils.content import find_item, get_content
from bot.utils.content_editor import update_message_text

logger = logging.getLogger(__name__)

router = Router()

CHAT_TYPE_LABELS = {
    "questions": "чат активистов РГ (вопросы)",
    "suggestions": "чат руководителей (предложения)",
}

FEEDBACK_CATEGORY_ID = "8"


class ChatStates(StatesGroup):
    waiting_chat_type = State()
    waiting_chat_id = State()


class AdminRoleStates(StatesGroup):
    waiting_user_id = State()
    waiting_action = State()


class SuperAdminRoleStates(StatesGroup):
    waiting_user_id = State()
    waiting_action = State()


class MessagesStates(StatesGroup):
    choose_lang = State()
    choose_category = State()
    choose_target = State()
    enter_text = State()


def _user_id(event: Message | CallbackQuery) -> int | None:
    return event.from_user.id if event.from_user else None


def _parse_user_id(raw: str) -> int | None:
    text = (raw or "").strip()
    if not text.isdigit():
        return None
    value = int(text)
    return value if value > 0 else None


async def _require_super_admin(event: Message | CallbackQuery) -> bool:
    if config.is_super_admin(_user_id(event)):
        return True
    if isinstance(event, CallbackQuery):
        await event.answer("Нет прав супер-админа.", show_alert=True)
    else:
        await event.answer("У вас нет прав супер-админа на эту команду.")
    return False


# --- /chat : смена чата вопросов/предложений ---


@router.message(Command("chat"))
async def cmd_chat(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    await state.clear()
    await state.set_state(ChatStates.waiting_chat_type)
    await message.answer(
        "🔧 Смена ID чата\n\n"
        "Шаг 1 из 2 — выбери, ID какого чата нужно поменять:\n"
        "• «Вопросы» уходят в чат активистов РГ\n"
        "• «Предложения» уходят в чат руководителей",
        reply_markup=get_chat_type_keyboard(),
    )


@router.callback_query(
    ChatStates.waiting_chat_type,
    F.data.in_({SA_CHAT_QUESTIONS, SA_CHAT_SUGGESTIONS}),
)
async def on_chat_type_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    chat_type = (
        "questions" if callback.data == SA_CHAT_QUESTIONS else "suggestions"
    )
    await state.update_data(chat_type=chat_type)
    await state.set_state(ChatStates.waiting_chat_id)
    await callback.answer()
    await callback.message.answer(
        f"Шаг 2 из 2 — отправь новый ID для {CHAT_TYPE_LABELS[chat_type]}.\n\n"
        "Это просто целое число, например: <code>-1001234567890</code>"
    )


@router.message(ChatStates.waiting_chat_id, F.text)
async def on_chat_id(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    text = (message.text or "").strip().replace(" ", "")
    try:
        chat_id = int(text)
    except ValueError:
        await message.answer(
            "❌ Это не число. Отправь целое число — ID чата (например, <code>-1001234567890</code>):"
        )
        return

    data = await state.get_data()
    chat_type = data.get("chat_type", "questions")

    if chat_type == "questions":
        env_manager.set_env_value("QUESTIONS_CHAT_ID", str(chat_id))
        config.set_questions_chat_id(chat_id)
    else:
        env_manager.set_env_value("SUGGESTIONS_CHAT_ID", str(chat_id))
        config.set_suggestions_chat_id(chat_id)

    await state.clear()
    await message.answer(
        f"✅ Готово! ID для {CHAT_TYPE_LABELS[chat_type]} обновлён:\n<code>{chat_id}</code>"
    )


# --- /admin : выдача/снятие роли админа + статус для всех ---


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    user_id = _user_id(message)

    if not config.is_super_admin(user_id):
        status_text = "✅ да" if config.is_admin(user_id) else "❌ нет"
        await message.answer(
            f"Твой Telegram ID: <code>{user_id}</code>\n"
            f"Статус админа: {status_text}\n\n"
            "Если ты админ, используй /answer чтобы ответить на вопрос."
        )
        return

    await state.clear()
    await state.set_state(AdminRoleStates.waiting_user_id)
    await message.answer(
        "🔧 Изменение роли админа\n\n"
        "Шаг 1 из 2 — отправь ID пользователя, которому нужно выдать или забрать роль админа.\n\n"
        "Это просто число — Telegram ID пользователя (например, <code>123456789</code>)."
    )


@router.message(AdminRoleStates.waiting_user_id, F.text)
async def on_admin_user_id(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    user_id = _parse_user_id(message.text or "")
    if user_id is None:
        await message.answer(
            "❌ Это не число. Отправь целое положительное число — Telegram ID пользователя:"
        )
        return
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminRoleStates.waiting_action)
    await message.answer(
        f"Шаг 2 из 2 — выбери действие для пользователя <code>{user_id}</code>:",
        reply_markup=get_role_action_keyboard(),
    )


@router.callback_query(
    AdminRoleStates.waiting_action,
    F.data.in_({SA_ROLE_GRANT, SA_ROLE_REVOKE}),
)
async def on_admin_role_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    data = await state.get_data()
    user_id = data.get("target_user_id")
    if not isinstance(user_id, int):
        await state.clear()
        await callback.answer("Контекст потерян. Начни команду заново.", show_alert=True)
        return

    grant = callback.data == SA_ROLE_GRANT
    if grant:
        config.add_admin_id(user_id)
        env_manager.add_to_list_env("ADMIN_IDS", user_id)
        result_text = f"Пользователю <code>{user_id}</code> выдана роль админа."
    else:
        config.remove_admin_id(user_id)
        env_manager.remove_from_list_env("ADMIN_IDS", user_id)
        result_text = f"У пользователя <code>{user_id}</code> роль админа удалена."

    await state.clear()
    await callback.answer()
    await callback.message.answer(result_text)


# --- /super_admin : выдача/снятие роли супер-админа ---


@router.message(Command("super_admin"))
async def cmd_super_admin(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    await state.clear()
    await state.set_state(SuperAdminRoleStates.waiting_user_id)
    await message.answer(
        "🔧 Изменение роли супер-админа\n\n"
        "Шаг 1 из 2 — отправь ID пользователя, которому нужно выдать или забрать роль супер-админа.\n\n"
        "Это просто число — Telegram ID пользователя (например, <code>123456789</code>)."
    )


@router.message(SuperAdminRoleStates.waiting_user_id, F.text)
async def on_super_admin_user_id(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    user_id = _parse_user_id(message.text or "")
    if user_id is None:
        await message.answer(
            "❌ Это не число. Отправь целое положительное число — Telegram ID пользователя:"
        )
        return
    await state.update_data(target_user_id=user_id)
    await state.set_state(SuperAdminRoleStates.waiting_action)
    await message.answer(
        f"Шаг 2 из 2 — выбери действие для пользователя <code>{user_id}</code>:",
        reply_markup=get_role_action_keyboard(),
    )


@router.callback_query(
    SuperAdminRoleStates.waiting_action,
    F.data.in_({SA_ROLE_GRANT, SA_ROLE_REVOKE}),
)
async def on_super_admin_role_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    caller_id = _user_id(callback)
    data = await state.get_data()
    user_id = data.get("target_user_id")
    if not isinstance(user_id, int):
        await state.clear()
        await callback.answer("Контекст потерян. Начни команду заново.", show_alert=True)
        return

    grant = callback.data == SA_ROLE_GRANT
    if not grant and user_id == caller_id:
        await callback.answer("Нельзя снять роль супер-админа с самого себя!", show_alert=True)
        return

    if grant:
        config.add_super_admin_id(user_id)
        env_manager.add_to_list_env("SUPER_ADMIN_IDS", user_id)
        result_text = f"Пользователю <code>{user_id}</code> выдана роль супер-админа."
    else:
        config.remove_super_admin_id(user_id)
        env_manager.remove_from_list_env("SUPER_ADMIN_IDS", user_id)
        result_text = f"У пользователя <code>{user_id}</code> роль супер-админа удалена."

    await state.clear()
    await callback.answer()
    await callback.message.answer(result_text)


# --- /messages : редактирование статичных текстов ---


@router.message(Command("messages"))
async def cmd_messages(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    await state.clear()
    await state.set_state(MessagesStates.choose_lang)
    await message.answer(
        "📝 Редактирование текстов бота\n\n"
        "Шаг 1 из 4 — выбери язык сообщения, которое хочешь изменить:",
        reply_markup=get_sa_lang_keyboard(),
    )


@router.callback_query(
    MessagesStates.choose_lang,
    F.data.startswith(SA_EDIT_LANG_PREFIX),
)
async def on_messages_lang(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    lang = callback.data.replace(SA_EDIT_LANG_PREFIX, "", 1)
    await state.update_data(lang=lang)
    await state.set_state(MessagesStates.choose_category)
    content = get_content(lang)
    await callback.answer()
    await callback.message.edit_text(
        "Шаг 2 из 4 — выбери категорию, текст внутри которой нужно изменить:",
        reply_markup=get_sa_categories_keyboard(content["categories"]),
    )


@router.callback_query(
    MessagesStates.choose_category,
    F.data.startswith(SA_EDIT_CAT_PREFIX),
)
async def on_messages_category(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    data = await state.get_data()
    lang = data.get("lang", "ru")

    category_id = callback.data.replace(SA_EDIT_CAT_PREFIX, "", 1)
    await state.update_data(category=category_id, subcategory=None, feedback_type=None)

    content = get_content(lang)
    cat = find_item(content, category_id)
    if cat is None:
        await callback.answer("Категория не найдена.", show_alert=True)
        return

    if category_id == FEEDBACK_CATEGORY_ID:
        await state.set_state(MessagesStates.choose_target)
        await callback.answer()
        await callback.message.edit_text(
            "Шаг 3 из 4 — какой текст подтверждения нужно изменить:",
            reply_markup=get_sa_feedback_keyboard(),
        )
        return

    subs = cat.get("subcategories", [])
    if subs:
        await state.set_state(MessagesStates.choose_target)
        await callback.answer()
        await callback.message.edit_text(
            "Шаг 3 из 4 — выбери ответ, который нужно изменить:",
            reply_markup=get_sa_subcategories_keyboard(subs),
        )
        return

    current = content.get("secret_meme", "")
    await state.set_state(MessagesStates.enter_text)
    await callback.answer()
    await callback.message.edit_text(
        "Шаг 3 из 4 — текст под мемом «Секретной кнопки» будет изменён.\n\n"
        f"📄 Текущий текст:\n{current}\n\n"
        "Шаг 4 из 4 — отправь новый текст (без картинки):"
    )


@router.callback_query(
    MessagesStates.choose_target,
    F.data.startswith(SA_EDIT_FB_PREFIX),
)
async def on_feedback_target(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    data = await state.get_data()
    lang = data.get("lang", "ru")

    feedback_type = callback.data.replace(SA_EDIT_FB_PREFIX, "", 1)
    key = "question_received" if feedback_type == "question" else "suggestion_received"
    label = "подтверждение вопроса" if feedback_type == "question" else "подтверждение предложения"

    content = get_content(lang)
    current = content.get(key, "")

    await state.update_data(feedback_type=feedback_type, subcategory=None)
    await state.set_state(MessagesStates.enter_text)
    await callback.answer()
    await callback.message.edit_text(
        f"Шаг 4 из 4 — текущий текст «{label}» будет заменён.\n\n"
        f"📄 Текущий текст:\n{current}\n\n"
        "Отправь новый текст:"
    )


@router.callback_query(
    MessagesStates.choose_target,
    F.data.startswith(SA_EDIT_SUB_PREFIX),
)
async def on_messages_subcategory(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    data = await state.get_data()
    lang = data.get("lang", "ru")

    sub_id = callback.data.replace(SA_EDIT_SUB_PREFIX, "", 1)
    content = get_content(lang)
    node = find_item(content, sub_id)
    if node is None:
        await callback.answer("Подкатегория не найдена.", show_alert=True)
        return

    await state.update_data(subcategory=sub_id, feedback_type=None)
    await state.set_state(MessagesStates.enter_text)
    await callback.answer()
    await callback.message.edit_text(
        f"Шаг 4 из 4 — ответ для «{node['title']}» будет заменён.\n\n"
        f"📄 Текущий текст:\n{node.get('text', '')}\n\n"
        "Отправь новый текст:"
    )


@router.message(MessagesStates.enter_text, F.text)
async def on_messages_text(message: Message, state: FSMContext) -> None:
    if not await _require_super_admin(message):
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым. Отправь снова:")
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    category = data.get("category")
    subcategory = data.get("subcategory")
    feedback_type = data.get("feedback_type")

    try:
        update_message_text(
            lang,
            text,
            category=category,
            subcategory=subcategory,
            feedback_type=feedback_type,
        )
    except Exception as exc:
        logger.exception("Ошибка сохранения текста в JSON: %s", exc)
        await message.answer("❌ Не удалось сохранить текст. Проверь логи.")
        return

    content = get_content(lang)
    await message.answer("✅ Текст обновлён. Теперь его будут видеть все пользователи.")
    await state.set_state(MessagesStates.choose_category)
    await message.answer(
        "Можешь изменить ещё одну категорию — шаг 2 из 4:",
        reply_markup=get_sa_categories_keyboard(content["categories"]),
    )


# --- Общие: назад и отмена ---


@router.callback_query(F.data == SA_EDIT_BACK)
async def on_edit_back(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    data = await state.get_data()
    lang = data.get("lang", "ru")
    content = get_content(lang)
    await state.set_state(MessagesStates.choose_category)
    await callback.answer()
    await callback.message.edit_text(
        "Шаг 2 из 4 — выбери категорию, текст внутри которой нужно изменить:",
        reply_markup=get_sa_categories_keyboard(content["categories"]),
    )


@router.callback_query(F.data == SA_EDIT_CANCEL)
async def on_edit_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_super_admin(callback):
        return
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("❌ Операция отменена. Ничего не изменено.")