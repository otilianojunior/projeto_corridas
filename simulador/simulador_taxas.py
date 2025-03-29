import asyncio
import aiohttp
import random
import time
from decimal import Decimal
from datetime import datetime, timedelta

# 🔥 Configuração da API
API_URL = "http://0.0.0.0:8000"
TIMEOUT = 120  # Tempo limite para requisições
MAX_CONCURRENT_REQUESTS = 5  # Limite de requisições simultâneas
NUM_CORRIDAS_PROCESSAR = 10  # Quantas corridas deseja processar

# Semáforo para controle de concorrência
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

def is_horario_pico(horario_pedido):
    """Verifica se o horário da corrida está dentro do intervalo de pico"""
    pico_1_inicio = "07:00:00"
    pico_1_fim = "08:00:00"
    pico_2_inicio = "12:00:00"
    pico_2_fim = "13:00:00"
    pico_3_inicio = "17:30:00"
    pico_3_fim = "18:30:00"
    try:
        horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S")
    hora_corrida = horario_pedido.time()
    pico_1_inicio = datetime.strptime(pico_1_inicio, "%H:%M:%S").time()
    pico_1_fim = datetime.strptime(pico_1_fim, "%H:%M:%S").time()
    pico_2_inicio = datetime.strptime(pico_2_inicio, "%H:%M:%S").time()
    pico_2_fim = datetime.strptime(pico_2_fim, "%H:%M:%S").time()
    pico_3_inicio = datetime.strptime(pico_3_inicio, "%H:%M:%S").time()
    pico_3_fim = datetime.strptime(pico_3_fim, "%H:%M:%S").time()
    return (pico_1_inicio <= hora_corrida <= pico_1_fim) or (pico_2_inicio <= hora_corrida <= pico_2_fim) or (pico_3_inicio <= hora_corrida <= pico_3_fim)

def is_horario_noturno(horario_pedido):
    """Verifica se a corrida ocorre entre 22:00 e 06:00 (horário noturno)"""
    horario_pedido = datetime.strptime(horario_pedido, "%Y-%m-%dT%H:%M:%S")
    hora_corrida = horario_pedido.time()
    noturno_inicio = datetime.strptime("22:00:00", "%H:%M:%S").time()
    noturno_fim = datetime.strptime("06:00:00", "%H:%M:%S").time()
    return noturno_inicio <= hora_corrida or hora_corrida <= noturno_fim

def verificar_excesso_corridas(horario_pedido, corridas_disponiveis):
    """Verifica se há excesso de corridas no mesmo horário."""
    limite_corridas = 10
    contagem = sum(1 for corrida in corridas_disponiveis if corrida["horario_pedido"] == horario_pedido)
    return contagem > limite_corridas

async def obter_corridas_disponiveis(session):
    """Obtém a lista de corridas disponíveis na API."""
    # Atualizado a rota para lista_disponiveis
    url = f"{API_URL}/corridas/listar_disponiveis"
    async with session.get(url, timeout=TIMEOUT) as response:
        if response.status == 200:
            corridas = await response.json()
            return corridas.get("corridas_disponiveis", [])
        else:
            print(f"⚠️ Erro ao buscar corridas disponíveis: {response.status} - {await response.text()}")
            return []

async def calcular_preco_km(distancia_km, consumo):
    """Calcula o preço baseado na distância e consumo (km/l)."""
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal(str(consumo))
    margem_lucro = Decimal("0.50")  # R$/km
    return (preco_combustivel / consumo_veiculo + margem_lucro) * Decimal(str(distancia_km))

async def aplicar_taxas_corrida(session, corrida, corridas_disponiveis):
    async with semaphore:
        corrida_id = corrida["id"]
        distancia_km = corrida["distancia_km"]
        horario_pedido = corrida["horario_pedido"]

        nivel_taxa = random.randint(1, 6)
        taxas = gerar_taxas_por_nivel(nivel_taxa)

        # Selecionar o consumo de acordo com o combustível, garantindo valor padrão se não houver
        combustivel = (corrida.get("combustivel") or "").lower()
        if combustivel == "gasolina":
            consumo = corrida.get("km_gasolina_cidade", 10)
        elif combustivel == "flex":
            consumo = corrida.get("km_gasolina_cidade", 10)
        elif combustivel == "etanol":
            consumo = corrida.get("km_etanol_cidade", 10)
        else:
            consumo = 10

        preco_km = await calcular_preco_km(distancia_km, consumo)

        if is_horario_pico(horario_pedido):
            preco_km += Decimal(str(taxas["taxa_pico"]))
        if is_horario_noturno(horario_pedido):
            preco_km += Decimal(str(taxas["taxa_noturna"]))
        if verificar_excesso_corridas(horario_pedido, corridas_disponiveis):
            preco_km += Decimal(str(taxas["taxa_excesso_corridas"]))

        if nivel_taxa == 6:
            total_taxas = Decimal(str(taxas["taxa_manutencao"])) + Decimal(str(taxas.get("taxa_cancelamento", 0)))
            preco_total = total_taxas
        else:
            total_taxas = sum(Decimal(str(value)) for value in taxas.values())
            preco_total = preco_km + total_taxas

        montante_restante = (preco_total - Decimal(str(taxas["taxa_manutencao"])))
        valor_motorista = round(montante_restante * Decimal("0.95"), 2)

        payload = {
            **taxas,
            "valor_motorista": float(valor_motorista),
            "preco_total": float(preco_total),
            "preco_km": float(preco_km),
            "nivel_taxa": nivel_taxa
        }

        url = f"{API_URL}/corridas/finalizar_corrida/{corrida_id}"
        async with session.put(url, json=payload, timeout=TIMEOUT) as response:
            if response.status == 200:
                print(f"✅ Corrida {corrida_id} finalizada: R$ {preco_total:.2f} (Nível {nivel_taxa})")
                return True
            else:
                print(f"❌ Erro ao finalizar corrida {corrida_id}: {response.status} - {await response.text()}")
                return False

async def processar_taxas_corridas():
    print("\n🚀 Iniciando aplicação de taxas nas corridas...")
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        corridas_disponiveis = await obter_corridas_disponiveis(session)
        if not corridas_disponiveis:
            print("⚠️ Nenhuma corrida disponível para aplicar taxas. Encerrando.")
            return

        num_corridas_a_processar = min(NUM_CORRIDAS_PROCESSAR, len(corridas_disponiveis))
        corridas_selecionadas = random.sample(corridas_disponiveis, num_corridas_a_processar)
        tarefas = [aplicar_taxas_corrida(session, corrida, corridas_disponiveis) for corrida in corridas_selecionadas]
        resultados = await asyncio.gather(*tarefas)
        total_sucessos = sum(resultados)

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)

    print("\n✅ Resumo das Taxas Aplicadas:")
    print(f"✔️ {total_sucessos}/{num_corridas_a_processar} corridas processadas com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")
    print("\n🏁 Processamento concluído!")

if __name__ == "__main__":
    asyncio.run(processar_taxas_corridas())
