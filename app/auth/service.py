from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import crud as auth_crud
from app.auth import utils as auth_utils
from app.crud import get_user_by_id
from app.models import User


async def login_user(db: AsyncSession, user: User) -> Dict[str, str]:
    tokens = auth_utils.create_tokens({"sub": str(user.id)})
    await auth_crud.save_user_tokens(db, user.id, tokens["access_token"], tokens["refresh_token"])
    return tokens


async def logout_user(db: AsyncSession, access_token: Optional[str]) -> None:
    if not access_token:
        return
    token_record = await auth_crud.get_token_by_access(db, access_token)
    if token_record:
        await auth_crud.revoke_user_tokens(db, token_record.user_id)


async def get_current_user(db: AsyncSession, access_token: Optional[str]) -> Optional[User]:
    if not access_token:
        return None
    payload = auth_utils.verify_token(access_token)
    if not payload or "error" in payload or payload.get("type") != "access":
        return None
    token_record = await auth_crud.get_token_by_access(db, access_token)
    if not token_record:
        return None
    return await get_user_by_id(db, int(payload["sub"]))


async def refresh_tokens(db: AsyncSession, refresh_token: Optional[str]) -> Optional[Dict[str, str]]:
    if not refresh_token:
        return None
    payload = auth_utils.verify_token(refresh_token)
    if not payload or "error" in payload or payload.get("type") != "refresh":
        return None
    token_record = await auth_crud.get_token_by_refresh(db, refresh_token)
    if not token_record:
        return None
    new_tokens = auth_utils.create_tokens({"sub": str(token_record.user_id)})
    await auth_crud.update_user_tokens(db, token_record, new_tokens["access_token"], new_tokens["refresh_token"])
    return new_tokens


async def get_authenticated_user(
    db: AsyncSession, access_token: Optional[str], refresh_token: Optional[str]
) -> Tuple[Optional[User], Optional[Dict[str, str]]]:
    user = await get_current_user(db, access_token)
    if user:
        return user, None
    new_tokens = await refresh_tokens(db, refresh_token)
    if new_tokens:
        user = await get_current_user(db, new_tokens["access_token"])
        return user, new_tokens
    return None, None
