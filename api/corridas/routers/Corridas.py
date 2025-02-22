from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from corridas.models.CorridaModel import CorridaModel
from corridas.services.tracar_rota import calcular_rota_mais_curta
from corridas.services.valor_corrida import calcular_valor_base, calcular_preco_corrida, calcular_preco_km
from motoristas.models.MotoristaModel import MotoristaModel
from shared.dependencies import get_db

router = APIRouter(prefix="/corridas", tags=["Corridas"])

# Modelo para receber as taxas e valores finais no request
class TaxasAtualizadas(BaseModel):
    taxa_noturna: float = 0.0
    taxa_manutencao: float = 0.0
    taxa_pico: float = 0.0
    taxa_excesso_corridas: float = 0.0
    taxa_limpeza: float = 0.0
    taxa_cancelamento: float = 0.0
    preco_km: float  # Preço por quilômetro definido no sistema
    valor_motorista: float  # Valor destinado ao motorista
    preco_total: float  # Preço total já calculado externamente

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


# 📌 Endpoints

@router.get("/disponiveis", summary="Listar corridas disponíveis")
async def listar_corridas_disponiveis(db: AsyncSession = Depends(get_db)):
    """Lista todas as corridas disponíveis no status 'solicitado'"""
    query = select(CorridaModel).where(CorridaModel.status == "solicitado")
    result = await db.execute(query)  # 🔄 Agora é assíncrono
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
                "nome_cliente": corrida.cliente.nome,
                "distancia_km": corrida.distancia_km
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

        # ✅ Verificar se já existe uma corrida ativa para o cliente
        query = select(CorridaModel).where(CorridaModel.id_cliente == id_cliente)
        result = await db.execute(query)  # 🔄 Agora é assíncrono
        corrida_existente = result.scalars().first()

        if corrida_existente and corrida_existente.status in ["solicitado", "aceita"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma corrida solicitada ou aceita para este cliente."
            )

        # ✅ Calcular a rota mais curta com base nas coordenadas fornecidas
        try:
            # Agora a função é síncrona
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

        # ✅ Calcular o preço parcial da corrida
        preco_parcial = await calcular_valor_base(distancia_km)

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
            preco_parcial=preco_parcial,
            status='solicitado',
            id_cliente=id_cliente
        )

        db.add(nova_corrida)
        await db.commit()  # 🔄 Agora é assíncrono
        await db.refresh(nova_corrida)  # 🔄 Agora é assíncrono

        return nova_corrida
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar a solicitação: {str(e)}"
        )


@router.put("/finalizar_corrida/{corrida_id}", status_code=status.HTTP_200_OK, summary="Aplicar taxas e finalizar corrida")
async def finalizar_corrida(corrida_id: int, taxas: TaxasAtualizadas, db: AsyncSession = Depends(get_db)):
    """Aplica taxas, atualiza o valor total e finaliza a corrida."""

    # Buscar corrida no banco de dados
    query = select(CorridaModel).where(CorridaModel.id == corrida_id, CorridaModel.status == "solicitado")
    result = await db.execute(query)
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada ou não está no estado 'solicitado'.")

    # Atualizar os valores na corrida com os dados recebidos
    corrida.taxa_noturna = taxas.taxa_noturna
    corrida.taxa_manutencao = taxas.taxa_manutencao
    corrida.taxa_pico = taxas.taxa_pico
    corrida.taxa_excesso_corridas = taxas.taxa_excesso_corridas
    corrida.taxa_limpeza = taxas.taxa_limpeza
    corrida.taxa_cancelamento = taxas.taxa_cancelamento
    corrida.preco_km = taxas.preco_km
    corrida.valor_motorista = taxas.valor_motorista
    corrida.preco_total = taxas.preco_total

    # Atualizar status da corrida para "finalizada"
    corrida.status = "finalizada"

    await db.commit()
    await db.refresh(corrida)

    return {
        "mensagem": "Corrida finalizada com sucesso.",
        "corrida_id": corrida.id,
        "status": corrida.status,
        "preco_total": corrida.preco_total,
        "valor_motorista": corrida.valor_motorista,
        "taxas_aplicadas": taxas.dict()
    }