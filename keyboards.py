from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Callback data constants
CB_CONSENT_AGREE   = "consent_agree"
CB_CONSENT_DECLINE = "consent_decline"
CB_DISCLAIMER_OK   = "disclaimer_ok"
CB_GENDER_FEMALE   = "gender_female"
CB_GENDER_MALE     = "gender_male"
CB_SCHEDULE_YES    = "schedule_yes"
CB_SCHEDULE_NO     = "schedule_no"
CB_SCHEDULE_TIME_07 = "schedule_time_07"
CB_SCHEDULE_TIME_10 = "schedule_time_10"
CB_SCHEDULE_TIME_14 = "schedule_time_14"
CB_SCHEDULE_TIME_18 = "schedule_time_18"
CB_DELETE_CONFIRM  = "delete_confirm"
CB_DELETE_CANCEL   = "delete_cancel"
CB_SCHEDULE_DISABLE = "schedule_disable"
CB_TZ_PREFIX       = "tz_"

CB_SCHEDULE_TIME_MAP = {
    CB_SCHEDULE_TIME_07: "07:00",
    CB_SCHEDULE_TIME_10: "10:00",
    CB_SCHEDULE_TIME_14: "14:00",
    CB_SCHEDULE_TIME_18: "18:00",
}

BTN_PREDICTION    = "🎲 Дай нить дня"
BTN_HOW_IT_WORKS  = "❓ Как это работает"
BTN_MY_SCHEDULE   = "📅 Моя рассылка"
BTN_DELETE        = "🗑 Удалить аккаунт"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_PREDICTION],
            [BTN_HOW_IT_WORKS, BTN_MY_SCHEDULE],
            [BTN_DELETE],
        ],
        resize_keyboard=True,
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Даю согласие",  callback_data=CB_CONSENT_AGREE)],
        [InlineKeyboardButton("❌ Отказываюсь",  callback_data=CB_CONSENT_DECLINE)],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Понял(а), продолжить ➡️", callback_data=CB_DISCLAIMER_OK)],
    ])


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👩 Женщина", callback_data=CB_GENDER_FEMALE),
            InlineKeyboardButton("👨 Мужчина", callback_data=CB_GENDER_MALE),
        ]
    ])


def timezone_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for h in range(-12, 13):
        label = f"UTC{'+' if h >= 0 else ''}{h}"
        row.append(InlineKeyboardButton(label, callback_data=f"{CB_TZ_PREFIX}{h * 60}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def schedule_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, хочу!",       callback_data=CB_SCHEDULE_YES)],
        [InlineKeyboardButton("❌ Нет, спасибо",   callback_data=CB_SCHEDULE_NO)],
    ])


def schedule_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕖 7:00",  callback_data=CB_SCHEDULE_TIME_07),
            InlineKeyboardButton("🕙 10:00", callback_data=CB_SCHEDULE_TIME_10),
        ],
        [
            InlineKeyboardButton("🕑 14:00", callback_data=CB_SCHEDULE_TIME_14),
            InlineKeyboardButton("🕕 18:00", callback_data=CB_SCHEDULE_TIME_18),
        ],
    ])


def delete_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Да, удалить", callback_data=CB_DELETE_CONFIRM)],
        [InlineKeyboardButton("↩️ Отмена",      callback_data=CB_DELETE_CANCEL)],
    ])


def schedule_manage_keyboard(has_schedule: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_schedule:
        buttons.append([InlineKeyboardButton("🔄 Изменить время",     callback_data=CB_SCHEDULE_YES)])
        buttons.append([InlineKeyboardButton("❌ Отключить рассылку", callback_data=CB_SCHEDULE_DISABLE)])
    else:
        buttons.append([InlineKeyboardButton("✅ Подключить рассылку", callback_data=CB_SCHEDULE_YES)])
    return InlineKeyboardMarkup(buttons)
