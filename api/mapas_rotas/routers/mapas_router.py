import asyncio
import io
import os

import osmnx as ox
import pandas as pd
from corridas.models.corrida_model import CorridaModel
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from geopy.geocoders import Nominatim
from mapas_rotas.services.visualizar_mapa import criar_mapa_interativo
from core.dependencies import get_db
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from unidecode import unidecode

router = APIRouter(prefix="/mapas_rotas", tags=["Mapas"])


async def obter_nome_rua_bairro(coordenada):
    """Obtém nome da rua e bairro a partir das coordenadas."""
    geolocator = Nominatim(user_agent="mapa_interativo")

    async def reverse_geocode():
        try:
            location = geolocator.reverse(coordenada, language='pt', exactly_one=True)
            if location:
                address = location.raw.get("address", {})
                return address.get("road", "Desconhecido"), address.get("suburb", "Desconhecido")
        except Exception:
            return "Desconhecido", "Desconhecido"

    return await asyncio.to_thread(reverse_geocode)


async def processar_no_grafo(node, grafo, nodes_data):
    """Processa um nó do grafo e adiciona os dados na lista compartilhada."""
    latitude = grafo.nodes[node]["y"]
    longitude = grafo.nodes[node]["x"]
    nome_rua, bairro = await obter_nome_rua_bairro((latitude, longitude))

    nodes_data["node_id"].append(node)
    nodes_data["latitude"].append(latitude)
    nodes_data["longitude"].append(longitude)
    nodes_data["nome_rua"].append(nome_rua)
    nodes_data["bairro"].append(bairro)


@router.get("/gerar_mapa", status_code=status.HTTP_200_OK)
async def gerar_mapa_interativo(cidade: str):
    """Gera o grafo da cidade e armazena informações de localização."""
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    graphml_path = f"data/{nome_cidade}-map.graphml"
    csv_path = f"data/{nome_cidade}-localizacoes.csv"

    if os.path.exists(graphml_path) and os.path.exists(csv_path):
        return {"message": "Arquivos existentes encontrados."}

    try:
        grafo = await asyncio.to_thread(ox.graph_from_place, cidade, network_type="drive")
        await asyncio.to_thread(ox.save_graphml, grafo, filepath=graphml_path)

        nodes_data = {"node_id": [], "latitude": [], "longitude": [], "nome_rua": [], "bairro": []}

        tasks = [processar_no_grafo(node, grafo, nodes_data) for node in grafo.nodes]
        await asyncio.gather(*tasks)

        df = pd.DataFrame(nodes_data)
        await asyncio.to_thread(df.to_csv, csv_path, index=False)

        return {"message": "Dados do mapa gerados com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do mapa: {str(e)}")


@router.get("/coordenadas_aleatorias", status_code=status.HTTP_200_OK)
async def coordenadas_aleatorias_para_rota(cidade: str):
    """Seleciona pontos de origem e destino aleatórios para uma cidade."""
    nome_cidade = unidecode(cidade.strip().lower().replace(" ", "-"))
    csv_path = f"data/{nome_cidade}-localizacoes.csv"

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Arquivo de localizações não encontrado para a cidade especificada.")

    df_nodes = await asyncio.to_thread(pd.read_csv, csv_path)
    df_nodes_filtrado = df_nodes[df_nodes["bairro"] != "Desconhecido"]

    if df_nodes_filtrado.empty:
        raise HTTPException(status_code=400, detail="Não há locais com bairros válidos para selecionar.")

    amostra = await asyncio.to_thread(lambda: df_nodes_filtrado.sample(n=2).to_dict(orient="records"))
    origem, destino = amostra[0], amostra[1]

    return {
        "origem": {
            "latitude": origem["latitude"],
            "longitude": origem["longitude"],
            "nome_rua": origem["nome_rua"],
            "bairro": origem["bairro"]
        },
        "destino": {
            "latitude": destino["latitude"],
            "longitude": destino["longitude"],
            "nome_rua": destino["nome_rua"],
            "bairro": destino["bairro"]
        }
    }


@router.get("/visualizar_corrida", status_code=status.HTTP_200_OK, summary="Visualizar mapa interativo de uma corrida")
async def visualizar_mapa_de_corrida(corrida_id: int, db: Session = Depends(get_db)):
    """Gera e retorna um mapa interativo com a rota de uma corrida."""
    query = select(CorridaModel).filter(CorridaModel.id == corrida_id)
    result = await db.execute(query)
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")

    if not corrida.coordenadas_rota:
        raise HTTPException(status_code=400, detail="Nenhuma rota disponível para esta corrida")

    try:
        coordenadas_rota = [
            (float(lat), float(lon))
            for point in corrida.coordenadas_rota.split("|")
            for lat, lon in [point.split(",")]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar coordenadas da rota: {str(e)}")

    html_conteudo = criar_mapa_interativo(
        origem=(corrida.origem_latitude, corrida.origem_longitude),
        destino=(corrida.destino_latitude, corrida.destino_longitude),
        coordenadas_rota=coordenadas_rota,
        distancia_km=corrida.distancia_km,
        origem_info={
            "nome_rua": corrida.origem_rua,
            "bairro": corrida.origem_bairro
        },
        destino_info={
            "nome_rua": corrida.destino_rua,
            "bairro": corrida.destino_bairro
        }
    )

    stream = io.StringIO(html_conteudo)
    headers = {"Content-Disposition": f"attachment; filename=mapa-corrida-{corrida_id}.html"}
    return StreamingResponse(stream, media_type="text/html", headers=headers)
