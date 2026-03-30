import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_db, TimeSlot, Booking
from keyboards.client_kb import services_keyboard, dates_keyboard, times_keyboard, confirm_keyboard

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SBP_PHONE = os.getenv("SBP_PHONE", "Номер не указан")
SBP_BANK = os.getenv("SBP_BANK", "")


class BookingState(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()
    waiting_payment = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💅 Добро пожаловать!\n\n"
        "Я помогу вам записаться на маникюр/педикюр.\n"
        "Выберите услугу:",
        reply_markup=services_keyboard()
    )
    await state.set_state(BookingState.choosing_service)


@router.callback_query(F.data.startswith("service:"), BookingState.choosing_service)
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)

    db = get_db()
    slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).all()
    db.close()

    if not slots:
        await callback.message.edit_text("😔 К сожалению, свободных слотов нет. Попробуйте позже.")
        await state.clear()
        return

    await callback.message.edit_text(
        f"✅ Услуга: <b>{service}</b>\n\nВыберите дату:",
        reply_markup=dates_keyboard(slots),
        parse_mode="HTML"
    )
    await state.set_state(BookingState.choosing_date)


@router.callback_query(F.data.startswith("date:"), BookingState.choosing_date)
async def choose_date(callback: CallbackQuery, state: FSMContext):
    date = callback.data.split(":", 1)[1]
    await state.update_data(date=date)

    db = get_db()
    slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).all()
    db.close()

    await callback.message.edit_text(
        f"📅 Дата: <b>{date}</b>\n\nВыберите время:",
        reply_markup=times_keyboard(slots, date),
        parse_mode="HTML"
    )
    await state.set_state(BookingState.choosing_time)


@router.callback_query(F.data == "back_to_dates", BookingState.choosing_time)
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    db = get_db()
    slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).all()
    db.close()

    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=dates_keyboard(slots)
    )
    await state.set_state(BookingState.choosing_date)


@router.callback_query(F.data.startswith("time:"), BookingState.choosing_time)
async def choose_time(callback: CallbackQuery, state: FSMContext):
    slot_id = int(callback.data.split(":")[1])

    db = get_db()
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    db.close()

    if not slot or slot.is_booked:
        await callback.answer("❌ Этот слот уже занят, выберите другой.", show_alert=True)
        return

    await state.update_data(slot_id=slot_id, time=slot.time)
    data = await state.get_data()

    await callback.message.edit_text(
        f"📋 <b>Ваша запись:</b>\n\n"
        f"💅 Услуга: {data['service']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {slot.time}\n\n"
        f"Всё верно?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BookingState.confirming)


@router.callback_query(F.data == "confirm_booking", BookingState.confirming)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"💳 <b>Оплата через СБП</b>\n\n"
        f"Переведите нужную сумму по номеру:\n"
        f"📱 <code>{SBP_PHONE}</code>\n"
        f"🏦 Банк: {SBP_BANK}\n\n"
        f"После оплаты отправьте скриншот подтверждения прямо сюда.",
        parse_mode="HTML"
    )
    await state.set_state(BookingState.waiting_payment)


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Запись отменена. Напишите /start чтобы начать заново.")


@router.message(BookingState.waiting_payment, F.photo)
async def receive_payment(message: Message, state: FSMContext):
    from utils.gemini import verify_payment_screenshot

    data = await state.get_data()
    db = get_db()

    # Скачиваем скриншот
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    await message.answer("⏳ Проверяю оплату...")

    try:
        is_valid, reason = await verify_payment_screenshot(image_bytes)
    except Exception as e:
        is_valid = False
        reason = "Ошибка при проверке. Мастер проверит вручную."

    # Блокируем слот
    slot = db.query(TimeSlot).filter(TimeSlot.id == data["slot_id"]).first()
    if slot:
        slot.is_booked = True

    # Создаём запись
    booking = Booking(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        service=data["service"],
        date=data["date"],
        time=data["time"],
        screenshot_file_id=photo.file_id,
        payment_verified=is_valid
    )
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()

    if is_valid:
        await message.answer(
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"Вы записаны:\n"
            f"💅 {data['service']}\n"
            f"📅 {data['date']} в {data['time']}\n\n"
            f"Ждём вас! 💅",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ <b>Не удалось подтвердить оплату автоматически.</b>\n"
            f"Причина: {reason}\n\n"
            f"Мастер проверит вручную и свяжется с вами.",
            parse_mode="HTML"
        )

    # Уведомляем мастера
    status_text = "✅ Оплата подтверждена" if is_valid else f"⚠️ Требует проверки: {reason}"
    username_str = f"@{message.from_user.username}" if message.from_user.username else "нет username"

    await message.bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Новая запись #{booking_id}</b>\n\n"
        f"👤 {message.from_user.full_name} ({username_str})\n"
        f"💅 {data['service']}\n"
        f"📅 {data['date']} в {data['time']}\n\n"
        f"💳 {status_text}",
        parse_mode="HTML"
    )
    await message.bot.send_photo(ADMIN_ID, photo.file_id, caption="Скриншот оплаты")

    await state.clear()


@router.message(BookingState.waiting_payment)
async def wrong_payment(message: Message):
    await message.answer("📸 Пожалуйста, отправьте скриншот оплаты как фотографию.")
