from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from starlette.requests import Request

from sqlalchemy.orm import Session
from models import User

from routers import plants, dashboard, ai
from fastapi.middleware.cors import CORSMiddleware
from services.notifier import start_scheduler

from database import engine, Base, get_db, SessionLocal  # добавил SessionLocal


def create_default_user(db: Session):
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, telegram_id=0)
        db.add(user)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):  # убрал лишний Depends
    # Старт
    start_scheduler()
    print("--- Планировщик запущен ---")

    db = SessionLocal()
    try:
        create_default_user(db)
    finally:
        db.close()

    yield
    # Выключение (если нужно что-то сделать — сюда)


app = FastAPI(lifespan=lifespan)  # один раз

Base.metadata.create_all(bind=engine)

app.include_router(plants.router)
app.include_router(dashboard.router)
app.include_router(ai.router, prefix="/ai")

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
    return templates.TemplateResponse(request, "index.html")


@app.get("/plants/{plant_id}/view")
def plant_detail(plant_id: int, request: Request):
    return templates.TemplateResponse(request, "plant.html")
    # return templates.TemplateResponse("plant.html", {"request": request})


@app.get("/ai")
def ai_page(request: Request):
    return templates.TemplateResponse(request, "ai-chat.html")
    # return templates.TemplateResponse("ai-chat.html", {"request": request})