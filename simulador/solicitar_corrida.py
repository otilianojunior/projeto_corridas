import asyncio
import random
import time
import urllib.parse
from datetime import datetime, timedelta

import aiohttp

# 🔥 Configuração da API
API_URL = "http://127.0.0.1:8000"
NUM_CORRIDAS = 10
CITY = "Vitória da Conquista"
TIMEOUT = 120
MAX_CONCURRENT_REQUESTS = 5

# 🔄 Semáforo para controle de concorrência
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def obter_motoristas(session):
    """Obtém a lista de motoristas disponíveis na API."""
    url = f"{API_URL}/motoristas/listar/"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            motoristas = await response.json()
            return motoristas  # Retorna a lista de motoristas
        else:
            print(f"⚠️ Erro ao buscar motoristas: {response.status} - {await response.text()}")
            return []  # Retorna uma lista vazia caso a requisição falhe


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
    """Gera um horário aleatório para o dia 2024-06-01 com possibilidade de cair nos horários de pico."""
    base_date = datetime(2024, 6, 1)

    # Definir os intervalos de pico (7:00-8:00, 12:00-13:00, 17:30-18:30)
    intervalos_pico = [
        {"inicio": "07:00:00", "fim": "08:00:00"},
        {"inicio": "12:00:00", "fim": "13:00:00"},
        {"inicio": "17:30:00", "fim": "18:30:00"}
    ]

    # Probabilidade de gerar um horário no intervalo de pico (exemplo: 50%)
    chance_pico = 0.15  # 15% de chance de cair no horário de pico

    # Decide aleatoriamente se o horário será dentro de um intervalo de pico
    if random.random() < chance_pico:
        # Escolher aleatoriamente um intervalo de pico
        intervalo_escolhido = random.choice(intervalos_pico)

        # Converter os horários de início e fim para objetos datetime
        inicio_intervalo = datetime.strptime(f"{base_date.date()} {intervalo_escolhido['inicio']}", "%Y-%m-%d %H:%M:%S")
        fim_intervalo = datetime.strptime(f"{base_date.date()} {intervalo_escolhido['fim']}", "%Y-%m-%d %H:%M:%S")

        # Calcular a diferença entre o início e o fim do intervalo
        delta = fim_intervalo - inicio_intervalo

        # Gerar um horário aleatório dentro do intervalo de pico
        segundos_aleatorios = random.randint(0, int(delta.total_seconds()))
        horario_aleatorio = inicio_intervalo + timedelta(seconds=segundos_aleatorios)
    else:
        # Gerar horário aleatório durante o dia
        # Intervalo completo do dia (00:00:00 até 23:59:59)
        inicio_dia = datetime.strptime(f"{base_date.date()} 00:00:00", "%Y-%m-%d %H:%M:%S")
        fim_dia = datetime.strptime(f"{base_date.date()} 23:59:59", "%Y-%m-%d %H:%M:%S")

        delta = fim_dia - inicio_dia
        segundos_aleatorios = random.randint(0, int(delta.total_seconds()))
        horario_aleatorio = inicio_dia + timedelta(seconds=segundos_aleatorios)

    return horario_aleatorio.isoformat()


async def solicitar_corrida(session, id_cliente):
    """Solicita uma corrida para um cliente específico."""
    async with semaphore:  # 🔥 Controle de concorrência
        coordenadas = await obter_coordenadas_aleatorias(session)
        if not coordenadas:
            return False

        origem, destino = coordenadas.get("origem"), coordenadas.get("destino")
        if not origem or not destino:
            return False

        # Buscar motoristas disponíveis e escolher um aleatório
        motoristas = await obter_motoristas(session)
        if motoristas:
            motorista = random.choice(motoristas)
            id_motorista = motorista["id"]  # Atribui o id do motorista aleatório

            # Atualiza o status do motorista para "ocupado"
            motorista["status"] = "ocupado"  # Atualiza o status do motorista
        else:
            print(f"⚠️ Nenhum motorista disponível para o cliente {id_cliente}.")
            id_motorista = None  # Nenhum motorista disponível

        corrida_data = {
            "cliente": {"id_cliente": id_cliente},
            "motorista": {"id_motorista": id_motorista},
            "origem": origem,
            "destino": destino,
            "horario_pedido": gerar_horario_pedido()
        }

        url = f"{API_URL}/corridas/solicitar"
        async with session.post(url, json=corrida_data, timeout=TIMEOUT) as response:
            if response.status == 201:
                return True
            else:
                print(
                    f"❌ Erro ao solicitar corrida para cliente {id_cliente}: {response.status} - {await response.text()}")
                return False


async def processar_solicitacoes_corrida():
    """Executa a solicitacoes das corridas."""
    print("\n🚀 Iniciando solicitacoes de corridas...")

    start_time = time.time()  # ⏳ Medição do tempo total

    async with aiohttp.ClientSession() as session:
        clientes = await obter_clientes(session)
        if not clientes:
            print("⚠️ Nenhum cliente disponível. Solicitacao abortada.")
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
