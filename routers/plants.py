from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from db import get_db
from models import Plant, WateringLog
from schemas import PlantCreate, PlantUpdate
from services import plant_status

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("/")
def add_plant(plant: PlantCreate, db: Session = Depends(get_db)):
    new_plant = Plant(
        name=plant.name,
        location=plant.location,
        water_interval_days=plant.water_interval_days,
        last_watered=plant.last_watered or date.today()
    )

    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    return new_plant


@router.get("/")
def get_plants(db: Session = Depends(get_db)):
    plants = db.query(Plant).all()
    result = []

    for p in plants:
        status = plant_status(p)

        result.append({
            "id": p.id,
            "name": p.name,
            "nickname": p.nickname,
            "location": p.location,
            "last_watered": p.last_watered,
            "water_interval_days": p.water_interval_days,
            "next_watering": status["next_watering"],
            "days_left": status["days_left"],
            "needs_watering": status["needs_watering"]
        })

    return result


@router.delete("/{plant_id}")
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    db.delete(plant)
    db.commit()
    return {"status": "deleted"}


@router.put("/{plant_id}")
def edit_plant(
    plant_id: int,
    plant_data: PlantUpdate,
    db: Session = Depends(get_db)
):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant.name = plant_data.name
    db.commit()
    return {"status": "updated"}


@router.post("/{plant_id}/water")
def water_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant.last_watered = date.today()

    log = WateringLog(
        plant_id=plant.id,
        action="watered"
    )

    db.add(log)
    db.commit()

    return {"status": "watered"}


@router.get("/{plant_id}/history")
def get_watering_history(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    logs = (
        db.query(WateringLog)
        .filter_by(plant_id=plant_id)
        .order_by(WateringLog.done_at.desc())
        .all()
    )

    return logs