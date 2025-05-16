from core.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class MotoristaModel(Base):
    __tablename__ = "tb_motorista"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    telefone = Column(String(20), unique=True, nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    status = Column(String(255), nullable=False)

    # Relacionamento com CorridaModel: um motorista pode ter muitas corridas
    corridas = relationship("CorridaModel", back_populates="motorista")

    # Relacionamento com CarroModel: um motorista está vinculado a um carro
    id_carro = Column(Integer, ForeignKey("tb_carro.id"), nullable=False)
    carro = relationship("CarroModel", back_populates="motoristas")
