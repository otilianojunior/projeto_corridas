import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

user = os.getenv("SQLALCHEMY_USER")
password = os.getenv("SQLALCHEMY_PASSWORD")
host = os.getenv("SQLALCHEMY_HOST")
database = os.getenv("SQLALCHEMY_DATABASE")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqldb://{user}:{password}@{host}/{database}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
