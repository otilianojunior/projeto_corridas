import asyncio
import aiohttp
import random
import time

# 🔥 Configuração da API
API_URL = "http://127.0.0.1:8000"
TIMEOUT = 120  # Tempo limite para requisições
MAX_CONCURRENT_REQUESTS = 5  # 🔄 Limite de requisições simultâneas
NUM_CORRIDAS_PROCESSAR = 10  # 🔥 Defina quantas corridas deseja processar

# 🔄 Semáforo para controle de concorrência
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


def gerar_taxas_por_nivel(nivel):
    """Retorna as taxas conforme o nível escolhido."""
    niveis_taxas = {
        1: {"taxa_noturna": 0, "taxa_manutencao": 0, "taxa_pico": 0, "taxa_excesso_corridas": 0, "taxa_limpeza": 0, "taxa_cancelamento": 0},
        2: {"taxa_noturna": 1.00, "taxa_manutencao": 1.00, "taxa_pico": 1.50, "taxa_excesso_corridas": 0.50, "taxa_limpeza": 2.00, "taxa_cancelamento": 3.00},
        3: {"taxa_noturna": 2.00, "taxa_manutencao": 1.50, "taxa_pico": 3.00, "taxa_excesso_corridas": 1.00, "taxa_limpeza": 5.00, "taxa_cancelamento": 4.00},
        4: {"taxa_noturna": 3.50, "taxa_manutencao": 2.00, "taxa_pico": 5.00, "taxa_excesso_corridas": 1.50, "taxa_limpeza": 7.00, "taxa_cancelamento": 6.00},
        5: {"taxa_noturna": 5.00, "taxa_manutencao": 3.00, "taxa_pico": 7.00, "taxa_excesso_corridas": 2.00, "taxa_limpeza": 10.00, "taxa_cancelamento": 8.00},
    }
    return niveis_taxas.get(nivel, niveis_taxas[3])  # Padrão: nível 3


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


async def aplicar_taxas_corrida(session, corrida):
    """Envia os valores calculados de taxas para a API com base no nível."""
    async with semaphore:
        corrida_id = corrida["id"]
        nivel_taxa = random.randint(1, 5)  # 🔥 Sorteia um nível aleatório (1 a 5)

        taxas = gerar_taxas_por_nivel(nivel_taxa)
        preco_km = round(random.uniform(1.5, 3.5), 2)
        valor_motorista = round(preco_km * corrida["distancia_km"] * 0.75, 2)
        preco_total = round(corrida["preco_parcial"] + sum(taxas.values()), 2)

        payload = {
            **taxas,
            "preco_km": preco_km,
            "valor_motorista": valor_motorista,
            "preco_total": preco_total,
            "nivel_taxa": nivel_taxa,  # 🚀 Adiciona nível da taxa
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
        tarefas = [aplicar_taxas_corrida(session, corrida) for corrida in corridas_selecionadas]
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
