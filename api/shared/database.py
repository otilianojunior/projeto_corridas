import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# 🔄 Configuração do banco de dados a partir do .env
user = os.getenv("SQLALCHEMY_USER")
password = os.getenv("SQLALCHEMY_PASSWORD")
host = os.getenv("SQLALCHEMY_HOST")
database = os.getenv("SQLALCHEMY_DATABASE")

# 🔥 Alterando para conexão assíncrona
SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{user}:{password}@{host}/{database}"

# 🚀 Criando o engine assíncrono
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 🔄 Criando a sessão assíncrona
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 📌 Base declarativa para os modelos
Base = declarative_base()
