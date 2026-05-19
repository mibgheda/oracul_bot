from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import PRIVACY_POLICY_URL

# Callback data constants
CB_CONSENT_AGREE = "consent_agree"
CB_CONSENT_DECLINE = "consent_decline"
CB_DISCLAIMER_OK = "disclaimer_ok"
CB_SCHEDULE_YES = "schedule_yes"
CB_SCHEDULE_NO = "schedule_no"
CB_SCHEDULE_TIME_07 = "schedule_time_07"
CB_SCHEDULE_TIME_10 = "schedule_time_10"
CB_SCHEDULE_TIME_14 = "schedule_time_14"
CB_SCHEDULE_TIME_18 = "schedule_time_18"
CB_DELETE_ACCOUNT = "delete_account"
CB_DELETE_CONFIRM = "delete_confirm"
CB_DELETE_CANCEL = "delete_cancel"
CB_SCHEDULE_DISABLE = "schedule_disable"

CB_SCHEDULE_TIME_MAP = {
    CB_SCHEDULE_TIME_07: "07:00",
    CB_SCHEDULE_TIME_10: "10:00",
    CB_SCHEDULE_TIME_14: "14:00",
    CB_SCHEDULE_TIME_18: "18:00",
}

BTN_PREDICTION = "🔮 Получить предсказание на сегодня"
BTN_MY_SCHEDULE = "📅 Моя рассылка"
BTN_DELETE = "🗑 Удалить аккаунт"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_PREDICTION], [BTN_MY_SCHEDULE, BTN_DELETE]],
        resize_keyboard=True,
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Даю согласие", callback_data=CB_CONSENT_AGREE)],
        [InlineKeyboardButton("❌ Отказываюсь", callback_data=CB_CONSENT_DECLINE)],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Понял(а), продолжить ➡️", callback_data=CB_DISCLAIMER_OK)],
    ])


def schedule_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, хочу!", callback_data=CB_SCHEDULE_YES)],
        [InlineKeyboardButton("❌ Нет, спасибо", callback_data=CB_SCHEDULE_NO)],
    ])


def schedule_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕖 7:00", callback_data=CB_SCHEDULE_TIME_07),
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
        [InlineKeyboardButton("↩️ Отмена", callback_data=CB_DELETE_CANCEL)],
    ])


def schedule_manage_keyboard(has_schedule: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_schedule:
        buttons.append([InlineKeyboardButton("🔄 Изменить время", callback_data=CB_SCHEDULE_YES)])
        buttons.append([InlineKeyboardButton("❌ Отключить рассылку", callback_data=CB_SCHEDULE_DISABLE)])
    else:
        buttons.append([InlineKeyboardButton("✅ Подключить рассылку", callback_data=CB_SCHEDULE_YES)])
    return InlineKeyboardMarkup(buttons)
