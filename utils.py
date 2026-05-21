from datetime import datetime, timedelta, timezone

UNLOCK_HOUR = 7


def user_local_dt(utc_offset_minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=utc_offset_minutes)


def user_date_str(utc_offset_minutes: int) -> str:
    return user_local_dt(utc_offset_minutes).strftime("%Y-%m-%d")


def format_utc_offset(minutes: int) -> str:
    hours = minutes // 60
    return f"UTC{'+' if hours >= 0 else ''}{hours}"


def can_get_prediction(last_pred_date: str | None, utc_offset_minutes: int) -> tuple[bool, str]:
    local_dt = user_local_dt(utc_offset_minutes)
    local_date = local_dt.strftime("%Y-%m-%d")

    if local_dt.hour < UNLOCK_HOUR:
        return False, f"⏳ Предсказание станет доступно сегодня в {UNLOCK_HOUR}:00 по вашему времени."

    if last_pred_date == local_date:
        return False, "🌙 Вы уже получили предсказание сегодня. Возвращайтесь завтра после 7:00 ✨"

    return True, ""
