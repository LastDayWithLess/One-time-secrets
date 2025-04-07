from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from app.db.datebase import Base, async_engine
from datetime import datetime
from typing import Union
from uuid import UUID

class SecretModel(Base):
    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(primary_key=True)
    secret_id: Mapped[UUID] = mapped_column(unique=True)
    create_at: Mapped[datetime] = mapped_column(server_default=func.now())
    passphrase: Mapped[Union[str, None]]
    ip_addr: Mapped[str]
    ttl_seconds: Mapped[Union[int, None]] = mapped_column(server_default="3600")
    get_secret_at: Mapped[Union[datetime, None]]
    deleted: Mapped[bool] = mapped_column(server_default="FALSE")

async def create_table():
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))
