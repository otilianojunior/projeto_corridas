import asyncio
import aiohttp
import random
import time
from decimal import Decimal
from datetime import datetime

# 🔥 Configuração da API
API_URL = "http://0.0.0.0:8000"
TIMEOUT = 120  # Tempo limite para requisições
MAX_CONCURRENT_REQUESTS = 5  # 🔄 Limite de requisições simultâneas
NUM_CORRIDAS_PROCESSAR = 10  # 🔥 Defina quantas corridas deseja processar

# 🔄 Semáforo para controle de concorrência
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def gerar_taxas_por_nivel(nivel):
    """Retorna as taxas conforme o nível escolhido, incluindo a taxa de cancelamento para o nível 6."""
    niveis_taxas = {
        1: {"taxa_manutencao": 1.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0},
        2: {"taxa_manutencao": 1.00, "taxa_limpeza": 2.00, "taxa_pico": 1.50, "taxa_noturna": 3.00, "taxa_excesso_corridas": 2.00},
        3: {"taxa_manutencao": 1.50, "taxa_limpeza": 5.00, "taxa_pico": 3.00, "taxa_noturna": 3.50, "taxa_excesso_corridas": 3.00},
        4: {"taxa_manutencao": 2.00, "taxa_limpeza": 7.00, "taxa_pico": 5.00, "taxa_noturna": 4.00, "taxa_excesso_corridas": 4.00},
        5: {"taxa_manutencao": 3.00, "taxa_limpeza": 10.00, "taxa_pico": 7.00, "taxa_noturna": 5.00, "taxa_excesso_corridas": 5.00},
        6: {"taxa_manutencao": 1.00, "taxa_cancelamento": 4.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0}
    }
    return niveis_taxas.get(nivel, niveis_taxas[3])  # Padrão: nível 3

# Função para verificar se o horário está dentro dos horários de pico
def is_horario_pico(horario_pedido):
    """Verifica se o horário da corrida está dentro do intervalo de pico"""
    pico_1_inicio = "07:00:00"
    pico_1_fim = "08:00:00"
    pico_2_inicio = "12:00:00"
    pico_2_fim = "13:00:00"
    pico_3_inicio = "17:30:00"
    pico_3_fim = "18:30:00"

    # Tenta converter o horário de pedido para datetime com fuso horário
    try:
        horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S.%f%z")  # Tenta com fuso horário
    except ValueError:
        horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S")  # Se falhar, tenta sem fuso horário

    # Extraímos apenas a hora e o minuto
    hora_corrida = horario_pedido.time()

    # Converte os horários de pico para time
    pico_1_inicio = datetime.strptime(pico_1_inicio, "%H:%M:%S").time()
    pico_1_fim = datetime.strptime(pico_1_fim, "%H:%M:%S").time()
    pico_2_inicio = datetime.strptime(pico_2_inicio, "%H:%M:%S").time()
    pico_2_fim = datetime.strptime(pico_2_fim, "%H:%M:%S").time()
    pico_3_inicio = datetime.strptime(pico_3_inicio, "%H:%M:%S").time()
    pico_3_fim = datetime.strptime(pico_3_fim, "%H:%M:%S").time()

    # Verifica se o horário da corrida está dentro de algum intervalo de pico
    if (pico_1_inicio <= hora_corrida <= pico_1_fim) or (pico_2_inicio <= hora_corrida <= pico_2_fim) or (pico_3_inicio <= hora_corrida <= pico_3_fim):
        return True
    return False

# Função para verificar se o horário está no período noturno
def is_horario_noturno(horario_pedido):
    """Verifica se a corrida ocorre entre 22:00 e 06:00 (horário noturno)"""
    horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S")  # Sem fuso horário
    hora_corrida = horario_pedido.time()

    noturno_inicio = datetime.strptime("22:00:00", "%H:%M:%S").time()
    noturno_fim = datetime.strptime("06:00:00", "%H:%M:%S").time()

    # Se o horário da corrida estiver entre 22:00 e 06:00, aplica a taxa noturna
    if noturno_inicio <= hora_corrida or hora_corrida <= noturno_fim:
        return True
    return False


# Função para verificar excesso de corridas no mesmo horário
def verificar_excesso_corridas(horario_pedido, corridas_disponiveis):
    """Verifica se há excesso de corridas no mesmo horário (ex: mais de 3 corridas no mesmo horário)."""
    limite_corridas = 10  # Defina o limite de corridas por horário
    contagem = sum(1 for corrida in corridas_disponiveis if corrida["horario_pedido"] == horario_pedido)
    return contagem > limite_corridas  # Se houver mais corridas no mesmo horário, aplica a taxa


async def obter_corridas_disponiveis(session):
    """Obtém a lista de corridas disponíveis na API."""
    url = f"{API_URL}/corridas/disponiveis"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            corridas = await response.json()
            return corridas.get("corridas_disponiveis", [])
        else:
            print(f"⚠️ Erro ao buscar corridas disponíveis: {response.status} - {await response.text()}")
            return []


async def calcular_preco_km(distancia_km):
    """Calcula o preço baseado na distância percorrida em quilômetros."""
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal("10")  # km/litro
    margem_lucro = Decimal("0.50")  # R$/km

    distancia_km = Decimal(str(distancia_km))

    return await asyncio.to_thread(
        lambda: ((preco_combustivel / consumo_veiculo) + margem_lucro) * distancia_km
    )


async def aplicar_taxas_corrida(session, corrida, corridas_disponiveis):
    """Envia os valores calculados de taxas para a API com base no nível."""
    async with semaphore:
        corrida_id = corrida["id"]
        distancia_km = corrida["distancia_km"]
        horario_pedido = corrida["horario_pedido"]

        nivel_taxa = random.randint(1, 6)  # 🔥 Sorteia um nível aleatório (1 a 6)
        taxas = gerar_taxas_por_nivel(nivel_taxa)  # Obtém as taxas com base no nível

        # Calcular o preço por km
        preco_km = await calcular_preco_km(distancia_km)

        # Adiciona a taxa de pico se for horário de pico (somente se for parte do nível)
        if is_horario_pico(horario_pedido):
            preco_km += Decimal(str(taxas["taxa_pico"]))  # Convertendo para Decimal

        # Adiciona a taxa noturna se for horário noturno (somente se for parte do nível)
        if is_horario_noturno(horario_pedido):
            preco_km += Decimal(str(taxas["taxa_noturna"]))  # Convertendo para Decimal

        # Verifica se há excesso de corridas no mesmo horário e aplica a taxa de excesso de corridas
        if verificar_excesso_corridas(horario_pedido, corridas_disponiveis):
            preco_km += Decimal(str(taxas["taxa_excesso_corridas"]))  # Convertendo para Decimal

        # Verifica se o nível é 6, aplica apenas taxa_manutencao e taxa_cancelamento
        if nivel_taxa == 6:
            total_taxas = Decimal(str(taxas["taxa_manutencao"])) + Decimal(str(taxas.get("taxa_cancelamento", 0)))  # Usando .get() para evitar KeyError
            preco_total = total_taxas  # No nível 6, o preco_total será igual a total_taxas
        else:
            # 🔹 Calcula o total das taxas aplicadas para outros níveis
            total_taxas = sum(Decimal(str(value)) for value in taxas.values())  # Convertendo para Decimal
            preco_total = preco_km + total_taxas  # No nível 1-5, o preco_total inclui preco_km

        # 🔹 Calcula o valor do motorista:
        # 1️⃣ Primeiro, desconta a taxa de manutenção do app do total
        montante_restante = (preco_total - Decimal(str(taxas["taxa_manutencao"])))

        # 2️⃣ Aplica a taxa da plataforma (5%) no valor restante
        valor_motorista = round(montante_restante * Decimal("0.95"), 2)

        # 🔹 Prepara os dados para envio, com as taxas diretamente de `taxas`
        payload = {
            **taxas,
            "valor_motorista": float(valor_motorista),  # Convertendo para float
            "preco_total": float(preco_total),  # Convertendo para float
            "preco_km": float(preco_km),  # Adicionando preco_km ao payload
            "nivel_taxa": nivel_taxa
        }

        # 🔹 Envia os dados para a API
        url = f"{API_URL}/corridas/finalizar_corrida/{corrida_id}"
        async with session.put(url, json=payload, timeout=TIMEOUT) as response:
            if response.status == 200:
                print(f"✅ Corrida {corrida_id} finalizada: R$ {preco_total:.2f} (Nível {nivel_taxa})")
                return True
            else:
                print(f"❌ Erro ao finalizar corrida {corrida_id}: {response.status} - {await response.text()}")
                return False


async def processar_taxas_corridas():
    """Executa a aplicação de taxas nas corridas disponíveis."""
    print("\n🚀 Iniciando aplicação de taxas nas corridas...")

    start_time = time.time()  # ⏳ Medição do tempo total

    async with aiohttp.ClientSession() as session:
        corridas_disponiveis = await obter_corridas_disponiveis(session)

        if not corridas_disponiveis:
            print("⚠️ Nenhuma corrida disponível para aplicar taxas. Encerrando.")
            return

        # 🔥 Pega apenas a quantidade desejada, mas nunca mais do que o total disponível
        num_corridas_a_processar = min(NUM_CORRIDAS_PROCESSAR, len(corridas_disponiveis))
        corridas_selecionadas = random.sample(corridas_disponiveis, num_corridas_a_processar)

        # Processa todas as corridas em paralelo
        tarefas = [aplicar_taxas_corrida(session, corrida, corridas_disponiveis) for corrida in corridas_selecionadas]
        resultados = await asyncio.gather(*tarefas)

        total_sucessos = sum(resultados)

    elapsed_time = time.time() - start_time  # ⏳ Tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    print("\n✅ Resumo das Taxas Aplicadas:")
    print(f"✔️ {total_sucessos}/{num_corridas_a_processar} corridas processadas com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")

    print("\n🏁 Processamento concluído!")


if __name__ == "__main__":
    asyncio.run(processar_taxas_corridas())
