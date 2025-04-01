import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from carros.models.carro_model import CarroModel
from core.dependencies import get_db

router = APIRouter(prefix="/carros", tags=["Carros"])

# 📌 Modelo de entrada para criação e edição de carro
class CarroCreate(BaseModel):
    categoria: str
    marca: str
    modelo: str
    motor: str
    versao: str
    transmissao: str
    ar_condicionado: str
    direcao: str
    combustivel: Optional[str] = None
    km_etanol_cidade: Optional[float] = None  # Alterado para float
    km_etanol_estrada: Optional[float] = None  # Alterado para float
    km_gasolina_cidade: Optional[float] = None  # Alterado para float
    km_gasolina_estrada: Optional[float] = None  # Alterado para float
    ano: Optional[int] = None

# 📌 Modelo de entrada para edição de carro
class CarroUpdate(BaseModel):
    categoria: str
    marca: str
    modelo: str
    motor: str
    versao: str
    transmissao: str
    ar_condicionado: str
    direcao: str
    combustivel: str = None
    km_etanol_cidade: str = None
    km_etanol_estrada: str = None
    km_gasolina_cidade: str = None
    km_gasolina_estrada: str = None
    ano: Optional[int] = None

@router.get("/listar/", summary="Listar Carros")
async def listar_carros(db: AsyncSession = Depends(get_db)):
    """Lista todos os carros cadastrados na API"""
    query = select(CarroModel)
    result = await db.execute(query)  # 🔄 Agora é assíncrono
    carros = result.scalars().all()

    if not carros:
        return {"mensagem": "Nenhum carro cadastrado."}

    # Retorna os carros em formato JSON serializável
    return [{"id": c.id, "categoria": c.categoria, "marca": c.marca, "modelo": c.modelo,
             "motor": c.motor, "versao": c.versao, "transmissao": c.transmissao,
             "ar_condicionado": c.ar_condicionado, "direcao": c.direcao, "combustivel": c.combustivel,
             "km_etanol_cidade": c.km_etanol_cidade, "km_etanol_estrada": c.km_etanol_estrada,
             "km_gasolina_cidade": c.km_gasolina_cidade, "km_gasolina_estrada": c.km_gasolina_estrada,
             "ano": c.ano} for c in carros]

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Carro")
async def criar_carro(carro: CarroCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo carro na API"""
    # Verificar se já existe um carro com os mesmos dados
    query = select(CarroModel).where(
        (CarroModel.marca == carro.marca) &
        (CarroModel.modelo == carro.modelo) &
        (CarroModel.ano == carro.ano) &
        (CarroModel.categoria == carro.categoria) &
        (CarroModel.motor == carro.motor) &
        (CarroModel.versao == carro.versao) &
        (CarroModel.transmissao == carro.transmissao) &
        (CarroModel.ar_condicionado == carro.ar_condicionado) &
        (CarroModel.direcao == carro.direcao) &
        (CarroModel.combustivel == carro.combustivel) &
        (CarroModel.km_etanol_cidade == carro.km_etanol_cidade) &
        (CarroModel.km_etanol_estrada == carro.km_etanol_estrada) &
        (CarroModel.km_gasolina_cidade == carro.km_gasolina_cidade) &
        (CarroModel.km_gasolina_estrada == carro.km_gasolina_estrada)
    )
    result = await db.execute(query)  # 🔄 Agora é assíncrono
    carro_existente = result.scalars().first()

    if carro_existente:
        raise HTTPException(status_code=400, detail=f"Carro '{carro.marca} {carro.modelo}' já cadastrado.")

    try:
        novo_carro = CarroModel(
            categoria=carro.categoria,
            marca=carro.marca,
            modelo=carro.modelo,
            motor=carro.motor,
            versao=carro.versao,
            transmissao=carro.transmissao,
            ar_condicionado=carro.ar_condicionado,
            direcao=carro.direcao,
            combustivel=carro.combustivel,
            km_etanol_cidade=carro.km_etanol_cidade,
            km_etanol_estrada=carro.km_etanol_estrada,
            km_gasolina_cidade=carro.km_gasolina_cidade,
            km_gasolina_estrada=carro.km_gasolina_estrada,
            ano=carro.ano
        )

        db.add(novo_carro)
        await db.commit()  # 🔄 Agora é assíncrono
        await db.refresh(novo_carro)  # 🔄 Agora é assíncrono

        return {"status": "OK", "carro": {
            "id": novo_carro.id,
            "categoria": novo_carro.categoria,
            "marca": novo_carro.marca,
            "modelo": novo_carro.modelo,
            "motor": novo_carro.motor,
            "versao": novo_carro.versao,
            "transmissao": novo_carro.transmissao,
            "ar_condicionado": novo_carro.ar_condicionado,
            "direcao": novo_carro.direcao,
            "combustivel": novo_carro.combustivel,
            "km_etanol_cidade": novo_carro.km_etanol_cidade,
            "km_etanol_estrada": novo_carro.km_etanol_estrada,
            "km_gasolina_cidade": novo_carro.km_gasolina_cidade,
            "km_gasolina_estrada": novo_carro.km_gasolina_estrada,
            "ano": novo_carro.ano
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar carro: {str(e)}")

@router.put("/{carro_id}", status_code=status.HTTP_200_OK, summary="Editar Carro")
async def editar_carro(carro_id: int, carro: CarroUpdate, db: AsyncSession = Depends(get_db)):
    """Edita os dados de um carro existente"""
    query = select(CarroModel).where(CarroModel.id == carro_id)
    result = await db.execute(query)  # 🔄 Agora é assíncrono
    carro_existente = result.scalars().first()

    if not carro_existente:
        raise HTTPException(status_code=404, detail="Carro não encontrado.")

    try:
        # Atualiza os dados do carro
        carro_existente.categoria = carro.categoria
        carro_existente.marca = carro.marca
        carro_existente.modelo = carro.modelo
        carro_existente.motor = carro.motor
        carro_existente.versao = carro.versao
        carro_existente.transmissao = carro.transmissao
        carro_existente.ar_condicionado = carro.ar_condicionado
        carro_existente.direcao = carro.direcao
        carro_existente.combustivel = carro.combustivel
        carro_existente.km_etanol_cidade = carro.km_etanol_cidade
        carro_existente.km_etanol_estrada = carro.km_etanol_estrada
        carro_existente.km_gasolina_cidade = carro.km_gasolina_cidade
        carro_existente.km_gasolina_estrada = carro.km_gasolina_estrada
        carro_existente.ano = carro.ano

        await db.commit()  # 🔄 Agora é assíncrono
        await db.refresh(carro_existente)  # 🔄 Agora é assíncrono

        return {"status": "OK", "carro": {
            "id": carro_existente.id,
            "categoria": carro_existente.categoria,
            "marca": carro_existente.marca,
            "modelo": carro_existente.modelo,
            "motor": carro_existente.motor,
            "versao": carro_existente.versao,
            "transmissao": carro_existente.transmissao,
            "ar_condicionado": carro_existente.ar_condicionado,
            "direcao": carro_existente.direcao,
            "combustivel": carro_existente.combustivel,
            "km_etanol_cidade": carro_existente.km_etanol_cidade,
            "km_etanol_estrada": carro_existente.km_etanol_estrada,
            "km_gasolina_cidade": carro_existente.km_gasolina_cidade,
            "km_gasolina_estrada": carro_existente.km_gasolina_estrada,
            "ano": carro_existente.ano
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar carro: {str(e)}")

@router.delete("/{carro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir Carro")
async def excluir_carro(carro_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui um carro da API"""
    query = select(CarroModel).where(CarroModel.id == carro_id)
    result = await db.execute(query)  # 🔄 Agora é assíncrono
    carro_existente = result.scalars().first()

    if not carro_existente:
        raise HTTPException(status_code=404, detail="Carro não encontrado.")

    try:
        await db.delete(carro_existente)
        await db.commit()  # 🔄 Agora é assíncrono

        return {"status": "OK", "mensagem": "Carro excluído com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir carro: {str(e)}")
