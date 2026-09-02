import asyncio
import logging
import shutil

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.config import ADMIN_IDS
from bot.database.dao import (
    answer_question,
    get_all_user_ids,
    get_question_by_id,
    get_user_language,
)
from bot.utils.content import DATA_DIR, get_content
from bot.utils.memes import MEME_IDS_FILE, MEMES_DIR, ensure_meme_ids, reset_meme_cache

logger = logging.getLogger(__name__)

router = Router()


class AnswerStates(StatesGroup):
    waiting_question_id = State()
    waiting_answer_text = State()


class PushStates(StatesGroup):
    waiting_push_text = State()


class SecretStates(StatesGroup):
    collecting = State()


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    is_admin = _is_admin(user_id)
    status_text = "\u2705 \u0434\u0430" if is_admin else "\u274C \u043D\u0435\u0442"
    await message.answer(
        f"\u0422\u0432\u043E\u0439 Telegram ID: <code>{user_id}</code>\n"
        f"\u0421\u0442\u0430\u0442\u0443\u0441 \u0430\u0434\u043C\u0438\u043D\u0430: {status_text}\n\n"
        f"\u0415\u0441\u043B\u0438 \u0442\u044B \u0430\u0434\u043C\u0438\u043D, \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0439 /answer \u0447\u0442\u043E\u0431\u044B \u043E\u0442\u0432\u0435\u0442\u0438\u0442\u044C \u043D\u0430 \u0432\u043E\u043F\u0440\u043E\u0441."
    )


@router.message(Command("answer"))
async def cmd_answer(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    logger.info("cmd_answer called by user %s (admin=%s)", user_id, _is_admin(user_id))
    if not _is_admin(user_id):
        await message.answer("\u0423 \u0432\u0430\u0441 \u043D\u0435\u0442 \u043F\u0440\u0430\u0432 \u043D\u0430 \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u043D\u0438\u0435 \u044D\u0442\u043E\u0439 \u043A\u043E\u043C\u0430\u043D\u0434\u044B.")
        return

    await state.set_state(AnswerStates.waiting_question_id)
    current_state = await state.get_state()
    logger.info("State set to %s", current_state)
    await message.answer(
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 ID \u0432\u043E\u043F\u0440\u043E\u0441\u0430, \u043D\u0430 \u043A\u043E\u0442\u043E\u0440\u044B\u0439 \u0445\u043E\u0442\u0438\u0442\u0435 \u043E\u0442\u0432\u0435\u0442\u0438\u0442\u044C:"
    )


@router.message(AnswerStates.waiting_question_id, F.text)
async def receive_question_id(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    logger.info("receive_question_id called by user %s, text=%s", user_id, message.text)
    if not _is_admin(user_id):
        await state.clear()
        return

    text = (message.text or "").strip()
    try:
        question_id = int(text)
    except ValueError:
        await message.answer("\u041D\u0435\u043A\u043E\u0440\u0440\u0435\u043A\u0442\u043D\u044B\u0439 ID. \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0447\u0438\u0441\u043B\u043E.")
        return

    question = await get_question_by_id(question_id)
    if not question:
        await message.answer(f"\u0412\u043E\u043F\u0440\u043E\u0441 #{question_id} \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D \u0432 \u0431\u0430\u0437\u0435 \u0434\u0430\u043D\u043D\u044B\u0445.")
        return

    if question.is_answered:
        await message.answer(f"\u041D\u0430 \u0432\u043E\u043F\u0440\u043E\u0441 #{question_id} \u0443\u0436\u0435 \u043E\u0442\u0432\u0435\u0447\u0435\u043D\u043E.")
        await state.clear()
        return

    await state.update_data(question_id=question_id)
    await state.set_state(AnswerStates.waiting_answer_text)
    logger.info("State set to waiting_answer_text for question #%s", question_id)
    await message.answer(
        f"\u0412\u043E\u043F\u0440\u043E\u0441 #{question_id} \u043E\u0442 {question.username or question.user_id}:\n\n"
        f"{question.text}\n\n"
        f"\u041D\u0430\u043F\u0438\u0448\u0438\u0442\u0435 \u0442\u0435\u043A\u0441\u0442 \u043E\u0442\u0432\u0435\u0442\u0430:"
    )


@router.message(AnswerStates.waiting_answer_text, F.text)
async def receive_answer_text(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    logger.info("receive_answer_text ENTERED by user %s, text=%s", user_id, (message.text or "")[:50])
    if not _is_admin(user_id):
        logger.warning("receive_answer_text: not admin, clearing state")
        await state.clear()
        return

    answer_text = (message.text or "").strip()
    if not answer_text:
        await message.answer("\u041E\u0442\u0432\u0435\u0442 \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u044B\u043C.")
        return

    data = await state.get_data()
    question_id = data.get("question_id")

    if not question_id:
        await state.clear()
        await message.answer("\u041E\u0448\u0438\u0431\u043A\u0430: ID \u0432\u043E\u043F\u0440\u043E\u0441\u0430 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D \u0432 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0438.")
        return

    question = await answer_question(question_id, answer_text)
    if not question:
        await message.answer(f"\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u043E\u0442\u0432\u0435\u0442\u0438\u0442\u044C \u043D\u0430 \u0432\u043E\u043F\u0440\u043E\u0441 #{question_id}.")
        await state.clear()
        return

    logger.info("Answering question #%s to user %s", question_id, question.user_id)

    bot = message.bot
    delivery_ok = True
    try:
        user_lang = await get_user_language(question.user_id) or "ru"
        content = get_content(user_lang)
        delivery_text = content["answer_delivery"].format(answer=answer_text)
        await bot.send_message(
            chat_id=question.user_id,
            text=delivery_text,
        )
        logger.info("Answer sent successfully to user %s", question.user_id)
    except Exception as e:
        logger.error("Failed to send answer to user %s: %s", question.user_id, e)
        delivery_ok = False

    await state.clear()

    if delivery_ok:
        await message.answer(f"\u041E\u0442\u0432\u0435\u0442 \u043D\u0430 \u0432\u043E\u043F\u0440\u043E\u0441 #{question_id} \u043E\u0442\u043F\u0440\u0430\u0432\u043B\u0435\u043D \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044E \u2705")
    else:
        await message.answer(f"\u041E\u0442\u0432\u0435\u0442 \u0441\u043E\u0445\u0440\u0430\u043D\u0451\u043D, \u043D\u043E \u043D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u0434\u043E\u0441\u0442\u0430\u0432\u0438\u0442\u044C \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u043E\u043B\u044E (\u0432\u043E\u0437\u043C\u043E\u0436\u043D\u043E, \u043E\u043D \u043D\u0435 \u0437\u0430\u043F\u0443\u0441\u043A\u0430\u043B \u0431\u043E\u0442\u0430).")


@router.message(Command("push"))
async def cmd_push(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id):
        await message.answer("\u0423 \u0432\u0430\u0441 \u043D\u0435\u0442 \u043F\u0440\u0430\u0432 \u043D\u0430 \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u043D\u0438\u0435 \u044D\u0442\u043E\u0439 \u043A\u043E\u043C\u0430\u043D\u0434\u044B.")
        return

    await state.set_state(PushStates.waiting_push_text)
    await message.answer(
        "\u041D\u0430\u043F\u0438\u0448\u0438 \u0442\u0435\u043A\u0441\u0442 \u0440\u0430\u0441\u0441\u044B\u043B\u043A\u0438:"
    )


@router.message(PushStates.waiting_push_text, F.text)
async def receive_push_text(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id):
        await state.clear()
        return

    push_text = (message.text or "").strip()
    if not push_text:
        await message.answer("\u0422\u0435\u043A\u0441\u0442 \u0440\u0430\u0441\u0441\u044B\u043B\u043A\u0438 \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u044B\u043C.")
        return

    await state.clear()
    await message.answer("\u041D\u0430\u0447\u0438\u043D\u0430\u044E \u0440\u0430\u0441\u0441\u044B\u043B\u043A\u0443...")

    user_ids = await get_all_user_ids()
    if not user_ids:
        await message.answer("\u0412 \u0431\u0430\u0437\u0435 \u043D\u0435\u0442 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0435\u0439.")
        return

    sent = 0
    failed = 0
    for uid in user_ids:
        while True:
            try:
                await bot.send_message(chat_id=uid, text=push_text, parse_mode=None)
                sent += 1
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except Exception:
                failed += 1
                break
        await asyncio.sleep(0.05)

    await message.answer(
        f"\u0420\u0430\u0441\u0441\u044B\u043B\u043A\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u0430: \u043E\u0442\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u043E {sent}, \u043E\u0448\u0438\u0431\u043E\u043A {failed}."
    )


@router.message(AnswerStates.waiting_question_id)
async def catch_all_question_id_state(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    current_state = await state.get_state()
    logger.warning(
        "UNHANDLED in waiting_question_id: user=%s state=%s has_text=%s",
        user_id, current_state, bool(message.text),
    )


@router.message(AnswerStates.waiting_answer_text)
async def catch_all_answer_state(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    current_state = await state.get_state()
    logger.warning(
        "UNHANDLED in waiting_answer_text: user=%s state=%s has_text=%s text=%s",
        user_id, current_state, bool(message.text), (message.text or "")[:50],
    )


SECRET_TMP_DIR = DATA_DIR / "photos" / "memes_tmp"


@router.message(Command("secret"))
async def cmd_secret(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id):
        await message.answer("\u0423 \u0432\u0430\u0441 \u043D\u0435\u0442 \u043F\u0440\u0430\u0432 \u043D\u0430 \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u043D\u0438\u0435 \u044D\u0442\u043E\u0439 \u043A\u043E\u043C\u0430\u043D\u0434\u044B.")
        return

    SECRET_TMP_DIR.mkdir(parents=True, exist_ok=True)
    for f in SECRET_TMP_DIR.glob("*"):
        f.unlink()

    await state.set_state(SecretStates.collecting)
    count = len(list(MEMES_DIR.glob("*.jpg")))
    await message.answer(
        f"\u0421\u0435\u0439\u0447\u0430\u0441 \u043D\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0435 {count} \u043C\u0435\u043C\u043E\u0432.\n\n"
        "\u041E\u0442\u043F\u0440\u0430\u0432\u043B\u044F\u0439\u0442\u0435 \u0444\u043E\u0442\u043E. \u041A\u043E\u0433\u0434\u0430 \u0437\u0430\u043A\u043E\u043D\u0447\u0438\u0442\u0435 \u2014 \u043D\u0430\u043F\u0438\u0448\u0438\u0442\u0435 \u00ab\u0421\u0442\u043E\u043F\u00bb."
    )


@router.message(SecretStates.collecting, F.photo)
async def collect_photo(message: Message, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    count = len(list(SECRET_TMP_DIR.glob("*.jpg"))) + 1
    dest = SECRET_TMP_DIR / f"photo_{count:04d}.jpg"
    await bot.download_file(file.file_path, dest)
    await message.answer(f"\u0421\u043E\u0445\u0440\u0430\u043D\u0435\u043D\u043E ({count})")


@router.message(SecretStates.collecting, F.text)
async def finish_collecting(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text != "\u0421\u0442\u043E\u043F":
        await message.answer(
            "\u041E\u0442\u043F\u0440\u0430\u0432\u043B\u044F\u0439\u0442\u0435 \u0444\u043E\u0442\u043E \u0438\u043B\u0438 \u043D\u0430\u043F\u0438\u0448\u0438\u0442\u0435 \u00ab\u0421\u0442\u043E\u043F\u00bb."
        )
        return

    new_photos = sorted(SECRET_TMP_DIR.glob("*.jpg"))
    if not new_photos:
        await state.clear()
        await message.answer(
            "\u0424\u043E\u0442\u043E \u043D\u0435 \u0431\u044B\u043B\u043E \u043E\u0442\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u043E. \u0420\u0435\u0436\u0438\u043C \u043E\u0442\u043C\u0435\u043D\u0451\u043D."
        )
        return

    for f in MEMES_DIR.glob("*"):
        f.unlink()

    for i, src in enumerate(new_photos, 1):
        shutil.move(str(src), MEMES_DIR / f"meme_{i:02d}.jpg")

    for f in SECRET_TMP_DIR.glob("*"):
        f.unlink()
    SECRET_TMP_DIR.rmdir()

    if MEME_IDS_FILE.exists():
        MEME_IDS_FILE.unlink()
    reset_meme_cache()

    await state.clear()
    await message.answer(
        f"\u0413\u043E\u0442\u043E\u0432\u043E! \u0421\u0442\u0430\u0440\u044B\u0435 \u043C\u0435\u043C\u044B \u0443\u0434\u0430\u043B\u0435\u043D\u044B, \u0441\u043E\u0445\u0440\u0430\u043D\u0435\u043D\u043E {len(new_photos)} \u043D\u043E\u0432\u044B\u0445."
    )
    asyncio.create_task(ensure_meme_ids(bot))
