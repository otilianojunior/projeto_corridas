import os
import networkx as nx
import osmnx as ox
from unidecode import unidecode


def calcular_rota_mais_curta(cidade, origem_latitude, origem_longitude, destino_latitude, destino_longitude):
    # Formatar o nome da cidade para o nome do arquivo
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    grafo_path = f"data/{nome_cidade}-map.graphml"

    # Verificar se o arquivo do grafo existe
    if not os.path.exists(grafo_path):
        raise FileNotFoundError(f"Arquivo não encontrado. Execute a rota gerar_mapa primeiro.")

    # Carregar o grafo da cidade
    grafo = ox.load_graphml(grafo_path)

    try:
        # Encontrar os nós mais próximos da origem e destino
        origem_no = ox.distance.nearest_nodes(grafo, X=origem_longitude, Y=origem_latitude)
        destino_no = ox.distance.nearest_nodes(grafo, X=destino_longitude, Y=destino_latitude)
    except ValueError as e:
        raise ValueError(f"Erro ao encontrar nós próximos: {e}")

    # Calcular a rota mais curta entre os nós
    rota = nx.shortest_path(grafo, origem_no, destino_no, weight="length")

    # Obter as coordenadas ao longo da rota
    coordenadas_rota = [(grafo.nodes[node]["y"], grafo.nodes[node]["x"]) for node in rota]

    # Calcular a distância total em metros
    distancia_metros = sum(
        nx.get_edge_attributes(grafo, "length")[(rota[i], rota[i + 1], 0)]
        for i in range(len(rota) - 1)
    )

    # Converter a distância para quilômetros
    distancia_km = distancia_metros / 1000

    return rota, coordenadas_rota, distancia_km
