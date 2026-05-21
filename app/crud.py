from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models import User, Income, Expense
from app.auth.utils import hash_password, verify_password
from typing import Optional


async def create_user(db: AsyncSession, username: str, email: str, password: str) -> bool:
    try:
        db_user = User(username=username, email=email, password=hash_password(password))
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return True
    except Exception:
        await db.rollback()
        return False


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password):
        return user
    return None


async def add_income(db: AsyncSession, user_id: int, description: str, amount: float, currency: str = "RUB"):
    income = Income(user_id=user_id, description=description, amount=amount, currency=currency)
    db.add(income)
    await db.commit()
    await db.refresh(income)
    return income


async def add_expense(db: AsyncSession, user_id: int, description: str, amount: float, currency: str = "RUB"):
    expense = Expense(user_id=user_id, description=description, amount=amount, currency=currency)
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def get_user_data(
    db: AsyncSession,
    user_id: int,
    year: Optional[str] = "",
    month: Optional[str] = "",
):
    stmt_incomes = select(Income).where(Income.user_id == user_id)
    stmt_expenses = select(Expense).where(Expense.user_id == user_id)

    if year and month:
        month_date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
        stmt_incomes = stmt_incomes.where(
            func.date_trunc("month", Income.created_at) == month_date
        )
        stmt_expenses = stmt_expenses.where(
            func.date_trunc("month", Expense.created_at) == month_date
        )
    elif year:
        stmt_incomes = stmt_incomes.where(
            func.extract("year", Income.created_at) == int(year)
        )
        stmt_expenses = stmt_expenses.where(
            func.extract("year", Expense.created_at) == int(year)
        )
    elif month:
        stmt_incomes = stmt_incomes.where(
            func.extract("month", Income.created_at) == int(month)
        )
        stmt_expenses = stmt_expenses.where(
            func.extract("month", Expense.created_at) == int(month)
        )

    result_incomes = await db.execute(stmt_incomes)
    result_expenses = await db.execute(stmt_expenses)
    return result_incomes.scalars().all(), result_expenses.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_monthly_limit(db: AsyncSession, user_id: int, new_limit: float):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.monthly_limit = new_limit
        await db.commit()
        await db.refresh(user)
        return user
    return None


async def get_total_expenses_for_month(db: AsyncSession, user_id: int, month_str: str) -> float:
    month_start = f"{month_str}-01"
    stmt = select(func.sum(Expense.amount)).where(
        and_(Expense.user_id == user_id, func.date_trunc('month', Expense.created_at) == month_start)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0.0
