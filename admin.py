import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_ID

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return

    stats = db.get_stats()

    schedule_lines = ""
    for time_str in ["07:00", "10:00", "14:00", "18:00"]:
        count = stats["schedule_breakdown"].get(time_str, 0)
        schedule_lines += f"  • {time_str} — {count} чел.\n"

    text = (
        "📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего зарегистрировано: <b>{stats['total']}</b>\n"
        f"✅ Активных: <b>{stats['active']}</b>\n"
        f"🗑 Удалили аккаунт: <b>{stats['deleted']}</b>\n\n"
        f"📅 С ежедневной рассылкой:\n{schedule_lines}"
        f"🔕 Без рассылки (ручной режим): <b>{stats['no_schedule']}</b>\n\n"
        f"🔮 Предсказаний сегодня: <b>{stats['predictions_today']}</b>"
    )

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast &lt;текст сообщения&gt;",
            parse_mode=ParseMode.HTML,
        )
        return

    message_text = " ".join(context.args)
    users = db.get_all_active_users()

    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 {message_text}",
            )
            sent += 1
        except Exception as exc:
            logger.warning("Broadcast failed for %d: %s", user["user_id"], exc)
            failed += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {failed}"
    )
