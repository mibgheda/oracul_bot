import logging
import sqlite3

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from keyboards import (
    BTN_DELETE,
    BTN_HOW_IT_WORKS,
    BTN_MY_SCHEDULE,
    BTN_PREDICTION,
    CB_CONSENT_AGREE,
    CB_CONSENT_DECLINE,
    CB_DELETE_CANCEL,
    CB_DELETE_CONFIRM,
    CB_DISCLAIMER_OK,
    CB_GENDER_FEMALE,
    CB_GENDER_MALE,
    CB_SCHEDULE_DISABLE,
    CB_SCHEDULE_NO,
    CB_SCHEDULE_TIME_MAP,
    CB_SCHEDULE_YES,
    consent_keyboard,
    delete_confirm_keyboard,
    disclaimer_keyboard,
    gender_keyboard,
    main_keyboard,
    schedule_manage_keyboard,
    schedule_question_keyboard,
    schedule_time_keyboard,
)
from threads import format_thread_message, get_random_thread
from utils import can_get_prediction, utc_date_str
from config import PRIVACY_POLICY_URL

logger = logging.getLogger(__name__)

HOW_IT_WORKS_TEXT = (
    "❓ <b>Как это работает</b>\n\n"
    "Каждый день тебе приходит одна <b>нить</b> — небольшой текст с:\n\n"
    "🔹 <b>Метафорой</b> — образ, который резонирует с чем-то внутри\n"
    "🔹 <b>Вопросом к себе</b> — не для ответа вслух, а для паузы\n"
    "🔹 <b>Ритуалом</b> — простое действие на 1–5 минут\n\n"
    "Нити охватывают 7 сфер внутренней жизни:\n"
    "🧶 Тишина · 🔥 Тень · 🌊 Вода\n"
    "🌍 Земля · 💨 Воздух · ⚡ Огонь · ✨ Свет\n\n"
    "Одна нить в день. Можно настроить автоматическую рассылку в удобное время."
)


def _consent_text() -> str:
    return (
        "👁 <b>Оракул Нитей Судьбы</b>\n\n"
        "Для использования бота необходимо дать согласие на обработку персональных данных.\n\n"
        f'Ознакомься с <a href="{PRIVACY_POLICY_URL}">Политикой конфиденциальности</a> '
        "и подтверди согласие."
    )


def _disclaimer_text() -> str:
    return (
        "⚠️ <b>Важное предупреждение</b>\n\n"
        "Все предсказания носят исключительно <b>развлекательно-познавательный характер</b> "
        "и не являются руководством к действию, медицинской, юридической или иной консультацией.\n\n"
        "Любые совпадения с реальными событиями случайны."
    )


def _name_text() -> str:
    return "Как тебя зовут? Напиши своё имя — я буду обращаться к тебе именно так."


def _gender_text() -> str:
    return "🌸 Укажи свой пол — это поможет сделать нити более точными для тебя."


def _welcome_text(name: str, gender: str) -> str:
    if gender == "female":
        return (
            f"✨ <b>{name}, ты коснулась первой нити.</b>\n\n"
            "Меня зовут Оракул Нитей Судьбы. Я не предсказываю будущее. "
            "Я помогаю распутать то, что уже здесь — страхи, обиды, выборы, "
            "обещания себе, которые ты забыла.\n\n"
            "Каждый день я даю одну нить. Это метафора + вопрос к себе + маленький ритуал.\n\n"
            "Оракул поведёт тебя вглубь твоего подсознания — день за днём помогая "
            "раскрыть все тайные стороны твоей психологии.\n\n"
            "Готова начать?"
        )
    else:
        return (
            f"✨ <b>{name}, ты коснулся первой нити.</b>\n\n"
            "Меня зовут Оракул Нитей Судьбы. Я не предсказываю будущее. "
            "Я помогаю распутать то, что уже здесь — страхи, обиды, выборы, "
            "обещания себе, которые ты забыл.\n\n"
            "Каждый день я даю одну нить. Это метафора + вопрос к себе + маленький ритуал.\n\n"
            "День за днём Оракул будет вести тебя вглубь — к тому, "
            "что ты давно знал, но не решался увидеть.\n\n"
            "Готов начать?"
        )


async def _send(update: Update, **kwargs) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(**kwargs)


async def _show_main_menu(update: Update, user: sqlite3.Row) -> None:
    name = user["display_name"] or ""
    schedule_time = user["schedule_time"]

    if schedule_time:
        note = f"\n\n📅 Рассылка настроена на <b>{schedule_time}</b>"
    else:
        note = "\n\n🌅 Нить доступна каждый день"

    greeting = (
        f"{name}, мысленно задай вопрос или просто позволь нити появиться."
        if name else
        "Мысленно задай вопрос или просто позволь нити появиться."
    )
    text = "🔮 <b>Оракул Нитей Судьбы</b>\n\n" + greeting + note
    await _send(update, text=text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    user = db.get_or_create_user(tg.id, tg.username, tg.first_name)

    if user["is_deleted"] or not user["consent_given"]:
        await update.message.reply_text(
            _consent_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=consent_keyboard(),
            disable_web_page_preview=True,
        )
        return

    if not user["disclaimer_ok"]:
        await update.message.reply_text(
            _disclaimer_text(), parse_mode=ParseMode.HTML, reply_markup=disclaimer_keyboard()
        )
        return

    if user["display_name"] is None:
        await update.message.reply_text(_name_text())
        return

    if user["gender"] is None:
        await update.message.reply_text(_gender_text(), reply_markup=gender_keyboard())
        return

    await _show_main_menu(update, user)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 <b>Команды</b>\n\n"
        "/start — начать или перезапустить\n"
        "/schedule — управление рассылкой\n"
        "/delete — удалить аккаунт\n"
        "/help — справка",
        parse_mode=ParseMode.HTML,
    )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    if not user or not user["welcomed"] or user["is_deleted"]:
        await update.message.reply_text("Нажми /start для начала работы.")
        return

    if user["schedule_time"]:
        text = f"📅 Рассылка настроена на <b>{user['schedule_time']}</b>."
    else:
        text = "📅 Ежедневная рассылка не настроена."

    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=schedule_manage_keyboard(bool(user["schedule_time"])),
    )


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    if not user or user["is_deleted"]:
        await update.message.reply_text("Аккаунт не найден. Нажми /start.")
        return

    await update.message.reply_text(
        "🗑 <b>Удаление аккаунта</b>\n\n"
        "Все настройки будут сброшены и нужно будет пройти регистрацию заново.\n\n"
        "⚠️ Если сегодня уже была нить — повторно получить её можно только завтра.",
        parse_mode=ParseMode.HTML,
        reply_markup=delete_confirm_keyboard(),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    if not user or not user["consent_given"] or not user["disclaimer_ok"] or user["is_deleted"]:
        await update.message.reply_text("Нажми /start для начала работы.")
        return

    if user["display_name"] is None:
        name = text.strip()[:50]
        db.set_display_name(user_id, name)
        await update.message.reply_text(
            f"Приятно познакомиться, {name}! 🌿\n\n{_gender_text()}",
            reply_markup=gender_keyboard(),
        )
        return

    if user["gender"] is None:
        await update.message.reply_text(_gender_text(), reply_markup=gender_keyboard())
        return

    if text == BTN_PREDICTION:
        await _handle_get_thread(update, user)
    elif text == BTN_HOW_IT_WORKS:
        await update.message.reply_text(HOW_IT_WORKS_TEXT, parse_mode=ParseMode.HTML)
    elif text == BTN_MY_SCHEDULE:
        await cmd_schedule(update, context)
    elif text == BTN_DELETE:
        await cmd_delete(update, context)


async def _handle_get_thread(update: Update, user: sqlite3.Row) -> None:
    can, reason = can_get_prediction(user["last_pred_date"])
    if not can:
        await update.message.reply_text(reason)
        return

    gender = user["gender"] or "female"
    thread = get_random_thread()
    db.record_prediction(user["user_id"], utc_date_str())

    footer = ""
    if user["schedule_time"]:
        footer = f"\n\n📅 Следующая нить придёт автоматически в <b>{user['schedule_time']}</b>."

    text = format_thread_message(thread, gender) + footer
    if thread.image_url:
        await update.message.reply_photo(photo=thread.image_url)
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    if not user["schedule_set"]:
        await update.message.reply_text(
            "✨ Хочешь, чтобы нить приходила автоматически каждый день в удобное время?",
            reply_markup=schedule_question_keyboard(),
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    db.get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)

    if data == CB_CONSENT_AGREE:
        db.set_consent(user_id)
        await query.edit_message_text(
            _disclaimer_text(), parse_mode=ParseMode.HTML, reply_markup=disclaimer_keyboard()
        )

    elif data == CB_CONSENT_DECLINE:
        await query.edit_message_text(
            "Без согласия на обработку данных бот недоступен. Если передумаешь — нажми /start."
        )

    elif data == CB_DISCLAIMER_OK:
        db.set_disclaimer_ok(user_id)
        await query.edit_message_text(_name_text())

    elif data in (CB_GENDER_FEMALE, CB_GENDER_MALE):
        gender = "female" if data == CB_GENDER_FEMALE else "male"
        db.set_gender(user_id, gender)
        db.set_welcomed(user_id)
        user = db.get_user(user_id)
        name = user["display_name"] or "друг"
        await query.edit_message_text("✅ Принято!")
        await query.message.reply_text(
            _welcome_text(name, gender),
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )

    elif data == CB_SCHEDULE_YES:
        await query.edit_message_text(
            "🕐 Выбери время рассылки:",
            reply_markup=schedule_time_keyboard(),
        )

    elif data == CB_SCHEDULE_NO:
        db.set_schedule(user_id, None)
        await query.edit_message_text("👍 Хорошо! Нить будет доступна вручную каждый день.")

    elif data in CB_SCHEDULE_TIME_MAP:
        time_str = CB_SCHEDULE_TIME_MAP[data]
        db.set_schedule(user_id, time_str)
        await query.edit_message_text(
            f"🌟 Готово! Каждый день в <b>{time_str}</b> тебе будет приходить нить.",
            parse_mode=ParseMode.HTML,
        )

    elif data == CB_SCHEDULE_DISABLE:
        db.set_schedule(user_id, None)
        await query.edit_message_text("❌ Рассылка отключена.")

    elif data == CB_DELETE_CONFIRM:
        db.delete_user(user_id)
        await query.edit_message_text("🗑 Аккаунт удалён. Нажми /start, чтобы начать заново.")

    elif data == CB_DELETE_CANCEL:
        await query.edit_message_text("↩️ Удаление отменено.")
