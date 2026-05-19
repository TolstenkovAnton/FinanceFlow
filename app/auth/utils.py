from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import bcrypt
import jwt
from app.auth.config import settings


def create_tokens(data: Dict) -> Dict[str, str]:
    now = datetime.now(timezone.utc)

    access_payload = data.copy()
    access_payload.update({
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": now,
        "type": "access",
    })
    access_token = jwt.encode(access_payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm)

    refresh_payload = data.copy()
    refresh_payload.update({
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "iat": now,
        "type": "refresh",
    })
    refresh_token = jwt.encode(refresh_payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm)

    return {"access_token": access_token, "refresh_token": refresh_token}


def verify_token(token: str) -> Optional[Dict]:
    try:
        return jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
    except Exception:
        return {"error": "Token verification failed"}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
