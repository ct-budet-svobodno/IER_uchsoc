import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import QUESTIONS_CHAT_ID, SUGGESTIONS_CHAT_ID
from bot.database.dao import create_question, create_suggestion, upsert_user
from bot.keyboards.inline import CALLBACK_FEEDBACK_QUESTION, CALLBACK_FEEDBACK_SUGGESTION
from bot.keyboards.reply import get_main_menu_keyboard
from bot.utils.content import get_content

logger = logging.getLogger(__name__)

router = Router()


class FeedbackStates(StatesGroup):
    waiting_question = State()
    waiting_suggestion = State()


@router.callback_query(F.data == CALLBACK_FEEDBACK_QUESTION)
async def start_question(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    content = get_content(lang)
    await state.set_state(FeedbackStates.waiting_question)
    await state.update_data(lang=lang)
    await callback.message.edit_text(content["ask_question_prompt"])
    await callback.answer()


@router.callback_query(F.data == CALLBACK_FEEDBACK_SUGGESTION)
async def start_suggestion(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    content = get_content(lang)
    await state.set_state(FeedbackStates.waiting_suggestion)
    await state.update_data(lang=lang)
    await callback.message.edit_text(content["ask_suggestion_prompt"])
    await callback.answer()


@router.message(FeedbackStates.waiting_question, F.text)
async def receive_question(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.from_user:
        return

    user = message.from_user
    text = (message.text or "").strip()
    if not text:
        await message.answer("\u0421\u043E\u043E\u0431\u0449\u0435\u043D\u0438\u0435 \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u044B\u043C.")
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    content = get_content(lang)

    await upsert_user(user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)
    question = await create_question(user.id, text, username=f"@{user.username}" if user.username else None)

    user_label = f"@{user.username}" if user.username else f"ID: {user.id}"
    forward_text = content["forwarded_question"].format(question_id=question.id, username=user_label, text=text)

    if QUESTIONS_CHAT_ID:
        try:
            await bot.send_message(chat_id=int(QUESTIONS_CHAT_ID), text=forward_text)
        except Exception as e:
            logger.error("Failed to forward question to chat %s: %s", QUESTIONS_CHAT_ID, e)

    await state.clear()
    await message.answer(
        content["question_received"],
        reply_markup=get_main_menu_keyboard(content["categories"], content.get("feedback", {}).get("title", "")),
    )


@router.message(FeedbackStates.waiting_suggestion, F.text)
async def receive_suggestion(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.from_user:
        return

    user = message.from_user
    text = (message.text or "").strip()
    if not text:
        await message.answer("\u0421\u043E\u043E\u0431\u0449\u0435\u043D\u0438\u0435 \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u044B\u043C.")
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    content = get_content(lang)

    await upsert_user(user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)
    await create_suggestion(user.id, text, username=f"@{user.username}" if user.username else None)

    user_label = f"@{user.username}" if user.username else f"ID: {user.id}"
    forward_text = content["forwarded_suggestion"].format(username=user_label, text=text)

    if SUGGESTIONS_CHAT_ID:
        try:
            await bot.send_message(chat_id=int(SUGGESTIONS_CHAT_ID), text=forward_text)
        except Exception as e:
            logger.error("Failed to forward suggestion to chat %s: %s", SUGGESTIONS_CHAT_ID, e)

    await state.clear()
    await message.answer(
        content["suggestion_received"],
        reply_markup=get_main_menu_keyboard(content["categories"], content.get("feedback", {}).get("title", "")),
    )
