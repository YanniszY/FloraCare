from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from datetime import date, datetime

from database import Base


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    location = Column(String)
    water_interval_days = Column(Integer, default=7)
    last_watered = Column(Date, default=date.today)

    action = Column(String)

    fertilizer_name = Column(String)
    fertilizer_interval_days = Column(Integer)
    last_fertilized = Column(Date)

    notes = Column(String)
    nickname = Column(String)
    purchase_date = Column(Date)
    photo_path = Column(String)


class WateringLog(Base):
    __tablename__ = "watering_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    action = Column(String)
    done_at = Column(DateTime, default=datetime.utcnow)


class PlantHistory(Base):
    __tablename__ = "plant_history"

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    action = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)