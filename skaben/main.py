from fastapi import FastAPI

from skaben.database import engine
from skaben.models.base import Base
from skaben.utils import get_logger

logger = get_logger(__name__)

app = FastAPI(title="SKABEN API", version="0.1")

#app.include_router(stuff_router)
#app.include_router(nonsense_router)


# async def start_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     await engine.dispose()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    # await start_db()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
