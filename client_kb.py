from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import calendar
from datetime import date


def nav_buttons(back_cb: str = None) -> list:
    """Returns nav buttons: [Назад] [В главное меню]"""
    buttons = []
    if back_cb:
        buttons.append(("⬅️ Назад", back_cb))
    buttons.append(("🏠 В главное меню", "to_menu"))
    return buttons


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Записаться", callback_data="menu:book")
    builder.button(text="📍 Адрес", callback_data="menu:address")
    builder.button(text="🖼 Работы", callback_data="menu:portfolio")
    builder.adjust(1)
    return builder.as_markup()


def simple_back_keyboard(back_cb: str = None) -> InlineKeyboardMarkup:
    """Just nav buttons — Назад + В главное меню"""
    builder = InlineKeyboardBuilder()
    for text, cb in nav_buttons(back_cb):
        builder.button(text=text, callback_data=cb)
    builder.adjust(1)
    return builder.as_markup()


def service_keyboard(service_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Записаться", callback_data=f"book_service:{service_id}")
    builder.button(text="⚡ Ближайший слот", callback_data=f"quick_service:{service_id}")

    nav_count = 0
    if index > 0:
        builder.button(text="⬅️ Назад", callback_data=f"service_page:{index - 1}")
        nav_count += 1
    if index < total - 1:
        builder.button(text="Далее ➡️", callback_data=f"service_page:{index + 1}")
        nav_count += 1

    builder.button(text="🏠 В главное меню", callback_data="to_menu")

    if nav_count > 0:
        builder.adjust(2, nav_count, 1)
    else:
        builder.adjust(2, 1)

    return builder.as_markup()


def calendar_keyboard(year: int, month: int, available_dates: list, service_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    month_name = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                  "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"][month]

    builder.button(text="⬅️", callback_data=f"cal_prev:{year}:{month}:{service_id}")
    builder.button(text=f"{month_name} {year}", callback_data="ignore")
    builder.button(text="➡️", callback_data=f"cal_next:{year}:{month}:{service_id}")

    for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        builder.button(text=d, callback_data="ignore")

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

    builder.button(text="⬅️ Назад", callback_data=f"back_to_services:{service_id}")
    builder.button(text="🏠 В главное меню", callback_data="to_menu")
    row_sizes.append(2)

    builder.adjust(*row_sizes)
    return builder.as_markup()


def times_keyboard(slots: list, selected_date: str, service_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sorted_slots = sorted(slots, key=lambda x: x.time)
    for slot in sorted_slots:
        builder.button(text=slot.time, callback_data=f"select_time:{slot.id}")

    n = len(sorted_slots)
    rows = [3] * (n // 3)
    if n % 3:
        rows.append(n % 3)

    builder.button(text="⬅️ Назад", callback_data=f"back_to_calendar:{service_id}")
    builder.button(text="🏠 В главное меню", callback_data="to_menu")
    rows.append(2)

    builder.adjust(*rows)
    return builder.as_markup()


def confirm_keyboard(slot_id: int = None, selected_date: str = None, service_id: int = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_booking")
    builder.button(text="⬅️ Назад", callback_data=f"back_to_times:{selected_date}:{service_id}")
    builder.button(text="🏠 В главное меню", callback_data="to_menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В главное меню", callback_data="to_menu")
    builder.adjust(1)
    return builder.as_markup()