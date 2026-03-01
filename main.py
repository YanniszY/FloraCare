from fastapi import FastAPI

from db import engine, Base
from routers import plants

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(plants.router)


@app.get("/")
def index():
    return {"message": "PlantCare работает!"}