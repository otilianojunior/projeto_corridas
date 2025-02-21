import os
import networkx as nx
import osmnx as ox
from unidecode import unidecode
import asyncio


async def calcular_rota_mais_curta(cidade, origem_latitude, origem_longitude, destino_latitude, destino_longitude):
    """Calcula a rota mais curta entre origem e destino usando um grafo pré-gerado."""
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    grafo_path = f"data/{nome_cidade}-map.graphml"

    if not os.path.exists(grafo_path):
        raise FileNotFoundError(f"Arquivo não encontrado. Execute a rota gerar_mapa primeiro.")

    # Carregar o grafo da cidade de forma assíncrona
    loop = asyncio.get_running_loop()
    grafo = await loop.run_in_executor(None, ox.load_graphml, grafo_path)

    try:
        # Encontrar os nós mais próximos da origem e destino
        origem_no = await loop.run_in_executor(
            None, ox.distance.nearest_nodes, grafo, origem_longitude, origem_latitude
        )
        destino_no = await loop.run_in_executor(
            None, ox.distance.nearest_nodes, grafo, destino_longitude, destino_latitude
        )
    except ValueError as e:
        raise ValueError(f"Erro ao encontrar nós próximos: {e}")

    try:
        # Calcular a rota mais curta de forma assíncrona
        rota = await loop.run_in_executor(
            None, nx.shortest_path, grafo, origem_no, destino_no, "length"
        )
    except nx.NetworkXNoPath:
        raise ValueError("Não foi possível encontrar um caminho entre os pontos fornecidos.")

    # Obter coordenadas da rota
    coordenadas_rota = [
        (grafo.nodes[node]["y"], grafo.nodes[node]["x"]) for node in rota
    ]

    # Calcular a distância total em metros
    distancia_metros = sum(
        nx.get_edge_attributes(grafo, "length").get((rota[i], rota[i + 1], 0), 0)
        for i in range(len(rota) - 1)
    )

    distancia_km = distancia_metros / 1000

    return rota, coordenadas_rota, distancia_km
