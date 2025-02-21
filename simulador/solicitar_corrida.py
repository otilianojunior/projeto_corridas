import asyncio
import aiohttp
import random
import urllib.parse
import time
from datetime import datetime, timedelta

# 🔥 Configuração da API
API_URL = "http://127.0.0.1:8000"
NUM_CORRIDAS = 2000  # Número total de corridas
CITY = "Vitória da Conquista"
TIMEOUT = 120  # Timeout para requisições
MAX_CONCURRENT_REQUESTS = 5  # 🔄 Limite de requisições simultâneas

# 🔄 Semáforo para controle de concorrência
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def obter_clientes(session):
    """Obtém a lista de clientes disponíveis na API."""
    url = f"{API_URL}/clientes/listar_sem_corrida/"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            clientes = await response.json()
            if isinstance(clientes, dict) and clientes.get("mensagem"):
                return []
            return clientes
        else:
            print(f"⚠️ Erro ao buscar clientes: {response.status} - {await response.text()}")
            return []


async def obter_coordenadas_aleatorias(session):
    """Obtém coordenadas aleatórias de origem e destino da API."""
    url = f"{API_URL}/mapas/selecionar_coordenadas_aleatorias?cidade={urllib.parse.quote(CITY)}"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"⚠️ Erro ao buscar coordenadas: {response.status} - {await response.text()}")
            return None


def gerar_horario_pedido():
    """Gera um horário aleatório para o dia 2024-06-01."""
    base_date = datetime(2024, 6, 1)
    return (base_date + timedelta(seconds=random.randint(0, 86399))).isoformat()


async def solicitar_corrida(session, id_cliente):
    """Solicita uma corrida para um cliente específico."""
    async with semaphore:  # 🔥 Controle de concorrência
        coordenadas = await obter_coordenadas_aleatorias(session)
        if not coordenadas:
            return False

        origem, destino = coordenadas.get("origem"), coordenadas.get("destino")
        if not origem or not destino:
            return False

        corrida_data = {
            "cliente": {"id_cliente": id_cliente},
            "origem": origem,
            "destino": destino,
            "horario_pedido": gerar_horario_pedido()
        }

        url = f"{API_URL}/corridas/solicitar"
        async with session.post(url, json=corrida_data, timeout=TIMEOUT) as response:
            if response.status == 201:
                return True
            else:
                print(f"❌ Erro ao solicitar corrida para cliente {id_cliente}: {response.status} - {await response.text()}")
                return False


async def processar_solicitacoes_corrida():
    """Executa a simulação das corridas."""
    print("\n🚀 Iniciando simulação de corridas...")

    start_time = time.time()  # ⏳ Medição do tempo total

    async with aiohttp.ClientSession() as session:
        clientes = await obter_clientes(session)
        if not clientes:
            print("⚠️ Nenhum cliente disponível. Simulação abortada.")
            return

        # Seleciona clientes aleatoriamente
        clientes_selecionados = random.sample(clientes, min(NUM_CORRIDAS, len(clientes)))

        # Processa todas as corridas em paralelo
        tarefas = [solicitar_corrida(session, cliente["id"]) for cliente in clientes_selecionados]
        resultados = await asyncio.gather(*tarefas)

        total_sucessos = sum(resultados)

    elapsed_time = time.time() - start_time  # ⏳ Tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    print("\n✅ Resumo da Simulação:")
    print(f"✔️ {total_sucessos}/{NUM_CORRIDAS} corridas solicitadas com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")

    print("\n🏁 Simulação concluída!")


if __name__ == "__main__":
    asyncio.run(processar_solicitacoes_corrida())
