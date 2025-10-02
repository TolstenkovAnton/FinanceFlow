from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import crud, auth, special_funcs
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
BASE_DIR = Path(__file__).resolve().parent.parent

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = auth.get_current_user(request.cookies.get("session_token"))
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if crud.create_user(username, email, password):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})

@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = crud.authenticate_user(username, password)
    if user:
        token = auth.login_user(user)
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("session_token", token)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    auth.logout_user(token)
    return RedirectResponse("/login")

@app.post("/add-income")
async def add_income(request: Request, description: str = Form(...), amount: float = Form(...), currency: str = Form(...)):
    user = auth.get_current_user(request.cookies.get("session_token"))
    crud.add_income(user['id'], description, amount, currency)
    return RedirectResponse("/", status_code=302)

@app.post("/add-expense")
async def add_expense(request: Request, description: str = Form(...), amount: float = Form(...), currency: str = Form(...)):
    user = auth.get_current_user(request.cookies.get("session_token"))
    crud.add_expense(user['id'], description, amount, currency)
    return RedirectResponse("/", status_code=302)

@app.get("/data")
async def show_data(request: Request, month: str = ''):
    user = auth.get_current_user(request.cookies.get("session_token"))
    incomes, expenses = crud.get_user_data(user['id'], month)

    current_month = month or datetime.now().strftime("%Y-%m")
    totals = {}

    for income in incomes:
        cur = income["currency"]
        totals.setdefault(cur, {"income": 0, "expense": 0, "balance": 0})
        totals[cur]["income"] += income["amount"]

    for expense in expenses:
        cur = expense["currency"]
        totals.setdefault(cur, {"income": 0, "expense": 0, "balance": 0})
        totals[cur]["expense"] += expense["amount"]

    for cur in totals:
        totals[cur]["balance"] = totals[cur]["income"] - totals[cur]["expense"]

    return templates.TemplateResponse("data.html", {
        "request": request,
        "user": user,
        "incomes": incomes,
        "expenses": expenses,
        "month": month,
        "totals": totals
    })

@app.get("/analytics")
async def analytics(request: Request, currency: str = "RUB"):
    session_token = request.cookies.get("session_token")
    user = auth.get_current_user(session_token)
    if not user:
        return RedirectResponse("/login")

    incomes, expenses = crud.get_user_data(user['id'])

    incomes_converted = special_funcs.convert_all_to_currency(incomes, currency)
    expenses_converted = special_funcs.convert_all_to_currency(expenses, currency)

    income_categories = special_funcs.categorize_transactions(incomes_converted)
    expense_categories = special_funcs.categorize_transactions(expenses_converted)

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": user,
        "income_categories": income_categories,
        "expense_categories": expense_categories,
        "currency": currency
    })