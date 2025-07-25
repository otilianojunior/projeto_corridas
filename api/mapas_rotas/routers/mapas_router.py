import asyncio
import io
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import osmnx as ox
import pandas as pd
from core.dependencies import get_db
from corridas.models.corrida_model import CorridaModel
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from geopy.geocoders import Nominatim
from mapas_rotas.services.visualizar_mapa import criar_mapa_interativo
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from unidecode import unidecode

router = APIRouter(prefix="/mapas_rotas", tags=["Mapas"])

BASE_DIR = Path(__file__).resolve().parents[2] / "resources"
BASE_DIR.mkdir(parents=True, exist_ok=True)


# Carrega um grafo de um arquivo local se existir, ou baixa da internet e salva localmente.
def carregar_ou_baixar_grafo(cidade: str, caminho: str):
    if os.path.exists(caminho):
        print(f"Carregando grafo de '{caminho}'...")
        grafo = ox.load_graphml(caminho)
    else:
        print("Baixando grafo da cidade...")
        grafo = ox.graph_from_place(cidade, network_type="drive")
        ox.save_graphml(grafo, filepath=caminho)
        print(f"Grafo salvo em '{caminho}'.")
    return grafo


# Extrai informações de endereço (rua, bairro, CEP) de uma string JSON.
def extrair_dados(json_str: str):
    try:
        dados = json.loads(json_str)
        endereco = dados.get("address", {})
        return {
            "rua": endereco.get("road"),
            "bairro": endereco.get("suburb"),
            "cep": endereco.get("postcode"),
        }
    except Exception:
        return {"rua": None, "bairro": None, "cep": None}


# Realiza geocodificação reversa para obter informações de endereço a partir de coordenadas.
async def reverse_geocode(lat, lon, geolocator):
    def _reverso():
        try:
            location = geolocator.reverse((lat, lon), language='pt', timeout=10)
            return json.dumps(location.raw, ensure_ascii=False) if location else ""
        except Exception as e:
            print(f"Erro geocodificação reversa: {e}")
            return ""

    return await asyncio.to_thread(_reverso)


#  Processa um nó do grafo para obter suas coordenadas e dados de endereço.
async def processar_no_grafo(node, grafo, geolocator, nodes_data):
    lat = grafo.nodes[node]["y"]
    lon = grafo.nodes[node]["x"]
    raw_data = await reverse_geocode(lat, lon, geolocator)

    nodes_data["node_id"].append(node)
    nodes_data["latitude"].append(lat)
    nodes_data["longitude"].append(lon)
    nodes_data["raw_data"].append(raw_data)


# Gera um grafo da cidade especificada, salva dados brutos e tratados em CSVs.
@router.get("/gerar_mapa", status_code=status.HTTP_200_OK)
async def gerar_mapa(cidade: str):
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    os.makedirs(BASE_DIR, exist_ok=True)

    graphml_path = os.path.join(BASE_DIR, f"{nome_cidade}.graphml")
    bruto_path = os.path.join(BASE_DIR, f"{nome_cidade}_enderecos_brutos.csv")
    tratado_path = os.path.join(BASE_DIR, f"{nome_cidade}_enderecos_tratados.csv")

    if os.path.exists(graphml_path) and os.path.exists(tratado_path):
        return {
            "message": "Arquivos existentes encontrados.",
            "arquivos": {
                "grafo": graphml_path,
                "enderecos_tratados": tratado_path
            }
        }

    try:
        inicio = datetime.now()

        grafo = await asyncio.to_thread(carregar_ou_baixar_grafo, cidade, graphml_path)
        nodes = list(grafo.nodes)
        total_nodes = len(nodes)
        total_lotes = total_nodes // 2 + (1 if total_nodes % 2 != 0 else 0)

        print(f"Total de nós no grafo: {total_nodes}")
        print(f"Iniciando processamento de {total_lotes} lotes com 2 nós por lote...")

        fim_estimado = inicio + timedelta(seconds=total_lotes)
        print(f"Previsão de término: {fim_estimado.strftime('%H:%M:%S')}")

        geolocator = Nominatim(user_agent="mapa_interativo")

        nodes_data = {
            "node_id": [],
            "latitude": [],
            "longitude": [],
            "raw_data": []
        }

        for i in range(0, total_nodes, 2):
            lote = nodes[i:i + 2]
            print(f"Processando lote {i // 2 + 1}/{total_lotes} - nós: {lote}")
            tasks = [processar_no_grafo(node, grafo, geolocator, nodes_data) for node in lote]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

            if (i + 2) % 100 == 0 or (i + 2) >= total_nodes:
                df_temp = pd.DataFrame(nodes_data)
                await asyncio.to_thread(df_temp.to_csv, bruto_path, index=False, encoding='utf-8')
                print(f"Progresso salvo em {bruto_path}")

        # Após o loop, garantir salvamento final
        df_bruto = pd.DataFrame(nodes_data)
        await asyncio.to_thread(df_bruto.to_csv, bruto_path, index=False, encoding='utf-8')
        print(f"Endereços brutos salvos em {bruto_path}")

        df_bruto['raw_data'] = df_bruto['raw_data'].astype(str)
        dados_extraidos = df_bruto['raw_data'].apply(extrair_dados).apply(pd.Series)

        df_final = pd.concat([df_bruto[["node_id", "latitude", "longitude"]], dados_extraidos], axis=1)
        df_filtrado = df_final[~(df_final['rua'].isna() & df_final['bairro'].isna())]

        await asyncio.to_thread(df_filtrado.to_csv, tratado_path, index=False, encoding='utf-8')
        print(f"Endereços tratados salvos em {tratado_path}")

        fim_real = datetime.now()
        duracao = fim_real - inicio
        minutos, segundos = divmod(duracao.total_seconds(), 60)

        print(f"Tempo total de execução: {int(minutos)} minutos e {int(segundos)} segundos")

        return {
            "message": "Dados do mapa gerados com sucesso!",
            "tempo_execucao": f"{int(minutos)} minutos e {int(segundos)} segundos",
            "arquivos": {
                "grafo": graphml_path,
                "enderecos_brutos": bruto_path,
                "enderecos_tratados": tratado_path
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do mapa: {str(e)}")


# Seleciona dois pontos aleatórios (origem e destino) de uma cidade para criar uma rota.
@router.get("/coordenadas_aleatorias", status_code=status.HTTP_200_OK)
async def coordenadas_aleatorias_para_rota(cidade: str):
    nome_cidade = unidecode(cidade.split(",")[0].strip().lower().replace(" ", "-"))
    csv_path = os.path.join(BASE_DIR, f"{nome_cidade}_enderecos_tratados.csv")

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404,
                            detail="Arquivo de localizações não encontrado para a cidade especificada.")

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
            "nome_rua": origem["rua"],
            "bairro": origem["bairro"]
        },
        "destino": {
            "latitude": destino["latitude"],
            "longitude": destino["longitude"],
            "nome_rua": destino["rua"],
            "bairro": destino["bairro"]
        }
    }


# Gera e retorna um mapa interativo com a rota de uma corrida específica.
@router.get("/visualizar_corrida", status_code=status.HTTP_200_OK, summary="Visualizar mapa interativo de uma corrida")
async def visualizar_mapa_de_corrida(corrida_id: int, db: Session = Depends(get_db)):
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

    html_conteudo = criar_mapa_interativo(corrida, coordenadas_rota)

    stream = io.StringIO(html_conteudo)
    headers = {"Content-Disposition": f"attachment; filename=mapa-corrida-{corrida_id}.html"}
    return StreamingResponse(stream, media_type="text/html", headers=headers)