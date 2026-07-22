import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    CALLBACK_BACK_TO_MENU,
    CALLBACK_SUBCATEGORY,
    get_feedback_keyboard,
    get_subcategories_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.utils.content import get_content, get_subcategory_by_id

logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(None), F.text)
async def handle_main_menu(message: Message, lang: str) -> None:
    content = get_content(lang)
    text = message.text or ""

    for cat in content["categories"]:
        if cat["title"] == text:
            subcategories = cat.get("subcategories", [])
            if subcategories:
                await message.answer(
                    content["choose_subcategory"],
                    reply_markup=get_subcategories_keyboard(subcategories, content["back"]),
                )
            return

    feedback = content.get("feedback", {})
    if feedback.get("title", "") == text:
        await message.answer(
            content["choose_subcategory"],
            reply_markup=get_feedback_keyboard(
                feedback["question"],
                feedback["suggestion"],
                content["back"],
            ),
        )
        return


@router.callback_query(F.data == CALLBACK_BACK_TO_MENU)
async def back_to_main_menu(callback: CallbackQuery, lang: str) -> None:
    content = get_content(lang)
    feedback_title = content.get("feedback", {}).get("title", "")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        content["main_menu_hint"],
        reply_markup=get_main_menu_keyboard(content["categories"], feedback_title),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CALLBACK_SUBCATEGORY))
async def show_subcategory_text(callback: CallbackQuery, lang: str) -> None:
    content = get_content(lang)
    sub_id = (callback.data or "").replace(CALLBACK_SUBCATEGORY, "", 1)

    for cat in content["categories"]:
        sub = get_subcategory_by_id(content, cat["id"], sub_id)
        if sub:
            await callback.message.edit_text(
                f"<b>{sub['title']}</b>\n\n{sub['text']}",
            )
            feedback_title = content.get("feedback", {}).get("title", "")
            await callback.message.answer(
                content["main_menu_hint"],
                reply_markup=get_main_menu_keyboard(content["categories"], feedback_title),
            )
            await callback.answer()
            return

    await callback.answer("\u0418\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u044F \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u0430", show_alert=True)
