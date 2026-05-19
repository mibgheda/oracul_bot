from datetime import datetime, time
import pytz

MOSCOW_TZ = pytz.timezone("Europe/Moscow")
UNLOCK_HOUR = 7  # predictions unlock at 07:00 Moscow


def moscow_now() -> datetime:
    return datetime.now(MOSCOW_TZ)


def moscow_date_str() -> str:
    return moscow_now().strftime("%Y-%m-%d")


def can_get_prediction(last_pred_date: str | None) -> tuple[bool, str]:
    """Returns (can_predict, reason_if_not)."""
    now = moscow_now()
    today = now.strftime("%Y-%m-%d")

    if now.hour < UNLOCK_HOUR:
        return False, f"⏳ Предсказание станет доступно сегодня в {UNLOCK_HOUR}:00 по московскому времени."

    if last_pred_date == today:
        return False, "🌙 Вы уже получили предсказание сегодня. Возвращайтесь завтра после 7:00 ✨"

    return True, ""
