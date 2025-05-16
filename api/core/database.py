import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do banco de dados a partir das variáveis de ambiente
user = os.getenv("SQLALCHEMY_USER")
password = os.getenv("SQLALCHEMY_PASSWORD")
host = os.getenv("SQLALCHEMY_HOST")
database = os.getenv("SQLALCHEMY_DATABASE")

# Define a URL de conexão assíncrona com o banco de dados MySQL
SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{user}:{password}@{host}/{database}"

# Cria o engine assíncrono para interagir com o banco de dados
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Configura o gerenciador de sessões assíncronas
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Define a base declarativa para os modelos ORM
Base = declarative_base()
