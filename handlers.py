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
    CB_DELETE_ACCOUNT,
    CB_DELETE_CANCEL,
    CB_DELETE_CONFIRM,
    CB_DISCLAIMER_OK,
    CB_SCHEDULE_DISABLE,
    CB_SCHEDULE_NO,
    CB_SCHEDULE_TIME_MAP,
    CB_SCHEDULE_YES,
    consent_keyboard,
    delete_confirm_keyboard,
    disclaimer_keyboard,
    main_keyboard,
    schedule_manage_keyboard,
    schedule_question_keyboard,
    schedule_time_keyboard,
)
from predictions import get_random_prediction
from utils import can_get_prediction, moscow_date_str
from config import PRIVACY_POLICY_URL

logger = logging.getLogger(__name__)


def _consent_text() -> str:
    return (
        "👁 <b>Оракул Нитей Судьбы</b>\n\n"
        "Для использования бота необходимо дать согласие на обработку персональных данных.\n\n"
        f'Ознакомьтесь с <a href="{PRIVACY_POLICY_URL}">Политикой конфиденциальности</a> и подтвердите согласие.'
    )


def _disclaimer_text() -> str:
    return (
        "⚠️ <b>Важное предупреждение</b>\n\n"
        "Все предсказания носят исключительно <b>развлекательно-познавательный характер</b> "
        "и не являются руководством к действию, медицинской, юридической или иной консультацией.\n\n"
        "Любые совпадения с реальными событиями случайны."
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    user = db.get_or_create_user(tg_user.id, tg_user.username, tg_user.first_name)

    if user["is_deleted"]:
        # Restart flow from consent, but keep last_pred_date intact
        await update.message.reply_text(
            _consent_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=consent_keyboard(),
            disable_web_page_preview=True,
        )
        return

    if not user["consent_given"]:
        await update.message.reply_text(
            _consent_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=consent_keyboard(),
            disable_web_page_preview=True,
        )
        return

    if not user["disclaimer_ok"]:
        await update.message.reply_text(
            _disclaimer_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=disclaimer_keyboard(),
        )
        return

    await _show_main_menu(update, user["schedule_time"])


async def _show_main_menu(update: Update, schedule_time: str | None) -> None:
    if schedule_time:
        note = f"\n\n📅 Ваша ежедневная рассылка настроена на <b>{schedule_time}</b> (мск)"
    else:
        note = "\n\n🌅 Предсказание доступно каждый день с 7:00 (мск)"

    text = "🔮 <b>Оракул Нитей Судьбы</b>\n\nМысленно задайте вопрос или просто узнайте, что сулит грядущий день." + note

    if update.callback_query:
        await update.callback_query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
        )


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
        await update.message.reply_text("Сначала нажмите /start для начала работы.")
        return

    schedule_time = user["schedule_time"]
    if schedule_time:
        text = f"📅 Ваша рассылка настроена на <b>{schedule_time}</b> по московскому времени."
    else:
        text = "📅 У вас не настроена ежедневная рассылка."

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
        "Вы уверены? После удаления вам нужно будет пройти регистрацию заново.\n\n"
        "⚠️ Если сегодня вы уже получали предсказание — повторно получить его можно будет только завтра после 7:00.",
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

    if text == BTN_PREDICTION:
        await _handle_get_prediction(update, user)
    elif text == BTN_MY_SCHEDULE:
        await cmd_schedule(update, context)
    elif text == BTN_DELETE:
        await cmd_delete(update, context)


async def _handle_get_prediction(update: Update, user: sqlite3.Row) -> None:
    can, reason = can_get_prediction(user["last_pred_date"])
    if not can:
        await update.message.reply_text(reason)
        return

    prediction = get_random_prediction()
    today = moscow_date_str()
    db.record_prediction(user["user_id"], today)

    schedule_time = user["schedule_time"]
    if schedule_time:
        footer = f"\n\n📅 Следующее предсказание придёт автоматически в <b>{schedule_time}</b>."
    else:
        footer = ""

    await update.message.reply_text(
        f"🔮 <b>Ваше предсказание на сегодня</b>\n\n<i>{prediction}</i>{footer}",
        parse_mode=ParseMode.HTML,
    )

    # Ask about schedule only if user hasn't decided yet
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

    user = db.get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)

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
        await query.edit_message_text("✅ Отлично! Добро пожаловать в Оракул Нитей Судьбы.")
        updated_user = db.get_user(user_id)
        await _show_main_menu(update, updated_user["schedule_time"] if updated_user else None)

    elif data == CB_SCHEDULE_YES:
        await query.edit_message_text(
            "🕐 Выберите время рассылки (по московскому времени):",
            reply_markup=schedule_time_keyboard(),
        )

    elif data == CB_SCHEDULE_NO:
        db.set_schedule(user_id, None)
        await query.edit_message_text(
            "👍 Хорошо! Предсказание будет доступно каждый день с 7:00 утра по московскому времени."
        )

    elif data in CB_SCHEDULE_TIME_MAP:
        time_str = CB_SCHEDULE_TIME_MAP[data]
        db.set_schedule(user_id, time_str)
        await query.edit_message_text(
            f"🌟 Отлично! Каждый день в <b>{time_str}</b> (мск) вам будет приходить предсказание.",
            parse_mode=ParseMode.HTML,
        )

    elif data == CB_SCHEDULE_DISABLE:
        db.set_schedule(user_id, None)
        await query.edit_message_text(
            "❌ Ежедневная рассылка отключена. Вы можете запросить предсказание вручную каждый день с 7:00."
        )

    elif data == CB_DELETE_CONFIRM:
        db.delete_user(user_id)
        await query.edit_message_text(
            "🗑 Аккаунт удалён. Все настройки сброшены.\n\n"
            "Нажмите /start, чтобы начать заново.",
        )

    elif data == CB_DELETE_CANCEL:
        await query.edit_message_text("↩️ Удаление отменено.")
