from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from db_engine import get_db, init_db
from app import crud, auth, special_funcs
from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Finance Flow API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
BASE_DIR = Path(__file__).resolve().parent.parent

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_token = request.cookies.get("session_token")
    user = auth.get_current_user(user_token)
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "index.html", {"user": user})


@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...),
                   db: AsyncSession = Depends(get_db)):
    user = await crud.create_user(db, username, email, password)
    if user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "register.html", {"error": "Пользователь уже существует"})


@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                db: AsyncSession = Depends(get_db)):
    user = await crud.authenticate_user(db, username, password)
    if user:
        token = auth.login_user(user)
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("session_token", token)
        return response
    return templates.TemplateResponse(request, "login.html", {"error": "Неверные данные"})

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    auth.logout_user(token)
    response = RedirectResponse("/login")
    response.delete_cookie("session_token")
    return response

@app.post("/add-income")
async def add_income(request: Request, description: str = Form(...), amount: float = Form(...),
                     currency: str = Form(...),
                     db: AsyncSession = Depends(get_db)):
    user = auth.get_current_user(request.cookies.get("session_token"))
    await crud.add_income(db, user.id, description, amount, currency)
    return RedirectResponse("/", status_code=302)

@app.post("/add-expense")
async def add_expense(request: Request, description: str = Form(...), amount: float = Form(...),
                      currency: str = Form(...),
                      db: AsyncSession = Depends(get_db)):
    user = auth.get_current_user(request.cookies.get("session_token"))
    await crud.add_expense(db, user.id, description, amount, currency)
    return RedirectResponse("/", status_code=302)

@app.get("/data")
async def show_data(request: Request, month: str = '', db: AsyncSession = Depends(get_db)):
    user = auth.get_current_user(request.cookies.get("session_token"))
    if not user:
        return RedirectResponse("/login")

    incomes, expenses = await crud.get_user_data(db, user.id, month)

    incomes_dict = [i.__dict__ for i in incomes] if incomes else []
    expenses_dict = [e.__dict__ for e in expenses] if expenses else []

    current_month = month or datetime.now().strftime("%Y-%m")
    totals: Dict[str, Dict[str, float]] = {}

    for income in incomes_dict:
        cur = income.get("currency", "RUB")
        totals.setdefault(cur, {"income": 0.0, "expense": 0.0, "balance": 0.0})
        totals[cur]["income"] += float(income["amount"])

    for expense in expenses_dict:
        cur = expense.get("currency", "RUB")
        totals.setdefault(cur, {"income": 0.0, "expense": 0.0, "balance": 0.0})
        totals[cur]["expense"] += float(expense["amount"])

    for cur in totals:
        totals[cur]["balance"] = totals[cur]["income"] - totals[cur]["expense"]

    return templates.TemplateResponse(
        request, "data.html",
        {
            "user": user.__dict__,
            "incomes": incomes_dict,
            "expenses": expenses_dict,
            "month": month,
            "totals": totals,
        }
    )

@app.get("/analytics")
async def analytics(request: Request, month: str = '', currency: str = "RUB", db: AsyncSession = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    user = auth.get_current_user(session_token)
    if not user:
        return RedirectResponse("/login")

    incomes, expenses = await crud.get_user_data(db, user.id, month)

    incomes_converted = special_funcs.convert_all_to_currency([i.__dict__ for i in incomes], currency)
    expenses_converted = special_funcs.convert_all_to_currency([e.__dict__ for e in expenses], currency)

    income_categories = special_funcs.categorize_transactions(incomes_converted)
    expense_categories = special_funcs.categorize_transactions(expenses_converted)

    return templates.TemplateResponse(
        request, "analytics.html",
        {
            "user": user,
            "income_categories": income_categories,
            "expense_categories": expense_categories,
            "currency": currency,
        }
    )
