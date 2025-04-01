import re

from carros.models.carro_model import CarroModel
from core.dependencies import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from motoristas.models.motorista_model import MotoristaModel
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/motoristas", tags=["Motoristas"])


class MotoristaCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str
    status: str
    id_carro: int


class MotoristaUpdate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str
    status: str
    id_carro: int


@router.get("/listar", summary="Listar motoristas")
async def listar_motoristas(db: AsyncSession = Depends(get_db)):
    """Lista todos os motoristas cadastrados na API, incluindo dados do carro."""
    query = select(MotoristaModel).options(selectinload(MotoristaModel.carro))
    result = await db.execute(query)
    motoristas = result.scalars().all()

    if not motoristas:
        raise HTTPException(status_code=404, detail="Nenhum motorista cadastrado.")

    return [
        {
            "id": m.id,
            "nome": m.nome,
            "cpf": m.cpf,
            "telefone": m.telefone,
            "email": m.email,
            "status": m.status,
            "id_carro": m.id_carro,
            "carro": {
                "id": m.carro.id if m.carro else None,
                "modelo": m.carro.modelo if m.carro else None,
                "combustivel": m.carro.combustivel if m.carro else None,
                "km_etanol_cidade": m.carro.km_etanol_cidade if m.carro else None,
                "km_gasolina_cidade": m.carro.km_gasolina_cidade if m.carro else None,
                "ano": m.carro.ano if m.carro else None,
            }
        }
        for m in motoristas
    ]


@router.get("/listar_disponiveis", summary="Listar motoristas disponíveis")
async def listar_motoristas_disponiveis(db: AsyncSession = Depends(get_db)):
    """Lista todos os motoristas disponíveis cadastrados na API, incluindo dados do carro."""
    query = (
        select(MotoristaModel)
        .where(MotoristaModel.status == "disponivel")
        .options(selectinload(MotoristaModel.carro))
    )
    result = await db.execute(query)
    motoristas = result.scalars().all()

    if not motoristas:
        raise HTTPException(status_code=404, detail="Nenhum motorista disponível.")

    return [
        {
            "id": m.id,
            "nome": m.nome,
            "cpf": m.cpf,
            "telefone": m.telefone,
            "email": m.email,
            "status": m.status,
            "id_carro": m.id_carro,
            "carro": {
                "id": m.carro.id if m.carro else None,
                "modelo": m.carro.modelo if m.carro else None,
                "combustivel": m.carro.combustivel if m.carro else None,
                "km_etanol_cidade": m.carro.km_etanol_cidade if m.carro else None,
                "km_gasolina_cidade": m.carro.km_gasolina_cidade if m.carro else None,
                "ano": m.carro.ano if m.carro else None,
            }
        }
        for m in motoristas
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar motorista")
async def criar_motorista(motorista: MotoristaCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo motorista na API."""
    motorista.cpf = re.sub(r"\D", "", motorista.cpf)

    query = select(MotoristaModel).where(
        (MotoristaModel.cpf == motorista.cpf) |
        (MotoristaModel.telefone == motorista.telefone) |
        (MotoristaModel.email == motorista.email)
    )
    result = await db.execute(query)
    existing_motorista = result.scalars().first()

    if existing_motorista:
        raise HTTPException(
            status_code=400,
            detail="Motorista com CPF, telefone ou email já cadastrado."
        )

    carro_query = select(CarroModel).where(CarroModel.id == motorista.id_carro)
    carro_result = await db.execute(carro_query)
    carro = carro_result.scalars().first()

    if not carro:
        raise HTTPException(status_code=400, detail="Carro não encontrado com o ID informado.")

    novo_motorista = MotoristaModel(
        nome=motorista.nome,
        email=motorista.email,
        telefone=motorista.telefone,
        cpf=motorista.cpf,
        status=motorista.status,
        id_carro=motorista.id_carro
    )

    try:
        db.add(novo_motorista)
        await db.commit()
        await db.refresh(novo_motorista)

        return {
            "status": "OK",
            "motorista": {
                "id": novo_motorista.id,
                "nome": novo_motorista.nome,
                "email": novo_motorista.email,
                "telefone": novo_motorista.telefone,
                "cpf": novo_motorista.cpf,
                "status": novo_motorista.status,
                "id_carro": novo_motorista.id_carro,
                "carro": {
                    "id": carro.id,
                    "marca": carro.marca,
                    "modelo": carro.modelo
                }
            }
        }
    except IntegrityError as ie:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro de integridade ao criar motorista: {str(ie.orig) if hasattr(ie, 'orig') else str(ie)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao criar motorista: {str(e)}"
        )


@router.put("/{motorista_id}", summary="Editar motorista")
async def editar_motorista(motorista_id: int, motorista: MotoristaUpdate, db: AsyncSession = Depends(get_db)):
    """Edita os dados de um motorista existente."""
    motorista.cpf = re.sub(r"\D", "", motorista.cpf)

    query = select(MotoristaModel).where(MotoristaModel.id == motorista_id)
    result = await db.execute(query)
    motorista_existente = result.scalars().first()

    if not motorista_existente:
        raise HTTPException(status_code=404, detail="Motorista não encontrado.")

    carro_query = select(CarroModel).where(CarroModel.id == motorista.id_carro)
    carro_result = await db.execute(carro_query)
    carro = carro_result.scalars().first()

    if not carro:
        raise HTTPException(status_code=400, detail="Carro não encontrado com o ID informado.")

    try:
        motorista_existente.nome = motorista.nome
        motorista_existente.email = motorista.email
        motorista_existente.telefone = motorista.telefone
        motorista_existente.cpf = motorista.cpf
        motorista_existente.status = motorista.status
        motorista_existente.id_carro = motorista.id_carro

        await db.commit()
        await db.refresh(motorista_existente)

        return {
            "status": "OK",
            "motorista": {
                "id": motorista_existente.id,
                "nome": motorista_existente.nome,
                "email": motorista_existente.email,
                "telefone": motorista_existente.telefone,
                "cpf": motorista_existente.cpf,
                "status": motorista_existente.status,
                "id_carro": motorista_existente.id_carro
            }
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar motorista: {str(e)}")


@router.delete("/{motorista_id}", summary="Excluir motorista")
async def excluir_motorista(motorista_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui um motorista da API."""
    query = select(MotoristaModel).where(MotoristaModel.id == motorista_id)
    result = await db.execute(query)
    motorista = result.scalars().first()

    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado.")

    try:
        await db.delete(motorista)
        await db.commit()
        return {"status": "OK", "mensagem": "Motorista excluído com sucesso."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir motorista: {str(e)}")
