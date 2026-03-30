import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter

from database import get_db, TimeSlot, Booking
from admin_kb import admin_main_keyboard, slots_delete_keyboard

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID


class AdminState(StatesGroup):
    adding_slot = State()


@router.message(IsAdmin(), F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👑 Панель администратора", reply_markup=admin_main_keyboard())


@router.message(IsAdmin(), F.text == "➕ Добавить слот")
async def add_slot_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите дату и время в формате:\n"
        "<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>\n\n"
        "Например: <code>2026-04-15 14:00</code>\n\n"
        "Можно несколько слотов — каждый с новой строки.",
        parse_mode="HTML"
    )
    await state.set_state(AdminState.adding_slot)


@router.message(IsAdmin(), AdminState.adding_slot)
async def add_slot_confirm(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    db = get_db()
    added = []
    errors = []

    for line in lines:
        line = line.strip()
        try:
            parts = line.split(" ")
            date = parts[0]
            time = parts[1]
            # Проверяем нет ли уже такого слота
            exists = db.query(TimeSlot).filter(
                TimeSlot.date == date, TimeSlot.time == time
            ).first()
            if exists:
                errors.append(f"⚠️ {date} {time} — уже существует")
                continue
            slot = TimeSlot(date=date, time=time)
            db.add(slot)
            added.append(f"✅ {date} {time}")
        except Exception:
            errors.append(f"❌ Ошибка в строке: {line}")

    db.commit()
    db.close()

    result = "\n".join(added + errors)
    await message.answer(f"Результат:\n{result}", reply_markup=admin_main_keyboard())
    await state.clear()


@router.message(IsAdmin(), F.text == "🗑 Удалить слот")
async def delete_slot_start(message: Message):
    db = get_db()
    slots = db.query(TimeSlot).order_by(TimeSlot.date, TimeSlot.time).all()
    db.close()

    if not slots:
        await message.answer("Слотов нет.")
        return

    await message.answer("Выберите слот для удаления:", reply_markup=slots_delete_keyboard(slots))


@router.callback_query(F.data.startswith("delete_slot:"))
async def delete_slot(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    slot_id = int(callback.data.split(":")[1])
    db = get_db()
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    if slot:
        db.delete(slot)
        db.commit()
        await callback.answer(f"✅ Слот {slot.date} {slot.time} удалён")
    db.close()

    # Обновляем список
    slots = db.query(TimeSlot).order_by(TimeSlot.date, TimeSlot.time).all() if False else []
    db2 = get_db()
    slots = db2.query(TimeSlot).order_by(TimeSlot.date, TimeSlot.time).all()
    db2.close()

    if slots:
        await callback.message.edit_reply_markup(reply_markup=slots_delete_keyboard(slots))
    else:
        await callback.message.edit_text("Все слоты удалены.")


@router.callback_query(F.data == "close")
async def close_keyboard(callback: CallbackQuery):
    await callback.message.delete()


@router.message(IsAdmin(), F.text == "📋 Все записи")
async def all_bookings(message: Message):
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
            f"#{b.id} {payment} <b>{b.full_name}</b> ({username_str})\n"
            f"   💅 {b.service}\n"
            f"   📅 {b.date} {b.time}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(IsAdmin(), F.text == "📅 Свободные слоты")
async def free_slots(message: Message):
    db = get_db()
    slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).order_by(
        TimeSlot.date, TimeSlot.time
    ).all()
    db.close()

    if not slots:
        await message.answer("Свободных слотов нет.")
        return

    text = "📅 <b>Свободные слоты:</b>\n\n"
    for s in slots:
        text += f"• {s.date} в {s.time}\n"

    await message.answer(text, parse_mode="HTML")
