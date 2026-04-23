"""Database migration script for Phase 10."""
import asyncio
from src_v2.infrastructure.database.base import engine, Base
from src_v2.infrastructure.database.models import ReportModel


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")


if __name__ == "__main__":
    asyncio.run(main())
