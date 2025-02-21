import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import osmnx as ox
import pandas as pd
from fastapi import APIRouter, HTTPException, status
from geopy.geocoders import Nominatim
from unidecode import unidecode

router = APIRouter(prefix="/mapas", tags=["Mapas"])


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


async def processar_no(node, grafo, nodes_data):
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
async def gerar_dados_mapa(cidade: str):
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

        tasks = [processar_no(node, grafo, nodes_data) for node in grafo.nodes]
        await asyncio.gather(*tasks)

        df = pd.DataFrame(nodes_data)
        await asyncio.to_thread(df.to_csv, csv_path, index=False)

        return {"message": "Dados do mapa gerados com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do mapa: {str(e)}")



@router.get("/selecionar_coordenadas_aleatorias", status_code=status.HTTP_200_OK)
async def selecionar_coordenadas_aleatorias(cidade: str):
    """Seleciona pontos de origem e destino aleatórios para uma cidade."""
    nome_cidade = unidecode(cidade.strip().lower().replace(" ", "-"))
    csv_path = f"data/{nome_cidade}-localizacoes.csv"

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Arquivo de localizações não encontrado para a cidade especificada.")

    df_nodes = await asyncio.to_thread(pd.read_csv, csv_path)
    df_nodes_filtrado = df_nodes[df_nodes["bairro"] != "Desconhecido"]

    if df_nodes_filtrado.empty:
        raise HTTPException(status_code=400, detail="Não há locais com bairros válidos para selecionar.")

    # Seleciona duas linhas aleatórias do DataFrame e converte para dicionário
    amostra = await asyncio.to_thread(lambda: df_nodes_filtrado.sample(n=2).to_dict(orient="records"))

    origem, destino = amostra[0], amostra[1]  # Aqui garantimos que pegamos corretamente os dois itens

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
