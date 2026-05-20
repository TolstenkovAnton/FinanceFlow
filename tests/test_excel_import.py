import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TEST_FILE = Path(__file__).parent / "data" / "test_data.xlsx"
TEST_DB   = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_import_xlsx_file():
    from app.main import app
    from app.models import Base
    from db_engine import get_db
    engine = create_async_engine(TEST_DB, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async def override_db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_db] = override_db
    fake_user = MagicMock()
    fake_user.id = 1
    try:
        with patch("app.main.get_user", new=AsyncMock(return_value=(fake_user, None))):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                raw = TEST_FILE.read_bytes()
                r = await client.post(
                    "/import",
                    files={"file": (TEST_FILE.stem + ".xlsx", raw,
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
    body = r.json()
    assert body["success"] is True, f"Ошибка импорта: {body.get('error')}"
    assert body["imported"] > 0, "Ни одна запись не была импортирована"
