from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.database import Base


class ClienteModel(Base):
    __tablename__ = 'tb_cliente'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    telefone = Column(String(20), unique=True, nullable=True)
    cpf = Column(String(11), unique=True, nullable=False)

    # Relacionamento com CorridaModel
    corridas = relationship("CorridaModel", back_populates="cliente")