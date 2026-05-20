import io
import openpyxl
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
from fastapi import Depends, FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app import auth, crud, special_funcs
from db_engine import get_db, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Finance Flow API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
BASE_DIR = Path(__file__).resolve().parent.parent

COOKIE_ACCESS = "access_token"
COOKIE_REFRESH = "refresh_token"


def set_auth_cookies(response: Response, tokens: Dict[str, str]) -> None:
    response.set_cookie(COOKIE_ACCESS, tokens["access_token"], httponly=True, samesite="lax")
    response.set_cookie(COOKIE_REFRESH, tokens["refresh_token"], httponly=True, samesite="lax")


def delete_auth_cookies(response: Response) -> None:
    response.delete_cookie(COOKIE_ACCESS)
    response.delete_cookie(COOKIE_REFRESH)


async def get_user(request: Request, db: AsyncSession) -> Tuple:
    return await auth.get_authenticated_user(
        db,
        request.cookies.get(COOKIE_ACCESS),
        request.cookies.get(COOKIE_REFRESH),
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    response = templates.TemplateResponse(request, "index.html", {"user": user})
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()
    user = await crud.create_user(db, username, email, password)
    if user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "register.html", {"error": "Пользователь уже существует"})


@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()
    user = await crud.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Неверные данные"})
    tokens = await auth.login_user(db, user)
    response = RedirectResponse("/", status_code=302)
    set_auth_cookies(response, tokens)
    return response


@app.get("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    await auth.logout_user(db, request.cookies.get(COOKIE_ACCESS))
    response = RedirectResponse("/login")
    delete_auth_cookies(response)
    return response


@app.post("/import")
async def import_excel(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user, new_tokens = await get_user(request, db)
    if not user:
        return JSONResponse({"success": False, "error": "Не авторизован"}, status_code=401)
    if not file.filename.endswith((".xlsx", ".xls")):
        return JSONResponse({"success": False, "error": "Поддерживаются только файлы .xlsx / .xls"})
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
        imported = 0
        skipped = []
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row or not any(cell is not None for cell in row):
                continue
            if len(row) < 3:
                skipped.append(f"строка {i}: мало столбцов")
                continue
            type_val = str(row[0]).strip().lower() if row[0] is not None else ""
            description = str(row[1]).strip() if row[1] is not None else ""
            amount_raw = row[2]
            currency = str(row[3]).strip().upper() if len(row) > 3 and row[3] else "RUB"
            if currency not in ("RUB", "USD", "EUR"):
                currency = "RUB"
            try:
                amount = float(amount_raw)
            except (ValueError, TypeError):
                skipped.append(f"строка {i}: некорректная сумма")
                continue
            if not description:
                skipped.append(f"строка {i}: пустое описание")
                continue
            if type_val in ("доход", "income", "доходы"):
                await crud.add_income(db, user.id, description, amount, currency)
                imported += 1
            elif type_val in ("расход", "expense", "расходы"):
                await crud.add_expense(db, user.id, description, amount, currency)
                imported += 1
            else:
                skipped.append(f"строка {i}: неизвестный тип «{row[0]}»")
        response_data: Dict = {"success": True, "imported": imported}
        if skipped:
            response_data["skipped"] = skipped
        resp = JSONResponse(response_data)
        if new_tokens:
            set_auth_cookies(resp, new_tokens)
        return resp
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@app.post("/add-income")
async def add_income(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    await crud.add_income(db, user.id, description, amount, currency)
    response = RedirectResponse("/", status_code=302)
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


@app.post("/add-expense")
async def add_expense(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    await crud.add_expense(db, user.id, description, amount, currency)
    response = RedirectResponse("/", status_code=302)
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


@app.get("/data")
async def show_data(request: Request, month: str = "", db: AsyncSession = Depends(get_db)):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    incomes, expenses = await crud.get_user_data(db, user.id, month)

    incomes_dict = [i.__dict__ for i in incomes] if incomes else []
    expenses_dict = [e.__dict__ for e in expenses] if expenses else []

    # current_month = month or datetime.now().strftime("%Y-%m")
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

    response = templates.TemplateResponse(
        request,
        "data.html",
        {
            "user": user.__dict__,
            "incomes": incomes_dict,
            "expenses": expenses_dict,
            "month": month,
            "totals": totals,
        },
    )
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


MONTH_NAMES_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


@app.get("/profile")
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    current_month = datetime.now().strftime("%Y-%m")
    incomes, expenses = await crud.get_user_data(db, user.id, current_month)

    totals: Dict[str, Dict[str, float]] = {}
    for income in incomes:
        cur = income.currency
        totals.setdefault(cur, {"income": 0.0, "expense": 0.0, "balance": 0.0})
        totals[cur]["income"] += float(income.amount)
    for expense in expenses:
        cur = expense.currency
        totals.setdefault(cur, {"income": 0.0, "expense": 0.0, "balance": 0.0})
        totals[cur]["expense"] += float(expense.amount)
    for cur in totals:
        totals[cur]["balance"] = totals[cur]["income"] - totals[cur]["expense"]

    total_expenses_rub = totals.get("RUB", {}).get("expense", 0.0)
    limit = float(user.monthly_limit) if user.monthly_limit else 0.0
    spent_percent = min(round(total_expenses_rub / limit * 100) if limit > 0 else 0, 100)

    response = templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user": user,
            "total_expenses_rub": total_expenses_rub,
            "spent_percent": spent_percent,
            "success": request.query_params.get("success"),
            "totals": totals,
            "month_name": MONTH_NAMES_RU[datetime.now().month],
            "income_count": len(incomes),
            "expense_count": len(expenses),
        },
    )
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


@app.post("/profile/limit")
async def update_limit(
    request: Request,
    monthly_limit: float = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    await crud.update_monthly_limit(db, user.id, monthly_limit)
    response = RedirectResponse("/profile?success=1", status_code=302)
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response


@app.get("/analytics")
async def analytics(
    request: Request,
    month: str = "",
    currency: str = "RUB",
    db: AsyncSession = Depends(get_db),
):
    user, new_tokens = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    incomes, expenses = await crud.get_user_data(db, user.id, month)

    incomes_converted = special_funcs.convert_all_to_currency([i.__dict__ for i in incomes], currency)
    expenses_converted = special_funcs.convert_all_to_currency([e.__dict__ for e in expenses], currency)

    income_categories = special_funcs.categorize_transactions(incomes_converted)
    expense_categories = special_funcs.categorize_transactions(expenses_converted)

    response = templates.TemplateResponse(
        request,
        "analytics.html",
        {
            "user": user,
            "income_categories": income_categories,
            "expense_categories": expense_categories,
            "currency": currency,
        },
    )
    if new_tokens:
        set_auth_cookies(response, new_tokens)
    return response
