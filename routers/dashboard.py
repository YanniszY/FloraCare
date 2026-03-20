from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import Plant, PlantHistory
from services.services import plant_status

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):

    plants = db.query(Plant).all()

    total_plants = len(plants)

    needs_watering = 0

    next_watering = None

    for plant in plants:

        status = plant_status(plant)

        if status["needs_watering"]:
            needs_watering += 1

        if not next_watering or status["next_watering"] < next_watering:
            next_watering = status["next_watering"]

    watered_today = (
        db.query(PlantHistory)
        .filter(
            PlantHistory.action == "watered",
            PlantHistory.created_at >= date.today()
        )
        .count()
    )

    return {
        "total_plants": total_plants,
        "needs_watering": needs_watering,
        "watered_today": watered_today,
        "next_watering": next_watering
    }



@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):

    total = db.query(Plant).count()

    plants = db.query(Plant).all()

    needs_water = 0

    for p in plants:
        status = plant_status(p)
        if status["needs_watering"]:
            needs_water += 1

    return {
        "total_plants": total,
        "needs_water": needs_water
    }



