import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter

from database import get_db, Service, TimeSlot, Booking
from admin_kb import (
    admin_main_keyboard, services_list_keyboard, service_edit_keyboard,
    slots_keyboard, confirm_delete_keyboard
)

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID


class AdminState(StatesGroup):
    # Service creation
    adding_name = State()
    adding_price = State()
    adding_duration = State()
    adding_description = State()
    adding_photo = State()
    # Service editing
    editing_field = State()
    editing_value = State()
    # Slots
    adding_slots = State()


@router.message(IsAdmin(), F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👑 Панель администратора", reply_markup=admin_main_keyboard())


# ========== УСЛУГИ ==========

@router.message(IsAdmin(), F.text == "💅 Услуги")
async def show_services(message: Message, state: FSMContext):
    await state.clear()
    db = get_db()
    services = db.query(Service).all()
    db.close()
    await message.answer("Список услуг:", reply_markup=services_list_keyboard(services))


@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    db = get_db()
    services = db.query(Service).all()
    db.close()
    await callback.message.edit_text("Список услуг:", reply_markup=services_list_keyboard(services))


@router.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.adding_name)
    await callback.message.edit_text("Введите <b>название</b> услуги:", parse_mode="HTML")


@router.message(IsAdmin(), AdminState.adding_name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminState.adding_price)
    await message.answer("Введите <b>цену</b> (только цифры, в рублях):", parse_mode="HTML")


@router.message(IsAdmin(), AdminState.adding_price)
async def add_service_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число, например: 1500")
        return
    await state.update_data(price=price)
    await state.set_state(AdminState.adding_duration)
    await message.answer("Введите <b>длительность</b>, например: 2 ч 30 мин", parse_mode="HTML")


@router.message(IsAdmin(), AdminState.adding_duration)
async def add_service_duration(message: Message, state: FSMContext):
    await state.update_data(duration=message.text.strip())
    await state.set_state(AdminState.adding_description)
    await message.answer("Введите <b>описание</b> услуги (или напишите '-' чтобы пропустить):", parse_mode="HTML")


@router.message(IsAdmin(), AdminState.adding_description)
async def add_service_description(message: Message, state: FSMContext):
    desc = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AdminState.adding_photo)
    await message.answer("Отправьте <b>фото</b> услуги (или напишите '-' чтобы пропустить):", parse_mode="HTML")


@router.message(IsAdmin(), AdminState.adding_photo)
async def add_service_photo(message: Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == "-":
        photo_id = None
    else:
        await message.answer("Отправьте фото или напишите '-'")
        return

    data = await state.get_data()
    db = get_db()
    service = Service(
        name=data["name"],
        price=data["price"],
        duration=data["duration"],
        description=data.get("description"),
        photo_file_id=photo_id,
        is_active=True
    )
    db.add(service)
    db.commit()
    db.close()

    await state.clear()
    await message.answer(f"✅ Услуга <b>{data['name']}</b> добавлена!", reply_markup=admin_main_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("edit_service:"))
async def edit_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    db = get_db()
    s = db.query(Service).filter(Service.id == service_id).first()
    db.close()

    status = "✅ Активна" if s.is_active else "❌ Скрыта"
    await callback.message.edit_text(
        f"<b>{s.name}</b>\n"
        f"💰 {s.price} ₽ | ⏱ {s.duration}\n"
        f"Статус: {status}\n\n"
        f"Что редактируем?",
        reply_markup=service_edit_keyboard(service_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("se_toggle:"))
async def toggle_service(callback: CallbackQuery):
    service_id = int(callback.data.split(":")[1])
    db = get_db()
    s = db.query(Service).filter(Service.id == service_id).first()
    s.is_active = not s.is_active
    db.commit()
    status = "включена ✅" if s.is_active else "скрыта ❌"
    db.close()
    await callback.answer(f"Услуга {status}")
    db2 = get_db()
    s2 = db2.query(Service).filter(Service.id == service_id).first()
    status2 = "✅ Активна" if s2.is_active else "❌ Скрыта"
    await callback.message.edit_text(
        f"<b>{s2.name}</b>\n💰 {s2.price} ₽ | ⏱ {s2.duration}\nСтатус: {status2}\n\nЧто редактируем?",
        reply_markup=service_edit_keyboard(service_id),
        parse_mode="HTML"
    )
    db2.close()


@router.callback_query(F.data.startswith("se_delete:"))
async def delete_service_confirm(callback: CallbackQuery):
    service_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Удалить услугу?",
        reply_markup=confirm_delete_keyboard(service_id, "service")
    )


@router.callback_query(F.data.startswith("confirm_delete:service:"))
async def delete_service(callback: CallbackQuery):
    service_id = int(callback.data.split(":")[2])
    db = get_db()
    s = db.query(Service).filter(Service.id == service_id).first()
    if s:
        db.delete(s)
        db.commit()
    db.close()
    await callback.message.edit_text("✅ Услуга удалена.")


# Edit individual fields
FIELD_LABELS = {
    "se_name": ("name", "Введите новое название:"),
    "se_price": ("price", "Введите новую цену (цифры):"),
    "se_duration": ("duration", "Введите новую длительность:"),
    "se_desc": ("description", "Введите новое описание:"),
    "se_photo": ("photo", "Отправьте новое фото:"),
}


@router.callback_query(F.data.regexp(r"^se_(name|price|duration|desc|photo):\d+$"))
async def edit_field_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field_key = parts[0]
    service_id = int(parts[1])
    field_name, prompt = FIELD_LABELS[field_key]
    await state.update_data(editing_service_id=service_id, editing_field=field_name)
    await state.set_state(AdminState.editing_value)
    await callback.message.edit_text(prompt)


@router.message(IsAdmin(), AdminState.editing_value)
async def save_field(message: Message, state: FSMContext):
    data = await state.get_data()
    service_id = data["editing_service_id"]
    field = data["editing_field"]

    db = get_db()
    s = db.query(Service).filter(Service.id == service_id).first()

    if field == "photo":
        if message.photo:
            s.photo_file_id = message.photo[-1].file_id
        else:
            await message.answer("Отправьте фото!")
            db.close()
            return
    elif field == "price":
        try:
            s.price = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введите число!")
            db.close()
            return
    else:
        setattr(s, field, message.text.strip())

    db.commit()
    db.close()
    await state.clear()
    await message.answer("✅ Сохранено!", reply_markup=admin_main_keyboard())


# ========== СЛОТЫ ==========

@router.message(IsAdmin(), F.text == "📅 Слоты")
async def show_slots(message: Message, state: FSMContext):
    await state.clear()
    db = get_db()
    from datetime import date
    slots = db.query(TimeSlot).filter(TimeSlot.date >= date.today().isoformat()).order_by(
        TimeSlot.date, TimeSlot.time
    ).all()
    db.close()
    if not slots:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Добавить слоты", callback_data="add_slots")
        await message.answer("Слотов нет.", reply_markup=builder.as_markup())
    else:
        await message.answer("Текущие слоты:", reply_markup=slots_keyboard(slots))


@router.callback_query(F.data == "add_slots")
async def add_slots_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.adding_slots)
    await callback.message.edit_text(
        "Введите слоты в формате <code>ГГГГ-ММ-ДД ЧЧ:ММ</code>\n"
        "Каждый слот с новой строки.\n\n"
        "Пример:\n<code>2026-04-15 10:00\n2026-04-15 12:00\n2026-04-16 14:00</code>",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), AdminState.adding_slots)
async def add_slots_save(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    db = get_db()
    added, errors = [], []

    for line in lines:
        try:
            parts = line.strip().split(" ")
            date_val, time_val = parts[0], parts[1]
            exists = db.query(TimeSlot).filter(TimeSlot.date == date_val, TimeSlot.time == time_val).first()
            if exists:
                errors.append(f"⚠️ {date_val} {time_val} — уже есть")
                continue
            db.add(TimeSlot(date=date_val, time=time_val))
            added.append(f"✅ {date_val} {time_val}")
        except Exception:
            errors.append(f"❌ Ошибка: {line}")

    db.commit()
    db.close()
    await state.clear()
    result = "\n".join(added + errors)
    await message.answer(f"Результат:\n{result}", reply_markup=admin_main_keyboard())


@router.callback_query(F.data.startswith("del_slot:"))
async def delete_slot(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    slot_id = int(callback.data.split(":")[1])
    db = get_db()
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    if slot:
        info = f"{slot.date} {slot.time}"
        db.delete(slot)
        db.commit()
        await callback.answer(f"✅ {info} удалён")
    db.close()

    from datetime import date as d
    db2 = get_db()
    slots = db2.query(TimeSlot).filter(TimeSlot.date >= d.today().isoformat()).order_by(
        TimeSlot.date, TimeSlot.time
    ).all()
    db2.close()
    if slots:
        await callback.message.edit_reply_markup(reply_markup=slots_keyboard(slots))
    else:
        await callback.message.edit_text("Все слоты удалены.")


@router.callback_query(F.data == "close")
async def close_kb(callback: CallbackQuery):
    await callback.message.delete()


# ========== ЗАПИСИ ==========

@router.message(IsAdmin(), F.text == "📋 Записи")
async def show_bookings(message: Message):
    db = get_db()
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(20).all()
    db.close()

    if not bookings:
        await message.answer("Записей нет.")
        return

    text = "📋 <b>Последние 20 записей:</b>\n\n"
    for b in bookings:
        payment = "✅" if b.payment_verified else "⚠️"
        username_str = f"@{b.username}" if b.username else "нет"
        text += (
            f"#{b.id} {payment} <b>{b.client_name or b.full_name}</b> ({username_str})\n"
            f"   💅 {b.service_name} — {b.service_price} ₽\n"
            f"   📅 {b.date} {b.time}\n\n"
        )
    await message.answer(text, parse_mode="HTML")


# ========== СТАТИСТИКА ==========

@router.message(IsAdmin(), F.text == "📊 Статистика")
async def show_stats(message: Message):
    db = get_db()
    total = db.query(Booking).count()
    verified = db.query(Booking).filter(Booking.payment_verified == True).count()
    free_slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).count()
    services = db.query(Service).filter(Service.is_active == True).count()
    db.close()

    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"📋 Всего записей: {total}\n"
        f"✅ Оплата подтверждена: {verified}\n"
        f"📅 Свободных слотов: {free_slots}\n"
        f"💅 Активных услуг: {services}",
        parse_mode="HTML"
    )
