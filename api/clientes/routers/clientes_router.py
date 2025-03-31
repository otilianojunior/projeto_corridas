import re

from clientes.models.cliente_model import ClienteModel
from core.dependencies import get_db
from corridas.models.corrida_model import CorridaModel
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/clientes", tags=["Clientes"])


# Modelo de entrada para criação de cliente
class ClienteCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str


# Modelo de entrada para edição de cliente
class ClienteUpdate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str


def validar_cpf(cpf: str):
    """Remove formatação e valida CPF"""
    cpf_limpo = re.sub(r"\D", "", cpf)
    if len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido. Deve conter 11 dígitos numéricos.")
    return cpf_limpo


@router.get("/listar/", summary="Listar Clientes")
async def listar_clientes(db: AsyncSession = Depends(get_db)):
    """Lista todos os clientes cadastrados na API"""
    query = select(ClienteModel)
    result = await db.execute(query)
    clientes = result.scalars().all()

    if not clientes:
        return {"mensagem": "Nenhum cliente cadastrado."}

    return [
        {"id": c.id, "nome": c.nome, "cpf": c.cpf, "telefone": c.telefone, "email": c.email}
        for c in clientes
    ]


@router.get("/listar_sem_corrida/", summary="Listar Clientes sem corridas ativas")
async def listar_clientes_sem_corrida(db: AsyncSession = Depends(get_db)):
    """Lista clientes que não possuem corridas ativas"""

    query = select(ClienteModel).where(
        ~ClienteModel.id.in_(
            select(CorridaModel.id_cliente).where(CorridaModel.status.in_(["solicitado", "aceita"]))
        )
    )
    result = await db.execute(query)
    clientes_disponiveis = result.scalars().all()

    if not clientes_disponiveis:
        return {"mensagem": "Nenhum cliente disponível para solicitar corrida."}

    return [
        {"id": c.id, "nome": c.nome, "cpf": c.cpf, "telefone": c.telefone, "email": c.email}
        for c in clientes_disponiveis
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Cliente")
async def criar_cliente(cliente: ClienteCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo cliente na API"""
    cliente.cpf = validar_cpf(cliente.cpf)

    query = select(ClienteModel).where(
        (ClienteModel.email == cliente.email) | (ClienteModel.cpf == cliente.cpf)
    )
    result = await db.execute(query)
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
    await db.commit()
    await db.refresh(novo_cliente)

    return {"status": "OK", "cliente": {
        "id": novo_cliente.id,
        "nome": novo_cliente.nome,
        "email": novo_cliente.email,
        "telefone": novo_cliente.telefone,
        "cpf": novo_cliente.cpf
    }}


@router.put("/{cliente_id}", summary="Editar Cliente")
async def editar_cliente(cliente_id: int, cliente: ClienteUpdate, db: AsyncSession = Depends(get_db)):
    """Edita os dados de um cliente existente."""
    # Remove formatação do CPF
    cliente.cpf = validar_cpf(cliente.cpf)

    query = select(ClienteModel).where(ClienteModel.id == cliente_id)
    result = await db.execute(query)
    cliente_existente = result.scalars().first()

    if not cliente_existente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    try:
        cliente_existente.nome = cliente.nome
        cliente_existente.email = cliente.email
        cliente_existente.telefone = cliente.telefone
        cliente_existente.cpf = cliente.cpf

        await db.commit()
        await db.refresh(cliente_existente)

        return {"status": "OK", "cliente": {
            "id": cliente_existente.id,
            "nome": cliente_existente.nome,
            "email": cliente_existente.email,
            "telefone": cliente_existente.telefone,
            "cpf": cliente_existente.cpf
        }}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar cliente: {str(e)}")


@router.delete("/{cliente_id}", summary="Excluir Cliente")
async def excluir_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui um cliente da API."""
    query = select(ClienteModel).where(ClienteModel.id == cliente_id)
    result = await db.execute(query)
    cliente_existente = result.scalars().first()

    if not cliente_existente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    try:
        await db.delete(cliente_existente)
        await db.commit()
        return {"status": "OK", "mensagem": "Cliente excluído com sucesso."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir cliente: {str(e)}")
