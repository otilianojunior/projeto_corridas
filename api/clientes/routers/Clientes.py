from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from clientes.models.ClienteModel import ClienteModel
from shared.dependencies import get_db
import re

router = APIRouter(prefix="/clientes", tags=["Clientes"])

class ClienteCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str


@router.get("/listar/", summary="Listar Clientes")
async def listar_clientes(db: Session = Depends(get_db)):
    """Lista todos os clientes cadastrados na API"""
    query = select(ClienteModel)
    result = db.execute(query)
    clientes = result.scalars().all()

    if not clientes:
        return {"mensagem": "Nenhum cliente cadastrado."}

    # Retorna os clientes em formato JSON serializável
    return [{"id": c.id, "nome": c.nome, "cpf": c.cpf, "telefone": c.telefone, "email": c.email} for c in clientes]


def validar_cpf(cpf: str):
    """Remove formatação e valida CPF"""
    cpf_limpo = re.sub(r"\D", "", cpf)  # Remove tudo que não é número
    if len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido. Deve conter 11 dígitos numéricos.")
    return cpf_limpo

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Cliente")
async def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    """Cria um novo cliente na API"""
    cliente.cpf = validar_cpf(cliente.cpf)  # Formata CPF antes de salvar

    # Verificar se já existe um cliente com os mesmos dados
    query = select(ClienteModel).where(
        (ClienteModel.email == cliente.email) | (ClienteModel.cpf == cliente.cpf)
    )
    result = db.execute(query)
    cliente_existente = result.scalars().first()

    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado.")

    novo_cliente = ClienteModel(
        nome=cliente.nome,
        email=cliente.email,
        telefone=cliente.telefone,
        cpf=cliente.cpf
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    return {"status": "OK", "cliente": novo_cliente}