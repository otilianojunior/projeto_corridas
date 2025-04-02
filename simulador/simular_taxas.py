import asyncio
import aiohttp
import random
import time
import argparse
from decimal import Decimal
from datetime import datetime

API_URL = "http://0.0.0.0:8000"
TIMEOUT = 120
MAX_CONCORRENTES = 5

semaforo = asyncio.Semaphore(MAX_CONCORRENTES)

def obter_taxas_por_nivel(nivel: int) -> dict:
    niveis = {
        1: {"taxa_manutencao": 1.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0},
        2: {"taxa_manutencao": 1.00, "taxa_limpeza": 2.00, "taxa_pico": 1.50, "taxa_noturna": 3.00, "taxa_excesso_corridas": 2.00},
        3: {"taxa_manutencao": 1.50, "taxa_limpeza": 5.00, "taxa_pico": 3.00, "taxa_noturna": 3.50, "taxa_excesso_corridas": 3.00},
        4: {"taxa_manutencao": 2.00, "taxa_limpeza": 7.00, "taxa_pico": 5.00, "taxa_noturna": 4.00, "taxa_excesso_corridas": 4.00},
        5: {"taxa_manutencao": 3.00, "taxa_limpeza": 10.00, "taxa_pico": 7.00, "taxa_noturna": 5.00, "taxa_excesso_corridas": 5.00},
        6: {"taxa_manutencao": 1.00, "taxa_cancelamento": 4.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0}
    }
    return niveis.get(nivel, niveis[3])

def horario_pico(horario: str) -> bool:
    try:
        data_hora = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        data_hora = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = data_hora.time()
    intervalos = [("07:00:00", "08:00:00"), ("12:00:00", "13:00:00"), ("17:30:00", "18:30:00")]
    return any(
        datetime.strptime(inicio, "%H:%M:%S").time() <= hora <= datetime.strptime(fim, "%H:%M:%S").time()
        for inicio, fim in intervalos
    )

def eh_horario_noturno(horario: str) -> bool:
    data_hora = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = data_hora.time()
    return hora >= datetime.strptime("22:00:00", "%H:%M:%S").time() or hora <= datetime.strptime("06:00:00", "%H:%M:%S").time()

def excesso_de_corridas(horario: str, corridas) -> bool:
    return sum(1 for corrida in corridas if corrida["horario_pedido"] == horario) > 10

async def listar_corridas_disponiveis(session):
    url = f"{API_URL}/corridas/listar_disponiveis"
    async with session.get(url, timeout=TIMEOUT) as resposta:
        if resposta.status == 200:
            dados = await resposta.json()
            return dados.get("corridas_disponiveis", [])
        return []

async def calcular_preco_por_km(distancia_km, consumo):
    preco_combustivel = Decimal("6")
    return (preco_combustivel / Decimal(str(consumo)) + Decimal("0.50")) * Decimal(str(distancia_km))

async def aplicar_taxas_corrida(session, corrida, todas_corridas):
    async with semaforo:
        id_corrida = corrida["id"]
        distancia = corrida["distancia_km"]
        horario_pedido = corrida["horario_pedido"]
        nivel_taxa = random.randint(1, 6)
        taxas = obter_taxas_por_nivel(nivel_taxa)

        combustivel = (corrida.get("combustivel") or "").lower()
        consumo = corrida.get("km_gasolina_cidade", 10) if combustivel in ["gasolina", "flex"] else corrida.get("km_etanol_cidade", 10)

        preco_por_km = await calcular_preco_por_km(distancia, consumo)

        # Monta o dicionário com as taxas aplicadas
        if nivel_taxa == 6:
            taxas_aplicadas = {
                "taxa_manutencao": taxas["taxa_manutencao"],
                "taxa_cancelamento": taxas.get("taxa_cancelamento", 0)
            }
            preco_total = Decimal(str(taxas_aplicadas["taxa_manutencao"])) + Decimal(str(taxas_aplicadas["taxa_cancelamento"]))
        else:
            # Taxas fixas sempre aplicadas
            taxas_aplicadas = {
                "taxa_manutencao": taxas["taxa_manutencao"],
                "taxa_limpeza": taxas["taxa_limpeza"]
            }
            preco_total = preco_por_km + Decimal(str(taxas_aplicadas["taxa_manutencao"])) + Decimal(str(taxas_aplicadas["taxa_limpeza"]))
            # Adiciona as taxas condicionais somente se as condições forem atendidas
            if horario_pico(horario_pedido):
                taxas_aplicadas["taxa_pico"] = taxas["taxa_pico"]
                preco_total += Decimal(str(taxas["taxa_pico"]))
            if eh_horario_noturno(horario_pedido):
                taxas_aplicadas["taxa_noturna"] = taxas["taxa_noturna"]
                preco_total += Decimal(str(taxas["taxa_noturna"]))
            if excesso_de_corridas(horario_pedido, todas_corridas):
                taxas_aplicadas["taxa_excesso_corridas"] = taxas["taxa_excesso_corridas"]
                preco_total += Decimal(str(taxas["taxa_excesso_corridas"]))

        valor_motorista = round((preco_total - Decimal(str(taxas_aplicadas["taxa_manutencao"]))) * Decimal("0.95"), 2)

        payload = {
            **taxas_aplicadas,
            "valor_motorista": float(valor_motorista),
            "preco_total": float(preco_total),
            "preco_km": float(preco_por_km),
            "nivel_taxa": nivel_taxa
        }
        url = f"{API_URL}/corridas/finalizar_corrida/{id_corrida}"
        async with session.put(url, json=payload, timeout=TIMEOUT) as resposta:
            status = resposta.status
            texto = await resposta.text()
            if status == 200:
                print(f"✅ Corrida {id_corrida} finalizada: R$ {preco_total:.2f} (Nível {nivel_taxa})")
                return True
            else:
                print(f"❌ Corrida {id_corrida} falhou: {status} - {texto}")
                return False

async def executar_simulacao_taxas(qtd_corridas: int):
    print("\n💸 Aplicando taxas nas corridas...")
    inicio = time.time()
    async with aiohttp.ClientSession() as session:
        corridas = await listar_corridas_disponiveis(session)
        if not corridas:
            print("⚠️ Nenhuma corrida disponível.")
            return

        qtd_alvo = min(qtd_corridas, len(corridas))
        amostra = random.sample(corridas, qtd_alvo)
        tarefas = [aplicar_taxas_corrida(session, corrida, corridas) for corrida in amostra]
        resultados = await asyncio.gather(*tarefas)

        tempo_total = time.time() - inicio
        minutos, segundos = divmod(tempo_total, 60)

        print("\n✅ Resumo da aplicação de taxas:")
        print(f"✔️ {sum(resultados)}/{qtd_alvo} corridas com taxas aplicadas.")
        print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")
        print("\n🏁 Finalizado!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplicar taxas em corridas disponíveis")
    parser.add_argument("--corridas", type=int, default=1, help="Quantidade de corridas a processar")
    argumentos = parser.parse_args()

    asyncio.run(executar_simulacao_taxas(argumentos.corridas))
