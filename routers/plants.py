from sqlalchemy.orm import Session
from datetime import date
from schemas import PlantCreate, PlantUpdate
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import or_
import shutil

from database import get_db
from models import Plant, PlantHistory
from services.services import plant_status

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

    history = PlantHistory(
        plant_id=new_plant.id,
        action="created"
    )

    db.add(history)
    db.commit()

    return new_plant


@router.get("/")
def get_plants(
    search: str | None = None,
    location: str | None = None,
    needs_water: bool | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(Plant)

    if search:
        query = query.filter(
            or_(
                Plant.name.ilike(f"%{search}%"),
                Plant.nickname.ilike(f"%{search}%")
            )
        )

    if location:
        query = query.filter(Plant.location.ilike(f"%{location}%"))

    plants = query.all()

    result = []

    for p in plants:
        status = plant_status(p)

        if needs_water and not status["needs_watering"]:
            continue

        result.append({
            "id": p.id,
            "name": p.name,
            "nickname": p.nickname,
            "location": p.location,
            "photo": p.photo_path,
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

    history = PlantHistory(
        plant_id=plant.id,
        action="deleted"
    )

    db.add(history)

    db.delete(plant)
    db.commit()

    return {"status": "deleted"}


@router.put("/{plant_id}")
def edit_plant(
    plant_id: int,
    data: PlantUpdate,
    db: Session = Depends(get_db)
):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant.name = data.name

    history = PlantHistory(
        plant_id=plant.id,
        action="renamed"
    )

    db.add(history)

    db.commit()
    db.refresh(plant)

    return plant


@router.post("/{plant_id}/water")
def water_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant.last_watered = date.today()

    history = PlantHistory(
        plant_id=plant.id,
        action="watered"
    )

    db.add(history)
    db.commit()

    return {"status": "watered"}


@router.get("/{plant_id}/history")
def get_history(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    history = (
        db.query(PlantHistory)
        .filter_by(plant_id=plant_id)
        .order_by(PlantHistory.created_at.desc())
        .all()
    )

    return history



@router.post("/{plant_id}/photo")
def upload_photo(plant_id: int, file: UploadFile = File(), db: Session = Depends(get_db)):

    plant = db.query(Plant).filter_by(id=plant_id).first()

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    path = f"uploads/{plant_id}_{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    plant.photo_path = path
    db.commit()

    return {"photo": path}


@router.get("/needs-water")
def plants_need_water(db: Session = Depends(get_db)):
    
    plants = db.query(Plant).all()

    result = []

    for p in plants:
        status = plant_status(p)

        if status["needs_watering"]:
            result.append(p)

    return result



@router.post("/water-all")
def water_all_plants(db: Session = Depends(get_db)):

    plants = db.query(Plant).all()

    if not plants:
        raise HTTPException(status_code=404, detail="No plants found")

    count = 0

    for p in plants:

        status = plant_status(p)

        if status["needs_watering"]:

            p.last_watered = date.today()

            history = PlantHistory(
                plant_id=p.id,
                action="watered"
            )

            db.add(history)

            count += 1

    db.commit()

    return {
        "status": "watered",
        "updated": count
    }