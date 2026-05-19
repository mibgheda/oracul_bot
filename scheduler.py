import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

import database as db
from predictions import get_random_prediction
from utils import moscow_date_str, MOSCOW_TZ

logger = logging.getLogger(__name__)


async def send_scheduled_predictions(bot: Bot, hour: int) -> None:
    time_str = f"{hour:02d}:00"
    users = db.get_users_with_schedule(time_str)
    today = moscow_date_str()

    for user in users:
        if user["last_pred_date"] == today:
            continue
        prediction = get_random_prediction()
        try:
            await bot.send_message(
                chat_id=user["user_id"],
                text=(
                    "🔮 <b>Ваше предсказание на сегодня</b>\n\n"
                    f"<i>{prediction}</i>"
                ),
                parse_mode=ParseMode.HTML,
            )
            db.record_prediction(user["user_id"], today)
        except Exception as exc:
            logger.warning("Failed to send scheduled prediction to %d: %s", user["user_id"], exc)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    for hour in [7, 10, 14, 18]:
        scheduler.add_job(
            send_scheduled_predictions,
            trigger="cron",
            hour=hour,
            minute=0,
            kwargs={"bot": bot, "hour": hour},
            id=f"predict_{hour:02d}",
            replace_existing=True,
        )
    return scheduler
