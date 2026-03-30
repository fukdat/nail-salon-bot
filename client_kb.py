from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

SERVICES = [
    "Маникюр — 1500 руб.",
    "Педикюр — 2000 руб.",
    "Маникюр + Педикюр — 3000 руб.",
    "Покрытие гель-лак — 800 руб.",
    "Наращивание — 3500 руб.",
]


def services_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in SERVICES:
        builder.button(text=service, callback_data=f"service:{service}")
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard(slots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    dates = sorted(set(slot.date for slot in slots))
    for date in dates:
        builder.button(text=f"📅 {date}", callback_data=f"date:{date}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def times_keyboard(slots: list, date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    available = [s for s in slots if s.date == date and not s.is_booked]
    for slot in sorted(available, key=lambda x: x.time):
        builder.button(text=f"🕐 {slot.time}", callback_data=f"time:{slot.id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_dates")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(3)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_booking")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()
