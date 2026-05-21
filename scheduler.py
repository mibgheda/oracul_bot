import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

import database as db
from threads import format_thread_message, get_random_thread
from utils import utc_date_str

logger = logging.getLogger(__name__)


async def check_and_send_predictions(bot: Bot) -> None:
    now_utc = datetime.now(timezone.utc)
    today = utc_date_str()
    users = db.get_all_scheduled_users()

    for user in users:
        if int(user["schedule_time"][:2]) != now_utc.hour:
            continue
        if user["last_pred_date"] == today:
            continue

        thread = get_random_thread()
        gender = user["gender"] or "female"
        name = user["display_name"] or ""
        try:
            greeting = f"Привет, {name}! ✨\n\n" if name else ""
            text = greeting + format_thread_message(thread, gender)
            if thread.image_url:
                await bot.send_photo(chat_id=user["user_id"], photo=thread.image_url)
                await bot.send_message(
                    chat_id=user["user_id"], text=text, parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=user["user_id"], text=text, parse_mode=ParseMode.HTML
                )
            db.record_prediction(user["user_id"], today)
        except Exception as exc:
            logger.warning("Scheduled send failed for %d: %s", user["user_id"], exc)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_and_send_predictions,
        trigger="cron",
        minute=0,
        kwargs={"bot": bot},
        id="check_scheduled",
        replace_existing=True,
    )
    return scheduler
