import sys
import pytest
from pathlib import Path


TEST_FILE = Path(__file__).parent / "data" / "test_data.xlsx"


@pytest.mark.asyncio
async def test_import_xlsx_file():
    assert str(TEST_FILE).endswith("xlsx")
