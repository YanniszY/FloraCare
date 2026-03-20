from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers import plants, dashboard
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.notifier import start_scheduler

from database import engine, Base

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код здесь выполнится ПРИ СТАРТЕ сервера
    start_scheduler()
    print("--- Планировщик запущен ---")
    yield
    # Код здесь выполнится ПРИ ВЫКЛЮЧЕНИИ сервера
app = FastAPI(lifespan=lifespan)







Base.metadata.create_all(bind=engine)

app.include_router(plants.router)
app.include_router(dashboard.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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