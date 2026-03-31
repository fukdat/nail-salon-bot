import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, BigInteger, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    duration = Column(String, nullable=False)   # "2 ч 30 мин"
    description = Column(Text, nullable=True)
    photo_file_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    is_booked = Column(Boolean, default=False)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    service_name = Column(String, nullable=False)
    service_price = Column(Integer, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    screenshot_file_id = Column(String, nullable=True)
    payment_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


DEFAULT_SERVICES = [
    {
        "name": "Маникюр без покрытия",
        "price": 1200,
        "duration": "2 часа",
        "description": (
            "Чистота и естественность — иногда этого достаточно. Маникюр без покрытия — это тщательный уход "
            "за ногтями и кутикулой без нанесения лака. Ногти приобретают аккуратную форму, ухоженный вид "
            "и здоровый естественный блеск.\n\n"
            "Идеальный выбор для тех, кто предпочитает минимализм или даёт ногтям отдохнуть между покрытиями."
        ),
    },
    {
        "name": "Классический маникюр с покрытием",
        "price": 2100,
        "duration": "2 ч 40 мин",
        "description": (
            "Ухоженные, аккуратные ногти — основа любого образа. Классический маникюр с покрытием включает "
            "полную обработку ногтей и кутикулы, придание желаемой формы и нанесение стойкого гель-лака "
            "любого цвета на ваш выбор.\n\n"
            "Результат держится до 3–4 недель, сохраняя глянец и насыщенность цвета с первого до последнего дня."
        ),
    },
    {
        "name": "Наращивание на верхние формы",
        "price": 2900,
        "duration": "3 часа",
        "description": (
            "Длина, форма и безупречный вид — всё это возможно с наращиванием на верхние формы. Технология "
            "позволяет создать красивые длинные ногти любой формы с нуля, даже если натуральные ногти "
            "короткие или ломкие.\n\n"
            "Результат — прочные, лёгкие ногти с идеальным изгибом, которые выглядят естественно и держат "
            "форму на протяжении всего срока носки."
        ),
    },
    {
        "name": "Педикюр с покрытием",
        "price": 2500,
        "duration": "2 ч 30 мин",
        "description": (
            "Полный уход за стопами и ногтями ног с нанесением стойкого гель-лака. Включает аппаратную "
            "обработку, удаление огрубевшей кожи, уход за кутикулой и покрытие на выбор.\n\n"
            "После педикюра ноги выглядят ухоженно и свежо на протяжении нескольких недель."
        ),
    },
    {
        "name": "Маникюр + Педикюр",
        "price": 3800,
        "duration": "4 часа",
        "description": (
            "Комплексный уход за руками и ногами в одном визите. Полная обработка ногтей и кутикулы "
            "на руках и ногах, покрытие гель-лаком на ваш выбор.\n\n"
            "Выгоднее, чем записываться по отдельности — и результат сразу везде!"
        ),
    },
]


def migrate_db():
    """Add missing columns to existing tables"""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS client_name VARCHAR"))
            conn.commit()
        except Exception:
            pass


def init_db():
    Base.metadata.create_all(engine)
    migrate_db()
    seed_services()


def seed_services():
    """Add default services if table is empty"""
    db = SessionLocal()
    try:
        count = db.query(Service).count()
        if count == 0:
            for s in DEFAULT_SERVICES:
                db.add(Service(
                    name=s["name"],
                    price=s["price"],
                    duration=s["duration"],
                    description=s["description"],
                    is_active=True
                ))
            db.commit()
    finally:
        db.close()


def get_db():
    return SessionLocal()