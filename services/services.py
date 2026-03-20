from datetime import date, timedelta
from models import Plant


def plant_status(plant: Plant):
    today = date.today()
    next_watering = plant.last_watered + timedelta(days=plant.water_interval_days)
    days_left = (next_watering - today).days

    return {
        "next_watering": next_watering,
        "days_left": days_left,
        "needs_watering": days_left <= 0
    }