from typing import Optional

from carros.models.carro_model import CarroModel
from core.dependencies import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

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
    km_etanol_cidade: Optional[float] = None
    km_etanol_estrada: Optional[float] = None
    km_gasolina_cidade: Optional[float] = None
    km_gasolina_estrada: Optional[float] = None
    ano: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "categoria": "SUV",
                "marca": "Toyota",
                "modelo": "Corolla Cross",
                "motor": "2.0 Flex",
                "versao": "XRE",
                "transmissao": "Automática",
                "ar_condicionado": "Sim",
                "direcao": "Elétrica",
                "combustivel": "Flex",
                "km_etanol_cidade": 8.0,
                "km_etanol_estrada": 10.5,
                "km_gasolina_cidade": 11.5,
                "km_gasolina_estrada": 13.8,
                "ano": 2024
            }
        }


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


# 📌 Rota para listar todos os carros cadastrados
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


# 📌 Rota para criar um novo carro
@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar Carro")
async def criar_carro(carro: CarroCreate, db: AsyncSession = Depends(get_db)):
    """
    Cria um novo carro na API, evitando duplicidade exata:
    - Campos `None` são comparados com `.is_(None)`
    - Campos numéricos podem ser arredondados para evitar imprecisões
    """

    filtros = [
        CarroModel.categoria == carro.categoria,
        CarroModel.marca == carro.marca,
        CarroModel.modelo == carro.modelo,
        CarroModel.motor == carro.motor,
        CarroModel.versao == carro.versao,
        CarroModel.transmissao == carro.transmissao,
        CarroModel.ar_condicionado == carro.ar_condicionado,
        CarroModel.direcao == carro.direcao,
    ]

    # String opcional
    if carro.combustivel is not None:
        filtros.append(CarroModel.combustivel == carro.combustivel)
    else:
        filtros.append(CarroModel.combustivel.is_(None))

    # Floats opcionais (com arredondamento a 2 casas, se desejar)
    def float_filter(column, value):
        if value is not None:
            # opcional: usar func.round para maior segurança no SQL
            return func.round(column, 2) == round(value, 2)
        return column.is_(None)

    filtros.append(float_filter(CarroModel.km_etanol_cidade, carro.km_etanol_cidade))
    filtros.append(float_filter(CarroModel.km_etanol_estrada, carro.km_etanol_estrada))
    filtros.append(float_filter(CarroModel.km_gasolina_cidade, carro.km_gasolina_cidade))
    filtros.append(float_filter(CarroModel.km_gasolina_estrada, carro.km_gasolina_estrada))

    # Ano opcional
    if carro.ano is not None:
        filtros.append(CarroModel.ano == carro.ano)
    else:
        filtros.append(CarroModel.ano.is_(None))

    # Executa a consulta de duplicata
    query = select(CarroModel).where(and_(*filtros))
    result = await db.execute(query)
    existente = result.scalars().first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um carro cadastrado com estas mesmas especificações."
        )

    # Se não existir, cria normalmente
    novo = CarroModel(
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
    db.add(novo)
    await db.commit()
    await db.refresh(novo)

    return {
        "status": "OK",
        "carro": {
            "id": novo.id,
            "categoria": novo.categoria,
            "marca": novo.marca,
            "modelo": novo.modelo,
            "motor": novo.motor,
            "versao": novo.versao,
            "transmissao": novo.transmissao,
            "ar_condicionado": novo.ar_condicionado,
            "direcao": novo.direcao,
            "combustivel": novo.combustivel,
            "km_etanol_cidade": novo.km_etanol_cidade,
            "km_etanol_estrada": novo.km_etanol_estrada,
            "km_gasolina_cidade": novo.km_gasolina_cidade,
            "km_gasolina_estrada": novo.km_gasolina_estrada,
            "ano": novo.ano,
        }
    }


# 📌 Rota para editar os dados de um carro existente
@router.put("/{carro_id}", status_code=status.HTTP_200_OK, summary="Editar Carro")
async def editar_carro(carro_id: int, carro: CarroUpdate, db: AsyncSession = Depends(get_db)):
    """Edita os dados de um carro existente"""
    # Busca o carro pelo ID e atualiza os dados fornecidos
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


# 📌 Rota para excluir um carro existente
@router.delete("/{carro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir Carro")
async def excluir_carro(carro_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui um carro da API"""
    # Busca o carro pelo ID e o remove do banco de dados
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
