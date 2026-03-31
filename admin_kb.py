from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="💅 Услуги")
    builder.button(text="📅 Слоты")
    builder.button(text="📋 Записи")
    builder.button(text="📊 Статистика")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def services_list_keyboard(services: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in services:
        status = "✅" if s.is_active else "❌"
        builder.button(text=f"{status} {s.name} — {s.price}₽", callback_data=f"edit_service:{s.id}")
    builder.button(text="➕ Добавить услугу", callback_data="add_service")
    builder.button(text="❌ Закрыть", callback_data="close")
    builder.adjust(1)
    return builder.as_markup()


def service_edit_keyboard(service_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Название", callback_data=f"se_name:{service_id}")
    builder.button(text="💰 Цена", callback_data=f"se_price:{service_id}")
    builder.button(text="⏱ Длительность", callback_data=f"se_duration:{service_id}")
    builder.button(text="📝 Описание", callback_data=f"se_desc:{service_id}")
    builder.button(text="🖼 Фото", callback_data=f"se_photo:{service_id}")
    builder.button(text="🔄 Вкл/Выкл", callback_data=f"se_toggle:{service_id}")
    builder.button(text="🗑 Удалить", callback_data=f"se_delete:{service_id}")
    builder.button(text="⬅️ Назад", callback_data="back_to_services")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def slots_keyboard(slots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        status = "🔴" if slot.is_booked else "🟢"
        builder.button(
            text=f"{status} {slot.date} {slot.time}",
            callback_data=f"del_slot:{slot.id}"
        )
    builder.button(text="➕ Добавить слоты", callback_data="add_slots")
    builder.button(text="❌ Закрыть", callback_data="close")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_keyboard(item_id: int, item_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_delete:{item_type}:{item_id}")
    builder.button(text="❌ Отмена", callback_data="close")
    builder.adjust(2)
    return builder.as_markup()
