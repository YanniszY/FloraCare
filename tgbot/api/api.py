import requests

API = "http://127.0.0.1:8000"


def get_plants():

    r = requests.get(f"{API}/plants")
    return r.json()


def get_dashboard():

    r = requests.get(f"{API}/dashboard")
    return r.json()


def water_all_plants():
    return requests.post(f"{API}/plants/water-all")



def water_plant(plant_id):
    return requests.post(f"{API}/plants/{plant_id}/water")