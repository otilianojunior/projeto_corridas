import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from motoristas.models.MotoristaModel import MotoristaModel
from carros.models.CarroModel import CarroModel
from shared.dependencies import get_db

router = APIRouter(prefix="/motoristas", tags=["Motoristas"])

# 📌 Modelo de entrada para criação de motorista
class MotoristaCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str
    status: str
    id_carro: int

@router.get("/listar/", summary="Listar Motoristas")
async def listar_motoristas(db: AsyncSession = Depends(get_db)):
    """Lista todos os motoristas cadastrados na API"""
    query = select(MotoristaModel)
    result = await db.execute(query)
    motoristas = result.scalars().all()

    if not motoristas:
        return {"mensagem": "Nenhum motorista cadastrado."}

    return [
        {
            "id": m.id,
            "nome": m.nome,
            "cpf": m.cpf,
            "telefone": m.telefone,
            "email": m.email,
            "status": m.status,
            "id_carro": m.id_carro
        }
        for m in motoristas
    ]

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Motorista")
async def criar_motorista(motorista: MotoristaCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo motorista na API"""
    # Remove formatação do CPF
    motorista.cpf = re.sub(r"\D", "", motorista.cpf)

    # Verificar se já existe um motorista com o mesmo CPF, telefone ou email
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

    # Verificar se o carro com o id fornecido existe
    carro_query = select(CarroModel).where(CarroModel.id == motorista.id_carro)
    carro_result = await db.execute(carro_query)
    carro = carro_result.scalars().first()

    if not carro:
        raise HTTPException(status_code=400, detail="Carro não encontrado com o id informado.")

    # Criar novo motorista e definir explicitamente o id_carro
    novo_motorista = MotoristaModel(
        nome=motorista.nome,
        email=motorista.email,
        telefone=motorista.telefone,
        cpf=motorista.cpf,
        status="disponivel",
        id_carro=motorista.id_carro
    )

    try:
        db.add(novo_motorista)
        await db.commit()
        await db.refresh(novo_motorista)

        # A associação via chave estrangeira (id_carro) já foi feita;
        # se o relacionamento estiver configurado corretamente, não há necessidade de adicionar manualmente.
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
