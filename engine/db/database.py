"""
Database connection pool and session management.
"""
import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import config

logger = logging.getLogger(__name__)

engine = create_async_engine(
    config.DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    """Provide a transactional scope for database operations."""
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables from schema.sql."""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema = f.read()

    async with engine.begin() as conn:
        await conn.exec_driver_sql(schema)
    logger.info("Database initialized")


async def close_db():
    """Close the database engine."""
    await engine.dispose()
    logger.info("Database connection closed")
