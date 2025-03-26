from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from shared.database import Base

class CarroModel(Base):
    __tablename__ = 'tb_carro'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    categoria = Column(String(255), nullable=False)
    marca = Column(String(255), nullable=False)
    modelo = Column(String(255), nullable=False)
    motor = Column(String(255), nullable=False)
    versao = Column(String(255), nullable=False)
    transmissao = Column(String(255), nullable=False)
    ar_cond = Column(String(3), nullable=False)
    direcao = Column(String(10), nullable=False)
    combustivel = Column(String(20), nullable=True)
    km_etanol_cidade = Column(String(20), nullable=True)
    km_etanol_estrada = Column(String(20), nullable=True)
    km_gasolina_cidade = Column(String(20), nullable=True)
    km_gasolina_estrada = Column(String(20), nullable=True)
    ano = Column(String(20), nullable=True)

    # Relacionamento com MotoristaModel (carro tem motoristas)
    motoristas = relationship("MotoristaModel", back_populates="carro")
