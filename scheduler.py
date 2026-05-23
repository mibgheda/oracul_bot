import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

import database as db
from knots import SmallKnot, get_new_knots
from threads import format_thread_message, pick_thread_for_user
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

        user_id = user["user_id"]
        gender = user["gender"] or "female"
        name = user["display_name"] or ""
        try:
            user_variants = db.get_user_variants(user_id)
            thread, variant_index = pick_thread_for_user(user_variants)
            db.record_thread_variant(user_id, thread.name, variant_index, today)
            db.record_prediction(user_id, today)

            greeting = f"Привет, {name}! ✨\n\n" if name else ""
            text = greeting + format_thread_message(thread, gender, variant_index)
            if thread.image_url:
                await bot.send_photo(chat_id=user_id, photo=thread.image_url)
                await bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)

            # Check for newly unlocked knots
            all_received = set(user_variants.keys()) | {thread.name}
            unlocked_ids = {k["knot_id"] for k in db.get_user_knots(user_id)}
            for knot in get_new_knots(thread.name, all_received, unlocked_ids):
                knot_type = "small" if isinstance(knot, SmallKnot) else "transformation"
                db.record_knot(user_id, knot.knot_id, knot_type, knot.name, today)
                s = "а" if gender == "female" else ""
                emoji = "🪢" if knot_type == "small" else "🌀"
                level = "Малый узел" if knot_type == "small" else "Узел трансформации"
                await bot.send_message(
                    chat_id=user_id,
                    text=f"{emoji} <b>{level} разблокирован!</b>\n\nТы собрал{s} «{knot.name}».\n\n{knot.unlock_text}",
                    parse_mode=ParseMode.HTML,
                )
        except Exception as exc:
            logger.warning("Scheduled send failed for %d: %s", user_id, exc)


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
