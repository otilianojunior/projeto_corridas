from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from core.database import Base

class CarroModel(Base):
    __tablename__ = 'tb_carro'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    categoria = Column(String(255), nullable=True)
    marca = Column(String(255), nullable=True)
    modelo = Column(String(255), nullable=True)
    motor = Column(String(255), nullable=True)
    versao = Column(String(255), nullable=True)
    transmissao = Column(String(255), nullable=True)
    ar_condicionado = Column(String(255), nullable=True)
    direcao = Column(String(255), nullable=True)
    combustivel = Column(String(255), nullable=True)
    km_etanol_cidade = Column(Float, nullable=True)
    km_etanol_estrada = Column(Float, nullable=True)
    km_gasolina_cidade = Column(Float, nullable=True)
    km_gasolina_estrada = Column(Float, nullable=True)
    ano = Column(Integer, nullable=True)

    # Relacionamento com MotoristaModel (carro tem motoristas)
    motoristas = relationship("MotoristaModel", back_populates="carro")