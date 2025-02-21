from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from motoristas.models.MotoristaModel import MotoristaModel
from shared.dependencies import get_db
import re

router = APIRouter(prefix="/motoristas", tags=["Motoristas"])


class MotoristaCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str

@router.get("/listar/", summary="Listar Motoristas")
async def listar_motoristas(db: Session = Depends(get_db)):
    query = select(MotoristaModel)
    result = db.execute(query)
    motoristas = result.scalars().all()

    if not motoristas:
        return {"mensagem": "Nenhum motorista cadastrado."}

    return [{"id": m.id, "nome": m.nome, "cpf": m.cpf, "telefone": m.telefone, "email": m.email} for m in motoristas]

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Motorista")
async def criar_motorista(motorista: MotoristaCreate, db: Session = Depends(get_db)):
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
        db.commit()
        db.refresh(novo_motorista)

        return {"status": "OK", "motorista": novo_motorista}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erro ao criar motorista. Verifique os dados fornecidos."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao criar motorista: {str(e)}"
        )