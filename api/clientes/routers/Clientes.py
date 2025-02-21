import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from clientes.models.ClienteModel import ClienteModel
from shared.dependencies import get_db

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# 📌 Modelo de entrada para criação de cliente
class ClienteCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str


@router.get("/listar/", summary="Listar Clientes")
async def listar_clientes(db: AsyncSession = Depends(get_db)):
    """Lista todos os clientes cadastrados na API"""
    query = select(ClienteModel)
    result = await db.execute(query)  # 🔄 Agora é assíncrono
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
async def criar_cliente(cliente: ClienteCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo cliente na API"""
    cliente.cpf = validar_cpf(cliente.cpf)  # Formata CPF antes de salvar

    # 🔄 Verificar se já existe um cliente com os mesmos dados
    query = select(ClienteModel).where(
        (ClienteModel.email == cliente.email) | (ClienteModel.cpf == cliente.cpf)
    )
    result = await db.execute(query)  # 🔄 Agora é assíncrono
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
    await db.commit()  # 🔄 Agora é assíncrono
    await db.refresh(novo_cliente)  # 🔄 Agora é assíncrono

    return {"status": "OK", "cliente": {
        "id": novo_cliente.id,
        "nome": novo_cliente.nome,
        "email": novo_cliente.email,
        "telefone": novo_cliente.telefone,
        "cpf": novo_cliente.cpf
    }}
