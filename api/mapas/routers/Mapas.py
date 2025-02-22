import os
import io

import osmnx as ox
import pandas as pd
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from geopy.geocoders import Nominatim
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from unidecode import unidecode

from corridas.models.CorridaModel import CorridaModel
# Importe a função get_db de onde ela estiver definida, por exemplo:
from shared.dependencies import get_db
# Certifique-se de que a função criar_mapa_interativo esteja importada corretamente:
from mapas.services.visualizar import criar_mapa_interativo


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
        raise HTTPException(status_code=404,
                            detail="Arquivo de localizações não encontrado para a cidade especificada.")

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




@router.get("/visualizar_mapa_corrida", status_code=status.HTTP_200_OK,
            summary="Gerar e visualizar mapa interativo da corrida")
async def visualizar_mapa_corrida(corrida_id: int, db: Session = Depends(get_db)):
    # Buscar a corrida pelo ID usando execução assíncrona
    query = select(CorridaModel).filter(CorridaModel.id == corrida_id)
    result = await db.execute(query)  # Executar a consulta de forma assíncrona
    corrida = result.scalars().first()

    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")

    # Verificar se existem coordenadas de rota armazenadas
    if not corrida.cordenadas_rota:
        raise HTTPException(status_code=400, detail="Nenhuma rota disponível para esta corrida")

    # Converter a string de coordenadas para lista de tuplas
    try:
        coordenadas_rota = [
            (float(lat), float(lon))
            for point in corrida.cordenadas_rota.split("|")
            for lat, lon in [point.split(",")]
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar coordenadas da rota: {str(e)}"
        )

    # Gerar o mapa interativo em memória (a função deve retornar uma string com o HTML)
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

    # Converter o conteúdo HTML para um stream de bytes (ou string)
    stream = io.StringIO(html_conteudo)

    # Retornar a resposta para download sem salvar arquivo físico
    headers = {"Content-Disposition": f"attachment; filename=mapa-corrida-{corrida_id}.html"}
    return StreamingResponse(stream, media_type="text/html", headers=headers)
