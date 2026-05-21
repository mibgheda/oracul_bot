import logging
import sqlite3

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from keyboards import (
    BTN_DELETE,
    BTN_MY_SCHEDULE,
    BTN_PREDICTION,
    CB_CONSENT_AGREE,
    CB_CONSENT_DECLINE,
    CB_DELETE_CANCEL,
    CB_DELETE_CONFIRM,
    CB_DISCLAIMER_OK,
    CB_SCHEDULE_DISABLE,
    CB_SCHEDULE_NO,
    CB_SCHEDULE_TIME_MAP,
    CB_SCHEDULE_YES,
    CB_TZ_PREFIX,
    consent_keyboard,
    delete_confirm_keyboard,
    disclaimer_keyboard,
    main_keyboard,
    schedule_manage_keyboard,
    schedule_question_keyboard,
    schedule_time_keyboard,
    timezone_keyboard,
)
from threads import format_thread_message, get_random_thread
from utils import can_get_prediction, format_utc_offset, user_date_str
from config import PRIVACY_POLICY_URL

logger = logging.getLogger(__name__)


def _consent_text() -> str:
    return (
        "👁 <b>Оракул Нитей Судьбы</b>\n\n"
        "Для использования бота необходимо дать согласие на обработку персональных данных.\n\n"
        f'Ознакомьтесь с <a href="{PRIVACY_POLICY_URL}">Политикой конфиденциальности</a> '
        "и подтвердите согласие."
    )


def _disclaimer_text() -> str:
    return (
        "⚠️ <b>Важное предупреждение</b>\n\n"
        "Все предсказания носят исключительно <b>развлекательно-познавательный характер</b> "
        "и не являются руководством к действию, медицинской, юридической или иной консультацией.\n\n"
        "Любые совпадения с реальными событиями случайны."
    )


def _timezone_text() -> str:
    return (
        "🌍 <b>Укажите ваш часовой пояс</b>\n\n"
        "Это нужно, чтобы предсказание приходило в правильное время.\n\n"
        "Примеры:\n"
        "• <b>UTC+2</b> — Киев, Хельсинки\n"
        "• <b>UTC+3</b> — Москва, Минск\n"
        "• <b>UTC+4</b> — Баку, Самара\n"
        "• <b>UTC+5</b> — Екатеринбург, Ташкент\n"
        "• <b>UTC+0</b> — Лондон"
    )


async def _show_consent(update: Update) -> None:
    kwargs = dict(
        text=_consent_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=consent_keyboard(),
        disable_web_page_preview=True,
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(**kwargs)
    else:
        await update.message.reply_text(**kwargs)


async def _show_timezone_selection(update: Update) -> None:
    kwargs = dict(
        text=_timezone_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=timezone_keyboard(),
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(**kwargs)
    else:
        await update.message.reply_text(**kwargs)


async def _show_main_menu(update: Update, user: sqlite3.Row) -> None:
    utc_offset = user["utc_offset"] if user["utc_offset"] is not None else 0
    tz_str = format_utc_offset(utc_offset)
    schedule_time = user["schedule_time"]

    if schedule_time:
        note = f"\n\n📅 Рассылка настроена на <b>{schedule_time}</b> ({tz_str})"
    else:
        note = f"\n\n🌅 Предсказание доступно каждый день с 7:00 ({tz_str})"

    text = (
        "🔮 <b>Оракул Нитей Судьбы</b>\n\n"
        "Мысленно задайте вопрос или просто узнайте, что сулит грядущий день."
        + note
    )

    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    user = db.get_or_create_user(tg.id, tg.username, tg.first_name)

    if user["is_deleted"] or not user["consent_given"]:
        await _show_consent(update)
        return

    if not user["disclaimer_ok"]:
        await update.message.reply_text(
            _disclaimer_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=disclaimer_keyboard(),
        )
        return

    if user["utc_offset"] is None:
        await _show_timezone_selection(update)
        return

    await _show_main_menu(update, user)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 <b>Команды бота</b>\n\n"
        "/start — начать или перезапустить\n"
        "/schedule — управление рассылкой\n"
        "/delete — удалить аккаунт\n"
        "/help — эта справка",
        parse_mode=ParseMode.HTML,
    )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    if not user or not user["consent_given"] or not user["disclaimer_ok"] or user["is_deleted"]:
        await update.message.reply_text("Сначала нажмите /start.")
        return

    utc_offset = user["utc_offset"] if user["utc_offset"] is not None else 0
    tz_str = format_utc_offset(utc_offset)
    schedule_time = user["schedule_time"]

    if schedule_time:
        text = f"📅 Рассылка настроена на <b>{schedule_time}</b> ({tz_str})."
    else:
        text = f"📅 Ежедневная рассылка не настроена. Ваш часовой пояс: <b>{tz_str}</b>."

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=schedule_manage_keyboard(bool(schedule_time)),
    )


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    if not user or user["is_deleted"]:
        await update.message.reply_text("Аккаунт не найден. Нажмите /start.")
        return

    await update.message.reply_text(
        "🗑 <b>Удаление аккаунта</b>\n\n"
        "Вы уверены? Все настройки будут сброшены и нужно будет пройти регистрацию заново.\n\n"
        "⚠️ Если сегодня уже было предсказание — повторно получить его можно только завтра после 7:00.",
        parse_mode=ParseMode.HTML,
        reply_markup=delete_confirm_keyboard(),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    if not user or not user["consent_given"] or not user["disclaimer_ok"] or user["is_deleted"]:
        await update.message.reply_text("Нажмите /start для начала работы.")
        return

    if user["utc_offset"] is None:
        await _show_timezone_selection(update)
        return

    if text == BTN_PREDICTION:
        await _handle_get_prediction(update, user)
    elif text == BTN_MY_SCHEDULE:
        await cmd_schedule(update, context)
    elif text == BTN_DELETE:
        await cmd_delete(update, context)


async def _handle_get_prediction(update: Update, user: sqlite3.Row) -> None:
    utc_offset = user["utc_offset"] if user["utc_offset"] is not None else 0
    can, reason = can_get_prediction(user["last_pred_date"], utc_offset)
    if not can:
        await update.message.reply_text(reason)
        return

    thread = get_random_thread()
    local_date = user_date_str(utc_offset)
    db.record_prediction(user["user_id"], local_date)

    schedule_time = user["schedule_time"]
    if schedule_time:
        footer = f"\n\n📅 Следующее предсказание придёт автоматически в <b>{schedule_time}</b>."
    else:
        footer = ""

    await update.message.reply_text(
        format_thread_message(thread) + footer,
        parse_mode=ParseMode.HTML,
    )

    if not user["schedule_set"]:
        await update.message.reply_text(
            "✨ Хотите, чтобы предсказание приходило автоматически каждый день в удобное время?",
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
            _disclaimer_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=disclaimer_keyboard(),
        )

    elif data == CB_CONSENT_DECLINE:
        await query.edit_message_text(
            "Без согласия на обработку данных бот недоступен. "
            "Если передумаете — нажмите /start."
        )

    elif data == CB_DISCLAIMER_OK:
        db.set_disclaimer_ok(user_id)
        await query.edit_message_text(
            _timezone_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=timezone_keyboard(),
        )

    elif data.startswith(CB_TZ_PREFIX):
        offset_minutes = int(data[len(CB_TZ_PREFIX):])
        db.set_timezone(user_id, offset_minutes)
        tz_str = format_utc_offset(offset_minutes)
        await query.edit_message_text(
            f"✅ Часовой пояс сохранён: <b>{tz_str}</b>",
            parse_mode=ParseMode.HTML,
        )
        user = db.get_user(user_id)
        await _show_main_menu(update, user)

    elif data == CB_SCHEDULE_YES:
        await query.edit_message_text(
            "🕐 Выберите время рассылки (по вашему часовому поясу):",
            reply_markup=schedule_time_keyboard(),
        )

    elif data == CB_SCHEDULE_NO:
        db.set_schedule(user_id, None)
        await query.edit_message_text(
            "👍 Хорошо! Предсказание будет доступно каждый день с 7:00 по вашему времени."
        )

    elif data in CB_SCHEDULE_TIME_MAP:
        time_str = CB_SCHEDULE_TIME_MAP[data]
        db.set_schedule(user_id, time_str)
        user = db.get_user(user_id)
        tz_str = format_utc_offset(user["utc_offset"] or 0)
        await query.edit_message_text(
            f"🌟 Готово! Каждый день в <b>{time_str}</b> ({tz_str}) вам будет приходить предсказание.",
            parse_mode=ParseMode.HTML,
        )

    elif data == CB_SCHEDULE_DISABLE:
        db.set_schedule(user_id, None)
        await query.edit_message_text(
            "❌ Рассылка отключена. Предсказание доступно вручную каждый день с 7:00."
        )

    elif data == CB_DELETE_CONFIRM:
        db.delete_user(user_id)
        await query.edit_message_text(
            "🗑 Аккаунт удалён. Все настройки сброшены.\n\nНажмите /start, чтобы начать заново."
        )

    elif data == CB_DELETE_CANCEL:
        await query.edit_message_text("↩️ Удаление отменено.")
