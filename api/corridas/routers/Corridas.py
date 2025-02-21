from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from corridas.models.CorridaModel import CorridaModel
from corridas.services.tracar_rota import calcular_rota_mais_curta
from corridas.services.valor_corrida import calcular_valor_base, calcular_preco_corrida, calcular_preco_km
from motoristas.models.MotoristaModel import MotoristaModel
from shared.dependencies import get_db

router = APIRouter(prefix="/corridas", tags=["Corridas"])


# Modelos Pydantic para requisições e respostas

class Endereco(BaseModel):
    latitude: float
    longitude: float
    nome_rua: str = "Desconhecido"
    bairro: str = "Desconhecido"


class Cliente(BaseModel):
    id_cliente: int


class CorridaCreate(BaseModel):
    origem: Endereco
    destino: Endereco
    cliente: Cliente
    horario_pedido: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "origem": {
                    "latitude": -14.8744823,
                    "longitude": -40.8827484,
                    "nome_rua": "Desconhecido",
                    "bairro": "Campinhos"
                },
                "destino": {
                    "latitude": -14.8440731,
                    "longitude": -40.8737567,
                    "nome_rua": "Caminho Dez",
                    "bairro": "Zabelê"
                },
                "cliente": {
                    "id_cliente": 0
                },
                "horario_pedido": "2025-02-06T14:29:14.112Z"
            }
        }


class CorridaResponse(BaseModel):
    id: int
    origem_rua: str
    origem_bairro: str
    origem_longitude: float
    origem_latitude: float
    destino_rua: str
    destino_bairro: str
    destino_longitude: float
    destino_latitude: float
    horario_pedido: datetime
    id_cliente: int
    distancia_km: float
    cordenadas_rota: str
    preco_parcial: float

    class Config:
        from_attributes = True


# Endpoints

@router.get("/disponiveis", summary="Listar corridas disponíveis")
async def listar_corridas_disponiveis(db: Session = Depends(get_db)):
    query = select(CorridaModel).where(CorridaModel.status == "solicitado")
    result = db.execute(query)
    corridas_disponiveis = result.scalars().all()

    if not corridas_disponiveis:
        return {"mensagem": "Sem corridas disponíveis no momento."}

    lista_corridas = [
        {
            "id": corrida.id,
            "origem_rua": corrida.origem_rua,
            "origem_bairro": corrida.origem_bairro,
            "destino_rua": corrida.destino_rua,
            "destino_bairro": corrida.destino_bairro,
            "nome_cliente": corrida.cliente.nome,
            "distancia_km": corrida.distancia_km
        }
        for corrida in corridas_disponiveis
    ]

    return {"corridas_disponiveis": lista_corridas}


@router.post("/solicitar", response_model=CorridaResponse, status_code=status.HTTP_201_CREATED,
             summary="Solicitar nova corrida")
async def solicitar_corrida(corrida_data: CorridaCreate, db: Session = Depends(get_db)):
    try:
        origem = corrida_data.origem
        destino = corrida_data.destino
        cliente = corrida_data.cliente
        horario_pedido = corrida_data.horario_pedido

        id_cliente = cliente.id_cliente

        # Verificar se já existe uma corrida ativa para o cliente
        query = select(CorridaModel).where(CorridaModel.id_cliente == id_cliente)
        result = db.execute(query)
        corrida_existente = result.scalars().first()

        if corrida_existente and corrida_existente.status in ["solicitado", "aceita"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma corrida solicitada ou aceita para este cliente."
            )

        # Calcular a rota mais curta com base nas coordenadas fornecidas
        try:
            _, coordenadas_rota, distancia_km = calcular_rota_mais_curta(
                cidade="Vitória da Conquista, Brasil",
                origem_longitude=origem.longitude,
                origem_latitude=origem.latitude,
                destino_longitude=destino.longitude,
                destino_latitude=destino.latitude
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao calcular rota: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro nos parâmetros de coordenadas: {str(e)}"
            )

        # Calcular o preço parcial da corrida
        preco_parcial = calcular_valor_base(distancia_km)

        nova_corrida = CorridaModel(
            origem_rua=origem.nome_rua,
            origem_bairro=origem.bairro,
            origem_longitude=origem.longitude,
            origem_latitude=origem.latitude,
            destino_rua=destino.nome_rua,
            destino_bairro=destino.bairro,
            destino_longitude=destino.longitude,
            destino_latitude=destino.latitude,
            horario_pedido=horario_pedido,
            cordenadas_rota="|".join([f"{lat},{lon}" for lat, lon in coordenadas_rota]),
            distancia_km=distancia_km,
            preco_parcial=preco_parcial,
            status='solicitado',
            id_cliente=id_cliente
        )

        db.add(nova_corrida)
        db.commit()
        db.refresh(nova_corrida)

        return nova_corrida
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )


@router.post("/simular", status_code=status.HTTP_200_OK, summary="Simular valores da corrida")
async def simular_corrida(
        corrida_id: int,
        id_motorista: int,
        status_corrida: str,
        taxa_noturna: float,
        taxa_manutencao: float,
        taxa_pico: float,
        taxa_excesso_corridas: float,
        taxa_limpeza: float,
        taxa_cancelamento: float,
        db: Session = Depends(get_db)
):
    # Buscar a corrida pelo ID
    corrida = db.query(CorridaModel).filter(CorridaModel.id == corrida_id).first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")

    if corrida.status != "solicitado":
        raise HTTPException(status_code=400, detail="Corrida não pode ser simulada no status atual")

    # Buscar o motorista pelo ID
    motorista = db.query(MotoristaModel).filter(MotoristaModel.id == id_motorista).first()

    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")

    distancia_km = corrida.distancia_km
    preco_km = calcular_preco_km(distancia_km)

    preco_total = calcular_preco_corrida(
        valor_base=corrida.preco_parcial,
        taxa_noturna=taxa_noturna,
        taxa_pico=taxa_pico,
        taxa_excesso_corridas=taxa_excesso_corridas,
        taxa_limpeza=taxa_limpeza,
        taxa_cancelamento=taxa_cancelamento
    )

    # Atualizar os dados da corrida com a simulação
    corrida.id_motorista = id_motorista
    corrida.status = status_corrida
    corrida.taxa_noturna = taxa_noturna
    corrida.taxa_manutencao = taxa_manutencao
    corrida.taxa_pico = taxa_pico
    corrida.taxa_excesso_corridas = taxa_excesso_corridas
    corrida.taxa_limpeza = taxa_limpeza
    corrida.taxa_cancelamento = taxa_cancelamento
    corrida.preco_km = preco_km
    corrida.preco_total = preco_total

    db.commit()
    db.refresh(corrida)

    return {"status": "OK", "corrida": corrida}