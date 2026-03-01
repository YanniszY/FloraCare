from pydantic import BaseModel
from datetime import date


class PlantCreate(BaseModel):
    name: str
    location: str
    water_interval_days: int
    last_watered: date | None = None


class PlantUpdate(BaseModel):
    name: str