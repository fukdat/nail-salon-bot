from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import calendar
from datetime import date


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Записаться", callback_data="menu:book")
    builder.button(text="📍 Адрес", callback_data="menu:address")
    builder.button(text="🖼 Работы", callback_data="menu:portfolio")
    builder.adjust(1)
    return builder.as_markup()


def service_keyboard(service_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Записаться", callback_data=f"book_service:{service_id}")
    builder.button(text="⚡ Ближайший слот", callback_data=f"quick_service:{service_id}")
    nav = []
    if index > 0:
        nav.append(("⬅️ Назад", f"service_page:{index - 1}"))
    if index < total - 1:
        nav.append(("Далее ➡️", f"service_page:{index + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="⬅️ В меню", callback_data="to_menu")
    builder.adjust(2, *([2] if nav else []), 1)
    return builder.as_markup()


def calendar_keyboard(year: int, month: int, available_dates: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    month_name = [
        "", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
        "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
    ][month]

    builder.button(text="⬅️", callback_data=f"cal_prev:{year}:{month}")
    builder.button(text=f"{month_name} {year}", callback_data="ignore")
    builder.button(text="➡️", callback_data=f"cal_next:{year}:{month}")
    builder.adjust(3)

    days_header = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for d in days_header:
        builder.button(text=d, callback_data="ignore")
    builder.adjust(3, 7)

    cal = calendar.monthcalendar(year, month)
    row_sizes = [3, 7]

    for week in cal:
        for day in week:
            if day == 0:
                builder.button(text=" ", callback_data="ignore")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                today = date.today().isoformat()
                if date_str in available_dates and date_str >= today:
                    builder.button(text=f"🔵{day}", callback_data=f"select_date:{date_str}")
                else:
                    builder.button(text=str(day), callback_data="ignore")
        row_sizes.append(7)

    builder.button(text="⬅️ В меню", callback_data="to_menu")
    row_sizes.append(1)

    builder.adjust(*row_sizes)
    return builder.as_markup()


def times_keyboard(slots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in sorted(slots, key=lambda x: x.time):
        builder.button(text=slot.time, callback_data=f"select_time:{slot.id}")
    builder.button(text="⬅️ В меню", callback_data="to_menu")
    builder.adjust(3, *([3] * (len(slots) // 3)), 1)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_booking")
    builder.button(text="❌ Отмена", callback_data="to_menu")
    builder.adjust(2)
    return builder.as_markup()
