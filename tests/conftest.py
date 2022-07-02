import pytest
import pytest_asyncio
from httpx import AsyncClient

from skaben.database import engine
from skaben.main import skaben
from skaben.models.base import Base


@pytest.fixture(
    params=[
        pytest.param(("asyncio", {"use_uvloop": True}), id="asyncio+uvloop"),
    ]
)
def anyio_backend(request):
    return request.param


async def start_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        skaben=skaben,
        base_url="http://testserver/v1",
        headers={"Content-Type": "application/json"},
    ) as client:
        await start_db()
        yield client
        # for AsyncEngine created in function scope, close and
        # clean-up pooled connections
        await engine.dispose()
