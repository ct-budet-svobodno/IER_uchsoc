import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.handlers.feedback import start_question, start_suggestion
from bot.keyboards.inline import (
    CALLBACK_BACK_TO_MENU,
    CALLBACK_BACK_TO_SUBCATEGORY,
    CALLBACK_SUBCATEGORY,
    get_subcategories_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.utils.content import DATA_DIR, find_item, get_content, get_parent_id
from bot.utils.memes import get_random_meme

logger = logging.getLogger(__name__)

router = Router()

PHOTOS_DIR = DATA_DIR / "photos"

QUESTION_ID = "8.1"
SUGGESTION_ID = "8.2"
SECRET_BUTTON_ID = "9"


async def _send_menu_hint(message: Message, content: dict) -> None:
    await message.answer(
        content["main_menu_hint"],
        reply_markup=get_main_menu_keyboard(content["categories"]),
    )


async def _show_secret_meme(message: Message, content: dict) -> bool:
    try:
        meme = await get_random_meme(message.bot)
    except FileNotFoundError:
        return False
    if isinstance(meme, str):
        await message.answer_photo(meme, caption=content["secret_meme"])
    else:
        await message.answer_photo(FSInputFile(meme), caption=content["secret_meme"])
    await _send_menu_hint(message, content)
    return True


@router.message(StateFilter(None), F.text)
async def handle_main_menu(message: Message, lang: str) -> None:
    content = get_content(lang)
    text = message.text or ""

    for cat in content["categories"]:
        if cat["title"] == text:
            if cat["id"] == SECRET_BUTTON_ID:
                if not await _show_secret_meme(message, content):
                    await message.answer("Мемы ещё не загружены")
                return
            subcategories = cat.get("subcategories", [])
            if subcategories:
                await message.answer(
                    content["choose_subcategory"],
                    reply_markup=get_subcategories_keyboard(subcategories, content["back"]),
                )
            return


@router.callback_query(F.data == CALLBACK_BACK_TO_MENU)
async def back_to_main_menu(callback: CallbackQuery, lang: str) -> None:
    content = get_content(lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    await _send_menu_hint(callback.message, content)
    await callback.answer()


@router.callback_query(F.data.startswith(CALLBACK_BACK_TO_SUBCATEGORY))
async def back_to_subcategory(callback: CallbackQuery, lang: str) -> None:
    content = get_content(lang)
    parent_id = (callback.data or "").replace(CALLBACK_BACK_TO_SUBCATEGORY, "", 1)
    parent = find_item(content, parent_id)
    if not parent:
        await callback.answer("\u0418\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u044F \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u0430", show_alert=True)
        return

    back_cb = (
        f"{CALLBACK_BACK_TO_SUBCATEGORY}{get_parent_id(parent_id)}"
        if get_parent_id(parent_id)
        else CALLBACK_BACK_TO_MENU
    )
    await callback.message.edit_text(
        content["choose_subcategory"],
        reply_markup=get_subcategories_keyboard(parent.get("subcategories", []), content["back"], back_cb),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CALLBACK_SUBCATEGORY))
async def show_subcategory_text(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    content = get_content(lang)
    sub_id = (callback.data or "").replace(CALLBACK_SUBCATEGORY, "", 1)

    if sub_id == SECRET_BUTTON_ID:
        if not await _show_secret_meme(callback.message, content):
            await callback.answer("Мемы ещё не загружены", show_alert=True)
        else:
            await callback.answer()
        return

    if sub_id == QUESTION_ID:
        await start_question(callback, state, lang)
        return

    if sub_id == SUGGESTION_ID:
        await start_suggestion(callback, state, lang)
        return

    item = find_item(content, sub_id)
    if not item:
        await callback.answer("\u0418\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u044F \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u0430", show_alert=True)
        return

    children = item.get("subcategories", [])
    if children:
        parent_id = get_parent_id(sub_id)
        back_cb = (
            f"{CALLBACK_BACK_TO_SUBCATEGORY}{parent_id}"
            if parent_id
            else CALLBACK_BACK_TO_MENU
        )
        await callback.message.edit_text(
            content["choose_subcategory"],
            reply_markup=get_subcategories_keyboard(children, content["back"], back_cb),
        )
        await callback.answer()
        return

    text = f"<b>{item['title']}</b>\n\n{item.get('text', '')}"
    photo = item.get("photo")
    if photo and (PHOTOS_DIR / photo).exists():
        await callback.message.answer_photo(FSInputFile(PHOTOS_DIR / photo), caption=text)
    else:
        await callback.message.edit_text(text)

    await _send_menu_hint(callback.message, content)
    await callback.answer()