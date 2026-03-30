from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить слот")
    builder.button(text="🗑 Удалить слот")
    builder.button(text="📋 Все записи")
    builder.button(text="📅 Свободные слоты")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def slots_delete_keyboard(slots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        status = "🔴 занят" if slot.is_booked else "🟢 свободен"
        builder.button(
            text=f"{slot.date} {slot.time} {status}",
            callback_data=f"delete_slot:{slot.id}"
        )
    builder.button(text="❌ Закрыть", callback_data="close")
    builder.adjust(1)
    return builder.as_markup()
