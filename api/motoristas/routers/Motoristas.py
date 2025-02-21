import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from motoristas.models.MotoristaModel import MotoristaModel
from shared.dependencies import get_db

router = APIRouter(prefix="/motoristas", tags=["Motoristas"])

# 📌 Modelo de entrada para criação de motorista
class MotoristaCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str


@router.get("/listar/", summary="Listar Motoristas")
async def listar_motoristas(db: AsyncSession = Depends(get_db)):
    """Lista todos os motoristas cadastrados na API"""
    query = select(MotoristaModel)
    result = await db.execute(query)  # 🔄 Agora é assíncrono
    motoristas = result.scalars().all()

    if not motoristas:
        return {"mensagem": "Nenhum motorista cadastrado."}

    return [{"id": m.id, "nome": m.nome, "cpf": m.cpf, "telefone": m.telefone, "email": m.email} for m in motoristas]


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Motorista")
async def criar_motorista(motorista: MotoristaCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo motorista na API"""
    motorista.cpf = re.sub(r"\D", "", motorista.cpf)  # Remove formatação do CPF

    novo_motorista = MotoristaModel(
        nome=motorista.nome,
        email=motorista.email,
        telefone=motorista.telefone,
        cpf=motorista.cpf
    )

    try:
        db.add(novo_motorista)
        await db.commit()  # 🔄 Agora é assíncrono
        await db.refresh(novo_motorista)  # 🔄 Agora é assíncrono

        return {"status": "OK", "motorista": {
            "id": novo_motorista.id,
            "nome": novo_motorista.nome,
            "email": novo_motorista.email,
            "telefone": novo_motorista.telefone,
            "cpf": novo_motorista.cpf
        }}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erro ao criar motorista. Verifique os dados fornecidos."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao criar motorista: {str(e)}"
        )
