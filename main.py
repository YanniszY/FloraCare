from fastapi import FastAPI
from routers import plants, dashboard
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(plants.router)
app.include_router(dashboard.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"message": "PlantCare работает!"}