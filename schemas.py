from pydantic import BaseModel
from datetime import date


class PlantCreate(BaseModel):
    name: str
    location: str
    water_interval_days: int
    last_watered: date | None = None

    nickname: str | None = None
    notes: str | None = None


class PlantUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    water_interval_days: int | None = None
    nickname: str | None = None
    notes: str | None = None