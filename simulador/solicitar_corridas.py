import argparse
import asyncio
import random
import time
import urllib.parse
from datetime import datetime, timedelta

import aiohttp

API_URL = "http://127.0.0.1:8000"
CIDADE = "Vitória da Conquista, Bahia"
TIMEOUT = 120
MAX_CONCORRENTES = 5

semaforo = asyncio.Semaphore(MAX_CONCORRENTES)


# Obtém motoristas disponíveis através da API.
async def obter_motoristas(session: aiohttp.ClientSession):
    url = f"{API_URL}/motoristas/listar_disponiveis/"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            dados = await response.json()
            return dados if isinstance(dados, list) else []
        else:
            print(f"⚠️ Erro ao buscar motoristas: {response.status} - {await response.text()}")
            return []


# Obtém clientes que ainda não têm corridas vinculadas.
async def obter_clientes(session: aiohttp.ClientSession):
    url = f"{API_URL}/clientes/listar_sem_corrida/"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            dados = await response.json()
            return dados if isinstance(dados, list) else []
        else:
            print(f"⚠️ Erro ao buscar clientes: {response.status} - {await response.text()}")
            return []


# Obtém coordenadas aleatórias para origem e destino.
async def obter_coordenadas(session: aiohttp.ClientSession):
    url = f"{API_URL}/mapas_rotas/coordenadas_aleatorias?cidade={urllib.parse.quote(CIDADE)}"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"⚠️ Erro ao buscar coordenadas: {response.status} - {await response.text()}")
            return None


# Gera um horário aleatório entre os intervalos de pico ou horários gerais.
def gerar_horario():
    base = datetime(2024, 6, 1)
    picos = [("07:00:00", "08:00:00"), ("12:00:00", "13:00:00"), ("17:30:00", "18:30:00")]
    if random.random() < 0.15:
        inicio, fim = random.choice(picos)
        dt_inicio = datetime.strptime(f"{base.date()} {inicio}", "%Y-%m-%d %H:%M:%S")
        dt_fim = datetime.strptime(f"{base.date()} {fim}", "%Y-%m-%d %H:%M:%S")
    else:
        dt_inicio = datetime.strptime(f"{base.date()} 00:00:00", "%Y-%m-%d %H:%M:%S")
        dt_fim = datetime.strptime(f"{base.date()} 23:59:59", "%Y-%m-%d %H:%M:%S")

    segundos = random.randint(0, int((dt_fim - dt_inicio).total_seconds()))
    return (dt_inicio + timedelta(seconds=segundos)).isoformat()


# Envia uma solicitação de corrida para a API com os dados gerados.
async def solicitar_corrida(session: aiohttp.ClientSession, id_cliente: int):
    async with semaforo:
        coordenadas = await obter_coordenadas(session)
        if not coordenadas:
            return False

        origem, destino = coordenadas.get("origem"), coordenadas.get("destino")
        if not origem or not destino:
            return False

        motoristas = await obter_motoristas(session)
        if not motoristas:
            print("⚠️ Nenhum motorista disponível.")
            return False

        try:
            id_motorista = random.choice(motoristas)["id"]
        except Exception as e:
            print(f"⚠️ Erro ao escolher motorista: {e}")
            return False

        corrida = {
            "cliente": {"id_cliente": id_cliente},
            "motorista": {"id_motorista": id_motorista},
            "origem": origem,
            "destino": destino,
            "horario_pedido": gerar_horario()
        }

        url = f"{API_URL}/corridas/solicitar"
        async with session.post(url, json=corrida, timeout=TIMEOUT) as response:
            if response.status != 201:
                print(
                    f"❌ Falha ao solicitar corrida (cliente {id_cliente}): {response.status} - {await response.text()}")
            return response.status == 201


# Executa um conjunto de solicitações de corrida em paralelo.
async def executar_solicitacoes_corrida(num_corridas: int):
    print("\n🚕 Iniciando solicitações de corridas...")
    inicio = time.time()

    async with aiohttp.ClientSession() as session:
        clientes = await obter_clientes(session)
        if not clientes:
            print("⚠️ Nenhum cliente disponível. Abortando...")
            return 0

        total = 0
        tentativas = 0
        MAX_TENTATIVAS = num_corridas * 10

        while total < num_corridas and tentativas < MAX_TENTATIVAS:
            pendentes = num_corridas - total
            tarefas = [solicitar_corrida(session, random.choice(clientes)["id"]) for _ in range(pendentes)]
            resultados = await asyncio.gather(*tarefas)
            total += sum(resultados)
            tentativas += pendentes

        fim = time.time() - inicio
        minutos, segundos = divmod(fim, 60)

        print("\n✅ Resumo das solicitações:")
        print(f"✔️ {total}/{num_corridas} corridas solicitadas com sucesso.")
        print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")
        return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simular solicitações de corridas")
    parser.add_argument("--corridas", type=int, default=1, help="Número de corridas a serem solicitadas")
    args = parser.parse_args()

    asyncio.run(executar_solicitacoes_corrida(args.corridas))
