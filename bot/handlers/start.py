import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.database.dao import get_user_language, upsert_user
from bot.keyboards.inline import CALLBACK_LANG, get_language_keyboard
from bot.keyboards.reply import get_main_menu_keyboard
from bot.utils.content import get_content

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    existing_lang = await get_user_language(user_id) if user_id else None

    if existing_lang:
        content = get_content(existing_lang)
        await message.answer(
            content["welcome"],
            reply_markup=get_main_menu_keyboard(content["categories"], content.get("feedback", {}).get("title", "")),
        )
    else:
        await message.answer(
            "\u0412\u044B\u0431\u0435\u0440\u0438 \u044F\u0437\u044B\u043A\n\nChoose your language",
            reply_markup=get_language_keyboard(),
        )


@router.callback_query(F.data.startswith(CALLBACK_LANG))
async def choose_language(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id if callback.from_user else None
    if not user_id:
        return

    existing_lang = await get_user_language(user_id)
    if existing_lang:
        await callback.answer()
        return

    lang = (callback.data or "").replace(CALLBACK_LANG, "", 1)
    if lang not in ("ru", "en"):
        lang = "ru"

    user = callback.from_user
    if user:
        await upsert_user(
            user.id,
            language=lang,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    content = get_content(lang)
    feedback_title = content.get("feedback", {}).get("title", "")

    await callback.message.edit_text(content["welcome"])
    await callback.message.answer(
        content["main_menu_hint"],
        reply_markup=get_main_menu_keyboard(content["categories"], feedback_title),
    )
    await callback.answer()
