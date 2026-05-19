from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserToken


async def save_user_tokens(db: AsyncSession, user_id: int, access_token: str, refresh_token: str) -> UserToken:
    await db.execute(delete(UserToken).where(UserToken.user_id == user_id))
    token = UserToken(user_id=user_id, access_token=access_token, refresh_token=refresh_token)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def get_token_by_access(db: AsyncSession, access_token: str) -> Optional[UserToken]:
    result = await db.execute(select(UserToken).where(UserToken.access_token == access_token))
    return result.scalar_one_or_none()


async def get_token_by_refresh(db: AsyncSession, refresh_token: str) -> Optional[UserToken]:
    result = await db.execute(select(UserToken).where(UserToken.refresh_token == refresh_token))
    return result.scalar_one_or_none()


async def revoke_user_tokens(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(UserToken).where(UserToken.user_id == user_id))
    await db.commit()


async def update_user_tokens(
    db: AsyncSession, token_record: UserToken, access_token: str, refresh_token: str
) -> UserToken:
    token_record.access_token = access_token
    token_record.refresh_token = refresh_token
    await db.commit()
    await db.refresh(token_record)
    return token_record
