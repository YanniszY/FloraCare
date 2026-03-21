from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request



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

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/plants/{plant_id}/view")
def plant_detail(plant_id: int, request: Request):
    return templates.TemplateResponse("plant.html", {"request": request})
