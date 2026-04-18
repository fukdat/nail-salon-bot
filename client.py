import os
from datetime import date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_db, Service, TimeSlot, Booking
from client_kb import (
    main_menu_keyboard, simple_back_keyboard, service_keyboard,
    calendar_keyboard, times_keyboard, confirm_keyboard, payment_keyboard
)

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SBP_PHONE = os.getenv("SBP_PHONE", "Номер не указан")
SBP_BANK = os.getenv("SBP_BANK", "")
MASTER_NAME = os.getenv("MASTER_NAME", "Мастер")
SALON_ADDRESS = os.getenv("SALON_ADDRESS", "Адрес не указан")


class BookingState(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    confirming = State()
    waiting_payment = State()


# ========== ГЛАВНОЕ МЕНЮ ==========

async def show_main_menu(target, state: FSMContext = None):
    text = (
        f"Привет, я {MASTER_NAME} 💅\n\n"
        "Очень рада видеть тебя здесь!\n"
        "Это мой уютный бот для записи на маникюр.\n\n"
        "Здесь легко:\n"
        "• выбрать услугу\n"
        "• подобрать удобные дату и время\n"
        "• подтвердить запись в пару кликов\n\n"
        "Буду ждать тебя на красивый маникюр 🖤\n"
        "Выбери, с чего начнём ⚡"
    )
    if state:
        await state.clear()
    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu_keyboard())
    else:
        try:
            await target.message.edit_text(text, reply_markup=main_menu_keyboard())
        except Exception:
            await target.message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await show_main_menu(message, state)


@router.callback_query(F.data == "to_menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    await show_main_menu(callback, state)


# ========== АДРЕС / РАБОТЫ ==========

@router.callback_query(F.data == "menu:address")
async def show_address(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📍 <b>Адрес:</b>\n{SALON_ADDRESS}",
        reply_markup=simple_back_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "menu:portfolio")
async def show_portfolio(callback: CallbackQuery):
    await callback.message.edit_text(
        "🖼 Работы мастера скоро появятся здесь!",
        reply_markup=simple_back_keyboard()
    )


# ========== КАРУСЕЛЬ УСЛУГ ==========

async def show_service_page(callback: CallbackQuery, index: int, state: FSMContext):
    db = get_db()
    services = db.query(Service).filter(Service.is_active == True).all()
    db.close()

    if not services:
        await callback.message.edit_text(
            "😔 Пока нет доступных услуг.",
            reply_markup=simple_back_keyboard()
        )
        return

    index = max(0, min(index, len(services) - 1))
    s = services[index]
    await state.update_data(service_index=index)

    caption = (
        f"✨ <b>{s.name}</b>\n"
        f"💰 Цена: {s.price} ₽\n"
        f"⏱ Длительность: {s.duration}\n\n"
        f"{s.description or ''}"
    )
    kb = service_keyboard(s.id, index, len(services))

    if s.photo_file_id:
        try:
            await callback.message.edit_media(
                InputMediaPhoto(media=s.photo_file_id, caption=caption, parse_mode="HTML"),
                reply_markup=kb
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer_photo(s.photo_file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
    else:
        try:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "menu:book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.choosing_service)
    await show_service_page(callback, 0, state)


@router.callback_query(F.data.startswith("service_page:"))
async def flip_service(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    await show_service_page(callback, index, state)


@router.callback_query(F.data.startswith("back_to_services:"))
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("service_index", 0)
    await state.set_state(BookingState.choosing_service)
    await show_service_page(callback, index, state)


# ========== КАЛЕНДАРЬ ==========

async def show_calendar(callback: CallbackQuery, service_id: int, year: int, month: int, state: FSMContext):
    db = get_db()
    slots = db.query(TimeSlot).filter(TimeSlot.is_booked == False).all()
    db.close()

    available_dates = list(set(s.date for s in slots if s.date >= date.today().isoformat()))
    await state.update_data(service_id=service_id)

    kb = calendar_keyboard(year, month, available_dates, service_id)
    text = "📅 <b>Выберите дату</b>\n\nПоказываем только доступные дни."

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("book_service:"))
async def book_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    today = date.today()
    await state.set_state(BookingState.choosing_date)
    await show_calendar(callback, service_id, today.year, today.month, state)


@router.callback_query(F.data.startswith("cal_prev:"))
async def cal_prev(callback: CallbackQuery, state: FSMContext):
    _, year, month, service_id = callback.data.split(":")
    year, month, service_id = int(year), int(month), int(service_id)
    month -= 1
    if month < 1:
        month, year = 12, year - 1
    await show_calendar(callback, service_id, year, month, state)


@router.callback_query(F.data.startswith("cal_next:"))
async def cal_next(callback: CallbackQuery, state: FSMContext):
    _, year, month, service_id = callback.data.split(":")
    year, month, service_id = int(year), int(month), int(service_id)
    month += 1
    if month > 12:
        month, year = 1, year + 1
    await show_calendar(callback, service_id, year, month, state)


@router.callback_query(F.data == "ignore")
async def ignore(callback: CallbackQuery):
    await callback.answer()


# ========== ВЫБОР ВРЕМЕНИ ==========

async def show_times(callback: CallbackQuery, selected_date: str, service_id: int):
    db = get_db()
    slots = db.query(TimeSlot).filter(
        TimeSlot.date == selected_date,
        TimeSlot.is_booked == False
    ).all()
    db.close()

    if not slots:
        await callback.answer("На эту дату нет свободных слотов", show_alert=True)
        return

    kb = times_keyboard(slots, selected_date, service_id)
    try:
        await callback.message.edit_text(
            f"⏰ <b>Выберите время</b>\nДата: <b>{selected_date}</b>\n\nВыберите удобный слот:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            f"⏰ <b>Выберите время</b>\nДата: <b>{selected_date}</b>\n\nВыберите удобный слот:",
            reply_markup=kb,
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("select_date:"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split(":")[1]
    await state.update_data(selected_date=selected_date)
    await state.set_state(BookingState.choosing_time)
    data = await state.get_data()
    await show_times(callback, selected_date, data["service_id"])


@router.callback_query(F.data.startswith("back_to_calendar:"))
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    today = date.today()
    await state.set_state(BookingState.choosing_date)
    await show_calendar(callback, service_id, today.year, today.month, state)


@router.callback_query(F.data.startswith("back_to_times:"))
async def back_to_times(callback: CallbackQuery, state: FSMContext):
    _, selected_date, service_id = callback.data.split(":")
    await state.set_state(BookingState.choosing_time)
    await show_times(callback, selected_date, int(service_id))


# ========== ВВОД ИМЕНИ ==========

@router.callback_query(F.data.startswith("select_time:"), BookingState.choosing_time)
async def select_time(callback: CallbackQuery, state: FSMContext):
    slot_id = int(callback.data.split(":")[1])
    db = get_db()
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    db.close()

    if not slot or slot.is_booked:
        await callback.answer("❌ Этот слот уже занят, выберите другой.", show_alert=True)
        return

    await state.update_data(slot_id=slot_id, slot_time=slot.time)
    await state.set_state(BookingState.entering_name)

    try:
        await callback.message.edit_text(
            "👤 <b>Как к вам обращаться?</b>\n\nВведите ваше имя.",
            reply_markup=simple_back_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            "👤 <b>Как к вам обращаться?</b>\n\nВведите ваше имя.",
            reply_markup=simple_back_keyboard(),
            parse_mode="HTML"
        )


@router.message(BookingState.entering_name)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text.strip())
    data = await state.get_data()

    db = get_db()
    service = db.query(Service).filter(Service.id == data["service_id"]).first()
    db.close()

    await state.update_data(service_name=service.name, service_price=service.price)
    await state.set_state(BookingState.confirming)

    await message.answer(
        f"📋 <b>Ваша запись:</b>\n\n"
        f"👤 Имя: {data['client_name']}\n"
        f"💅 Услуга: {service.name}\n"
        f"💰 Цена: {service.price} ₽\n"
        f"📅 Дата: {data['selected_date']}\n"
        f"🕐 Время: {data['slot_time']}\n\n"
        f"Всё верно?",
        reply_markup=confirm_keyboard(data["slot_id"], data["selected_date"], data["service_id"]),
        parse_mode="HTML"
    )


# ========== БЛИЖАЙШИЙ СЛОТ ==========

@router.callback_query(F.data.startswith("quick_service:"))
async def quick_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    db = get_db()
    today_str = date.today().isoformat()
    slot = db.query(TimeSlot).filter(
        TimeSlot.is_booked == False,
        TimeSlot.date >= today_str
    ).order_by(TimeSlot.date, TimeSlot.time).first()
    db.close()

    if not slot:
        await callback.answer("😔 Нет доступных слотов", show_alert=True)
        return

    await state.update_data(service_id=service_id, selected_date=slot.date, slot_id=slot.id, slot_time=slot.time)
    await state.set_state(BookingState.entering_name)
    try:
        await callback.message.edit_text(
            f"⚡ Ближайший слот: <b>{slot.date} в {slot.time}</b>\n\n"
            f"👤 <b>Как к вам обращаться?</b>\n\nВведите ваше имя.",
            reply_markup=simple_back_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            f"⚡ Ближайший слот: <b>{slot.date} в {slot.time}</b>\n\n"
            f"👤 <b>Как к вам обращаться?</b>\n\nВведите ваше имя.",
            reply_markup=simple_back_keyboard(),
            parse_mode="HTML"
        )


# ========== ОПЛАТА ==========

@router.callback_query(F.data == "confirm_booking", BookingState.confirming)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.waiting_payment)
    await callback.message.edit_text(
        f"💳 <b>Оплата через СБП</b>\n\n"
        f"Переведите нужную сумму по номеру:\n"
        f"📱 <code>{SBP_PHONE}</code>\n"
        f"🏦 Банк: {SBP_BANK}\n\n"
        f"После оплаты отправьте скриншот подтверждения сюда.",
        reply_markup=payment_keyboard(),
        parse_mode="HTML"
    )


@router.message(BookingState.waiting_payment, F.photo)
async def receive_payment(message: Message, state: FSMContext):
    from gemini import verify_payment_screenshot

    data = await state.get_data()
    await message.answer("⏳ Проверяю оплату...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    try:
        is_valid, reason = await verify_payment_screenshot(image_bytes)
    except Exception:
        is_valid = False
        reason = "Ошибка при проверке. Мастер проверит вручную."

    db = get_db()
    slot = db.query(TimeSlot).filter(TimeSlot.id == data["slot_id"]).first()
    if slot:
        slot.is_booked = True

    booking = Booking(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        client_name=data.get("client_name"),
        service_name=data["service_name"],
        service_price=data["service_price"],
        date=data["selected_date"],
        time=data["slot_time"],
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
            f"💅 {data['service_name']}\n"
            f"📅 {data['selected_date']} в {data['slot_time']}\n\n"
            f"Ждём вас! 💅",
            reply_markup=payment_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ <b>Не удалось подтвердить оплату автоматически.</b>\n"
            f"Причина: {reason}\n\n"
            f"Мастер проверит вручную и свяжется с вами.",
            reply_markup=payment_keyboard(),
            parse_mode="HTML"
        )

    username_str = f"@{message.from_user.username}" if message.from_user.username else "нет"
    payment_status = "✅ Оплата подтверждена" if is_valid else f"⚠️ Требует проверки: {reason}"

    await message.bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Новая запись #{booking_id}</b>\n\n"
        f"👤 {data.get('client_name')} ({username_str})\n"
        f"💅 {data['service_name']} — {data['service_price']} ₽\n"
        f"📅 {data['selected_date']} в {data['slot_time']}\n\n"
        f"💳 {payment_status}",
        parse_mode="HTML"
    )
    await message.bot.send_photo(ADMIN_ID, photo.file_id, caption="Скриншот оплаты")
    await state.clear()


@router.message(BookingState.waiting_payment)
async def wrong_payment(message: Message):
    await message.answer("📸 Пожалуйста, отправьте скриншот оплаты как фотографию.")