from datetime import datetime, timezone


def utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def can_get_prediction(last_pred_date: str | None) -> tuple[bool, str]:
    if last_pred_date == utc_date_str():
        return False, "🌙 Нить уже была сегодня. Возвращайся завтра ✨"
    return True, ""
