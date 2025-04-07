from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.db.config_postgres import settings_postgres
from app.db.config_redis import settings_redis
import redis.asyncio as redis

redis_client = redis.from_url(
    url=settings_redis.DATABASE_get_url_redis,
    decode_responses=True
)

async_engine = create_async_engine(
    url=settings_postgres.DATABASE_get_url_postgres,
    echo=True,
    pool_size=5,
)

class Base(DeclarativeBase, AsyncAttrs):
    pass

async_session = async_sessionmaker(async_engine)

async def get_db():
    async with async_session() as session:
        yield session

