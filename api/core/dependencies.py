from core.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


# Dependência para obter a sessão do banco de forma assíncrona
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
