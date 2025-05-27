from core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship


class CorridaModel(Base):
    __tablename__ = 'tb_corrida'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    origem_rua = Column(String(255), nullable=False)
    origem_bairro = Column(String(255), nullable=False)
    origem_longitude = Column(Numeric(11, 6), nullable=False)
    origem_latitude = Column(Numeric(11, 6), nullable=False)
    destino_rua = Column(String(255), nullable=False)
    destino_bairro = Column(String(255), nullable=False)
    destino_longitude = Column(Numeric(11, 6), nullable=False)
    destino_latitude = Column(Numeric(11, 6), nullable=False)
    distancia_km = Column(Numeric(10, 2), nullable=False)
    coordenadas_rota = Column(Text, nullable=False)
    horario_pedido = Column(DateTime, nullable=False)
    taxa_noturna = Column(String(255), nullable=True)
    taxa_manutencao = Column(String(255), nullable=True)
    taxa_pico = Column(String(255), nullable=True)
    taxa_excesso_corridas = Column(String(255), nullable=True)
    taxa_limpeza = Column(String(255), nullable=True)
    taxa_cancelamento = Column(String(255), nullable=True)
    valor_motorista = Column(Numeric(10, 2), nullable=True)
    preco_km = Column(Numeric(10, 2), nullable=True)
    nivel_taxa = Column(Integer, nullable=True)
    preco_total = Column(Numeric(10, 2), nullable=True)
    status = Column(String(255), nullable=False)

    id_cliente = Column(Integer, ForeignKey("tb_cliente.id"), nullable=True)
    cliente = relationship("ClienteModel", back_populates="corridas")

    id_motorista = Column(Integer, ForeignKey("tb_motorista.id"), nullable=True)
    motorista = relationship("MotoristaModel", back_populates="corridas")
