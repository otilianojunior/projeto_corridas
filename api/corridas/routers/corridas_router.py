import random
from datetime import datetime

from core.dependencies import get_db
from corridas.models.corrida_model import CorridaModel
from corridas.services.rota_service import calcular_rota_mais_curta
from fastapi import APIRouter, Depends, HTTPException, status
from motoristas.models.motorista_model import MotoristaModel
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/corridas", tags=["Corridas"])


# Modelo para receber as taxas e valores finais no request (já existente)
class TaxasAtualizadas(BaseModel):
    taxa_noturna: float = 0.0
    taxa_manutencao: float = 0.0
    taxa_pico: float = 0.0
    taxa_excesso_corridas: float = 0.0
    taxa_limpeza: float = 0.0
    taxa_cancelamento: float = 0.0
    preco_km: float
    valor_motorista: float
    preco_total: float
    nivel_taxa: int


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
                "motorista": {
                    "id_motorista": 0
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
    id_motorista: int
    distancia_km: float
    cordenadas_rota: str

    class Config:
        from_attributes = True


# Modelo para atualização de uma corrida
class CorridaUpdate(BaseModel):
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
    id_motorista: int
    distancia_km: float
    cordenadas_rota: str
    status: str


@router.get("/listar", summary="Listar todas as corridas")
async def listar_todas_corridas(db: AsyncSession = Depends(get_db)):
    """Lista todas as corridas, independente do status."""
    query = select(CorridaModel).options(joinedload(CorridaModel.cliente), joinedload(CorridaModel.motorista))
    result = await db.execute(query)
    corridas = result.scalars().all()

    if not corridas:
        raise HTTPException(status_code=404, detail="Nenhuma corrida cadastrada.")

    return {
        "total": len(corridas),
        "corridas": [
            {
                "id": corrida.id,
                "origem_rua": corrida.origem_rua,
                "origem_bairro": corrida.origem_bairro,
                "origem_longitude": corrida.origem_longitude,
                "origem_latitude": corrida.origem_latitude,
                "destino_rua": corrida.destino_rua,
                "destino_bairro": corrida.destino_bairro,
                "destino_longitude": corrida.destino_longitude,
                "destino_latitude": corrida.destino_latitude,
                "horario_pedido": corrida.horario_pedido,
                "id_cliente": corrida.id_cliente,
                "id_motorista": corrida.id_motorista,
                "distancia_km": corrida.distancia_km,
                "cordenadas_rota": corrida.cordenadas_rota,
                "status": corrida.status,
            }
            for corrida in corridas
        ]
    }


# Rotas existentes

@router.get("/listar_disponiveis", summary="Listar corridas disponíveis")
async def listar_corridas_disponiveis(db: AsyncSession = Depends(get_db)):
    """Lista todas as corridas disponíveis no status 'solicitado'"""
    query = (
        select(CorridaModel)
        .where(CorridaModel.status == "solicitado")
        .options(joinedload(CorridaModel.cliente), joinedload(CorridaModel.motorista))
    )
    result = await db.execute(query)
    corridas_disponiveis = result.scalars().all()

    if not corridas_disponiveis:
        return {"mensagem": "Sem corridas disponíveis no momento."}

    return {
        "corridas_disponiveis": [
            {
                "id": corrida.id,
                "origem_rua": corrida.origem_rua,
                "origem_bairro": corrida.origem_bairro,
                "destino_rua": corrida.destino_rua,
                "destino_bairro": corrida.destino_bairro,
                "nome_cliente": corrida.cliente.nome if corrida.cliente else "Cliente Desconhecido",
                "id_motorista": corrida.motorista.id if corrida.motorista else None,
                "distancia_km": corrida.distancia_km,
                "horario_pedido": corrida.horario_pedido,
            }
            for corrida in corridas_disponiveis
        ]
    }


@router.post("/solicitar", response_model=CorridaResponse, status_code=status.HTTP_201_CREATED,
             summary="Solicitar nova corrida")
async def solicitar_corrida(corrida_data: CorridaCreate, db: AsyncSession = Depends(get_db)):
    """Solicita uma nova corrida na API"""
    try:
        origem = corrida_data.origem
        destino = corrida_data.destino
        id_cliente = corrida_data.cliente.id_cliente

        # Verificar se já existe uma corrida ativa para o cliente
        query = select(CorridaModel).where(CorridaModel.id_cliente == id_cliente)
        result = await db.execute(query)
        corrida_existente = result.scalars().first()

        if corrida_existente and corrida_existente.status in ["solicitado", "aceita"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma corrida solicitada ou aceita para este cliente."
            )

        # Calcular a rota mais curta
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

        # Obter um motorista aleatório disponível
        motoristas_query = select(CorridaModel).where(CorridaModel.status == "solicitado")  # ajuste se necessário
        motoristas_query = select(MotoristaModel).where(MotoristaModel.status == "disponivel")
        motoristas_result = await db.execute(motoristas_query)
        motoristas = motoristas_result.scalars().all()

        if motoristas:
            motorista = random.choice(motoristas)
            id_motorista = motorista.id
            motorista.status = "ocupado"
            await db.commit()
        else:
            id_motorista = None

        nova_corrida = CorridaModel(
            origem_rua=origem.nome_rua,
            origem_bairro=origem.bairro,
            origem_longitude=origem.longitude,
            origem_latitude=origem.latitude,
            destino_rua=destino.nome_rua,
            destino_bairro=destino.bairro,
            destino_longitude=destino.longitude,
            destino_latitude=destino.latitude,
            horario_pedido=corrida_data.horario_pedido,
            cordenadas_rota="|".join([f"{lat},{lon}" for lat, lon in coordenadas_rota]),
            distancia_km=distancia_km,
            status='solicitado',
            id_cliente=id_cliente,
            id_motorista=id_motorista
        )

        db.add(nova_corrida)
        await db.commit()
        await db.refresh(nova_corrida)

        return nova_corrida
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )


@router.put("/finalizar_corrida/{corrida_id}", status_code=status.HTTP_200_OK,
            summary="Aplicar taxas e finalizar corrida")
async def finalizar_corrida(corrida_id: int, taxas: TaxasAtualizadas, db: AsyncSession = Depends(get_db)):
    """Aplica taxas, atualiza o valor total e finaliza a corrida."""
    query = select(CorridaModel).where(CorridaModel.id == corrida_id, CorridaModel.status == "solicitado")
    result = await db.execute(query)
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada ou não está no estado 'solicitado'.")

    corrida.taxa_noturna = taxas.taxa_noturna
    corrida.taxa_manutencao = taxas.taxa_manutencao
    corrida.taxa_pico = taxas.taxa_pico
    corrida.taxa_excesso_corridas = taxas.taxa_excesso_corridas
    corrida.taxa_limpeza = taxas.taxa_limpeza
    corrida.taxa_cancelamento = taxas.taxa_cancelamento
    corrida.preco_km = taxas.preco_km
    corrida.valor_motorista = taxas.valor_motorista
    if taxas.nivel_taxa is not None:
        corrida.nivel_taxa = taxas.nivel_taxa
    corrida.preco_total = taxas.preco_total
    corrida.status = "finalizada"

    if corrida.id_motorista:
        motorista_query = select(MotoristaModel).where(MotoristaModel.id == corrida.id_motorista)
        motorista_result = await db.execute(motorista_query)
        motorista = motorista_result.scalars().first()
        if motorista:
            motorista.status = "disponivel"
            await db.commit()
            await db.refresh(motorista)

    await db.commit()
    await db.refresh(corrida)

    return {
        "mensagem": "Corrida finalizada com sucesso.",
        "corrida_id": corrida.id,
        "status": corrida.status,
        "preco_total": corrida.preco_total,
        "valor_motorista": corrida.valor_motorista,
        "nivel_taxa": corrida.nivel_taxa
    }


@router.put("/editar/{corrida_id}", summary="Editar Corrida")
async def editar_corrida(corrida_id: int, corrida_update: CorridaUpdate, db: AsyncSession = Depends(get_db)):
    """Edita os dados de uma corrida existente."""
    query = select(CorridaModel).where(CorridaModel.id == corrida_id)
    result = await db.execute(query)
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")

    try:
        corrida.origem_rua = corrida_update.origem_rua
        corrida.origem_bairro = corrida_update.origem_bairro
        corrida.origem_longitude = corrida_update.origem_longitude
        corrida.origem_latitude = corrida_update.origem_latitude
        corrida.destino_rua = corrida_update.destino_rua
        corrida.destino_bairro = corrida_update.destino_bairro
        corrida.destino_longitude = corrida_update.destino_longitude
        corrida.destino_latitude = corrida_update.destino_latitude
        corrida.horario_pedido = corrida_update.horario_pedido
        corrida.id_cliente = corrida_update.id_cliente
        corrida.id_motorista = corrida_update.id_motorista
        corrida.distancia_km = corrida_update.distancia_km
        corrida.cordenadas_rota = corrida_update.cordenadas_rota
        corrida.status = corrida_update.status

        await db.commit()
        await db.refresh(corrida)

        return {"status": "OK", "corrida": {
            "id": corrida.id,
            "origem_rua": corrida.origem_rua,
            "origem_bairro": corrida.origem_bairro,
            "origem_longitude": corrida.origem_longitude,
            "origem_latitude": corrida.origem_latitude,
            "destino_rua": corrida.destino_rua,
            "destino_bairro": corrida.destino_bairro,
            "destino_longitude": corrida.destino_longitude,
            "destino_latitude": corrida.destino_latitude,
            "horario_pedido": corrida.horario_pedido,
            "id_cliente": corrida.id_cliente,
            "id_motorista": corrida.id_motorista,
            "distancia_km": corrida.distancia_km,
            "cordenadas_rota": corrida.cordenadas_rota,
            "status": corrida.status,
        }}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar corrida: {str(e)}")


@router.delete("/excluir/{corrida_id}", summary="Excluir Corrida", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_corrida(corrida_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui uma corrida da API."""
    query = select(CorridaModel).where(CorridaModel.id == corrida_id)
    result = await db.execute(query)
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada.")

    try:
        await db.delete(corrida)
        await db.commit()
        return {"status": "OK", "mensagem": "Corrida excluída com sucesso."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir corrida: {str(e)}")
