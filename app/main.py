from fastapi import FastAPI, Request, Depends, Response
from sqlalchemy import insert, select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SecretModel, create_table
from app.python_schema import SecretSchema
from app.db.datebase import get_db, redis_client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.db.datebase import async_engine
import uuid
import os

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=1)
async def cleanup_expired():
    async with async_engine.begin() as conn:
        stmt = update(SecretModel).where(
            and_(
                SecretModel.deleted == False,
                func.now() > (SecretModel.create_at + func.make_interval(0, 0, 0, 0, 0, 0, SecretModel.ttl_seconds))
            )
        ).values(deleted=True)
        await conn.execute(stmt)
        await conn.commit()

load_dotenv()
FERNET_KEY = os.getenv("TOKEN_DECODE_ENCODE")
fernet = Fernet(FERNET_KEY.encode())

no_cashe_heders = {
    "Cache-Control": "no-store, no-cache, must_revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_table() 
    scheduler.start()
    yield scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/secret", tags=["add_secret"])
async def create_secret(secret: SecretSchema, reqest: Request, db: AsyncSession = Depends(get_db)):
    secret_id = str(uuid.uuid4())
    encSecret = fernet.encrypt(secret.secret.encode())

    stmt = insert(SecretModel).values(
        secret_id=secret_id,
        passphrase=secret.passphrase,
        ip_addr=reqest.client.host,
        ttl_seconds=secret.ttl_seconds
    )
    await db.execute(stmt)

    await db.commit()

    await redis_client.set(secret_id, encSecret, ex=secret.ttl_seconds)

    return Response(
        content=f'{{"secret_key": "{secret_id}"}}',
        media_type="application/json",
        headers=no_cashe_heders
    )

@app.get("/secret/{secret_key}", tags=["get_secret"])
async def get_secret(secret_key: str, reqest: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(
        SecretModel.id,
        SecretModel.secret_id,
        SecretModel.get_secret_at
    ).where(
        and_(
            SecretModel.secret_id == secret_key,
            SecretModel.get_secret_at.is_(None)
        )
    )

    res_post = await db.execute(stmt)
    row = res_post.fetchone()

    result = None

    if row:
        stmt2 = update(SecretModel).where(and_(
            SecretModel.secret_id == secret_key,
            SecretModel.get_secret_at.is_(None)
        )).values(
            get_secret_at=func.now()
        )
        await db.execute(stmt2)
        await db.commit()

        result = await redis_client.get(secret_key)

        if result:
            decSecret = fernet.decrypt(result).decode()
            return Response(
                content=f'{{"secret": "{decSecret}"}}',
                media_type="application/json",
                headers=no_cashe_heders
            )

    if not result:
        return Response(
            content=f'{{"secret": "Not Found"}}',
            media_type="application/json",
            headers=no_cashe_heders
        )
    
@app.put("/secret/{secret_key}", tags=["delete_secret"])
async def delete_secret(passphrase: str, secret_key: str, request: Request, db: AsyncSession = Depends(get_db)):

    stmt = select(
        SecretModel.id,
        SecretModel.secret_id,
        SecretModel.get_secret_at
    ).where(
        and_(
            SecretModel.secret_id == secret_key,
            SecretModel.deleted == False,
            SecretModel.passphrase == passphrase
        )
    )

    res_post = await db.execute(stmt)
    row = res_post.fetchone()

    result = None

    if row:

        stmt2 = update(SecretModel).where(
            and_(
                SecretModel.secret_id == secret_key,
                SecretModel.deleted == False
            )
        ).values(
            deleted=True 
        )

        await db.execute(stmt2)
        await db.commit()

        result = await redis_client.delete(secret_key)

        if result:
            return Response(
                content='{"secret": "secret_deleted"}',
                media_type="application/json",
                headers=no_cashe_heders
            )

    return Response(
        content='{"secret": "Not Found"}',
        media_type="application/json",
        headers=no_cashe_heders
    )
