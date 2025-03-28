from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from shared.database import Base

class CarroModel(Base):
    __tablename__ = 'tb_carro'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    categoria = Column(String(255), nullable=True)
    marca = Column(String(255), nullable=False)
    modelo = Column(String(255), nullable=False)
    motor = Column(String(255), nullable=True)
    versao = Column(String(255), nullable=True)
    transmissao = Column(String(255), nullable=True)
    ar_cond = Column(String(10), nullable=True)
    direcao = Column(String(10), nullable=True)
    combustivel = Column(String(20), nullable=False)
    km_etanol_cidade = Column(String(20), nullable=True)
    km_etanol_estrada = Column(String(20), nullable=True)
    km_gasolina_cidade = Column(String(20), nullable=True)
    km_gasolina_estrada = Column(String(20), nullable=True)
    ano = Column(String(20), nullable=True)

    # Relacionamento com MotoristaModel (carro tem motoristas)
    motoristas = relationship("MotoristaModel", back_populates="carro")
