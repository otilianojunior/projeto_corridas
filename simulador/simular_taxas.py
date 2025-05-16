import argparse
import asyncio
import random
import time
from datetime import datetime
from decimal import Decimal

import aiohttp

API_URL = "http://0.0.0.0:8000"
TIMEOUT = 120
MAX_CONCORRENTES = 5

semaforo = asyncio.Semaphore(MAX_CONCORRENTES)


# Simula aplicação de taxas em corridas, considerando condições como horário de pico.
def obter_taxas_por_nivel(nivel: int) -> dict:
    niveis = {
        1: {"taxa_manutencao": 0.10, "taxa_limpeza": 0.00, "taxa_pico": 0.00, "taxa_noturna": 0.00,
            "taxa_excesso_corridas": 0.00},
        2: {"taxa_manutencao": 0.10, "taxa_limpeza": 0.20, "taxa_pico": 0.15, "taxa_noturna": 0.30,
            "taxa_excesso_corridas": 0.20},
        3: {"taxa_manutencao": 0.15, "taxa_limpeza": 0.50, "taxa_pico": 0.30, "taxa_noturna": 0.35,
            "taxa_excesso_corridas": 0.30},
        4: {"taxa_manutencao": 0.20, "taxa_limpeza": 0.70, "taxa_pico": 0.50, "taxa_noturna": 0.40,
            "taxa_excesso_corridas": 0.40},
        5: {"taxa_manutencao": 0.30, "taxa_limpeza": 1.00, "taxa_pico": 0.70, "taxa_noturna": 0.50,
            "taxa_excesso_corridas": 0.50},
        6: {"taxa_manutencao": 1.00, "taxa_cancelamento": 4.00, "taxa_limpeza": 0.00, "taxa_pico": 0.00,
            "taxa_noturna": 0.00, "taxa_excesso_corridas": 0.00}
    }
    return niveis.get(nivel, niveis[3])


# Define lógica para horários de pico.
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


# Avalia se o horário está no período noturno.
def eh_horario_noturno(horario: str) -> bool:
    data_hora = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = data_hora.time()
    return hora >= datetime.strptime("22:00:00", "%H:%M:%S").time() or hora <= datetime.strptime("06:00:00",
                                                                                                 "%H:%M:%S").time()


# Verifica se há excesso de corridas no horário informado.
def excesso_de_corridas(horario: str, corridas) -> bool:
    return sum(1 for corrida in corridas if corrida["horario_pedido"] == horario) > 10


# Lista corridas disponíveis através da API.
async def listar_corridas_disponiveis(session):
    url = f"{API_URL}/corridas/listar_disponiveis"
    async with session.get(url, timeout=TIMEOUT) as resposta:
        if resposta.status == 200:
            dados = await resposta.json()
            return dados.get("corridas_disponiveis", [])
        return []


# Calcula tarifa base por quilômetro considerando consumo.
async def calcular_tarifa_base_por_km(consumo) -> Decimal:
    preco_combustivel = Decimal("6")
    return preco_combustivel / Decimal(str(consumo)) + Decimal("0.50")


# Aplica taxas a uma corrida seguindo regras específicas.
async def aplicar_taxas_corrida(session, corrida, todas_corridas):
    async with semaforo:
        id_corrida = corrida["id"]
        distancia = Decimal(str(corrida["distancia_km"]))
        horario_pedido = corrida["horario_pedido"]
        nivel_taxa = random.randint(1, 6)
        taxas = obter_taxas_por_nivel(nivel_taxa)
        combustivel = (corrida.get("combustivel") or "").lower()
        consumo = corrida.get("km_gasolina_cidade", 10) if combustivel in ["gasolina", "flex"] else corrida.get(
            "km_etanol_cidade", 10)

        if nivel_taxa == 6:
            taxas_aplicadas = {
                "taxa_manutencao": Decimal(str(taxas["taxa_manutencao"])),
                "taxa_cancelamento": Decimal(str(taxas.get("taxa_cancelamento", 0)))
            }
            preco_total = taxas_aplicadas["taxa_manutencao"] + taxas_aplicadas["taxa_cancelamento"]
            valor_motorista = round((preco_total - taxas_aplicadas["taxa_manutencao"]) * Decimal("0.95"), 2)
            preco_por_km = preco_total
        else:
            tarifa_base = await calcular_tarifa_base_por_km(consumo)
            taxas_aplicadas = {
                "taxa_manutencao": Decimal(str(taxas["taxa_manutencao"])),
                "taxa_limpeza": Decimal(str(taxas["taxa_limpeza"]))
            }
            if horario_pico(horario_pedido):
                taxas_aplicadas["taxa_pico"] = Decimal(str(taxas["taxa_pico"]))
            if eh_horario_noturno(horario_pedido):
                taxas_aplicadas["taxa_noturna"] = Decimal(str(taxas["taxa_noturna"]))
            if excesso_de_corridas(horario_pedido, todas_corridas):
                taxas_aplicadas["taxa_excesso_corridas"] = Decimal(str(taxas["taxa_excesso_corridas"]))

            soma_percentual = sum(taxas_aplicadas.values())
            preco_por_km = tarifa_base * (1 + soma_percentual)
            preco_total = preco_por_km * distancia
            valor_motorista = round(
                ((preco_por_km - (tarifa_base * taxas_aplicadas["taxa_manutencao"])) * distancia) * Decimal("0.95"), 2)

        payload = {
            **{k: float(v) for k, v in taxas_aplicadas.items()},
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


# Executa a simulação da aplicação de taxas.
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
