import os
import time
from concurrent.futures import ThreadPoolExecutor

import osmnx as ox
import pandas as pd
from fastapi import APIRouter, HTTPException, status
from geopy.geocoders import Nominatim
from unidecode import unidecode

router = APIRouter(prefix="/mapas", tags=["Mapas"])


def obter_nome_rua_bairro(coordenada):
    geolocator = Nominatim(user_agent="mapa_interativo")
    location = geolocator.reverse(coordenada, language='pt', exactly_one=True)
    time.sleep(1)
    if location:
        address = location.raw.get("address", {})
        return address.get("road", "Desconhecido"), address.get("suburb", "Desconhecido")
    return "Desconhecido", "Desconhecido"


def processar_no(node, grafo, nodes_data):
    latitude = grafo.nodes[node]["y"]
    longitude = grafo.nodes[node]["x"]
    nome_rua, bairro = obter_nome_rua_bairro((latitude, longitude))

    nodes_data["node_id"].append(node)
    nodes_data["latitude"].append(latitude)
    nodes_data["longitude"].append(longitude)
    nodes_data["nome_rua"].append(nome_rua)
    nodes_data["bairro"].append(bairro)


@router.get("/gerar_mapa", status_code=status.HTTP_200_OK)
async def gerar_dados_mapa(cidade: str):
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    graphml_path = f"data/{nome_cidade}-map.graphml"
    csv_path = f"data/{nome_cidade}-localizacoes.csv"

    # Verifica se os arquivos já existem
    if os.path.exists(graphml_path) and os.path.exists(csv_path):
        return {"message": "Arquivos existentes encontrados."}

    # Gera o grafo da cidade
    try:
        grafo = ox.graph_from_place(cidade, network_type="drive")
        ox.save_graphml(grafo, filepath=graphml_path)

        nodes_data = {"node_id": [], "latitude": [], "longitude": [], "nome_rua": [], "bairro": []}

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(lambda node: processar_no(node, grafo, nodes_data), grafo.nodes)

        pd.DataFrame(nodes_data).to_csv(csv_path, index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do mapa: {str(e)}")


@router.get("/selecionar_coordenadas_aleatorias", status_code=status.HTTP_200_OK,
            summary="Selecionar coordenadas aleatórias para pontos de origem e destino")
async def selecionar_coordenadas_aleatorias(cidade: str):
    nome_cidade = unidecode(cidade.strip().lower().replace(" ", "-"))
    csv_path = f"data/{nome_cidade}-localizacoes.csv"

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404,
                            detail="Arquivo de localizações não encontrado para a cidade especificada.")

    df_nodes = pd.read_csv(csv_path)
    df_nodes_filtrado = df_nodes[df_nodes["bairro"] != "Desconhecido"]

    if df_nodes_filtrado.empty:
        raise HTTPException(status_code=400,
                            detail="Não há locais com bairros válidos para selecionar.")

    origem = df_nodes_filtrado.sample(n=1).iloc[0]
    destino = df_nodes_filtrado.sample(n=1).iloc[0]

    # Garante que os pontos de origem e destino sejam distintos
    while origem["node_id"] == destino["node_id"]:
        destino = df_nodes_filtrado.sample(n=1).iloc[0]

    origem_info = {
        "latitude": origem["latitude"],
        "longitude": origem["longitude"],
        "nome_rua": origem["nome_rua"],
        "bairro": origem["bairro"],
    }

    destino_info = {
        "latitude": destino["latitude"],
        "longitude": destino["longitude"],
        "nome_rua": destino["nome_rua"],
        "bairro": destino["bairro"],
    }

    return {"origem": origem_info, "destino": destino_info}
