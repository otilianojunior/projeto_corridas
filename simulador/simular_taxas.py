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


# Aplica taxas contínuas dentro do intervalo de cada nível.
def obter_taxas_por_nivel_continuo(nivel: int) -> dict:
    niveis = {
        1: {"taxa_manutencao": (0.08, 0.12), "taxa_limpeza": (0.00, 0.05), "taxa_pico": (0.00, 0.05),
            "taxa_noturna": (0.00, 0.05), "taxa_excesso_corridas": (0.00, 0.05)},
        2: {"taxa_manutencao": (0.09, 0.12), "taxa_limpeza": (0.15, 0.25), "taxa_pico": (0.12, 0.18),
            "taxa_noturna": (0.28, 0.32), "taxa_excesso_corridas": (0.18, 0.22)},
        3: {"taxa_manutencao": (0.13, 0.17), "taxa_limpeza": (0.45, 0.55), "taxa_pico": (0.28, 0.32),
            "taxa_noturna": (0.33, 0.37), "taxa_excesso_corridas": (0.28, 0.32)},
        4: {"taxa_manutencao": (0.18, 0.22), "taxa_limpeza": (0.65, 0.75), "taxa_pico": (0.48, 0.52),
            "taxa_noturna": (0.38, 0.42), "taxa_excesso_corridas": (0.38, 0.42)},
        5: {"taxa_manutencao": (0.28, 0.32), "taxa_limpeza": (0.95, 1.05), "taxa_pico": (0.68, 0.72),
            "taxa_noturna": (0.48, 0.52), "taxa_excesso_corridas": (0.48, 0.52)},
        6: {"taxa_manutencao": (0.95, 1.05), "taxa_cancelamento": (3.8, 4.2)}
    }

    nivel_config = niveis.get(nivel, niveis[6])

    # Para cada taxa, sorteia um valor dentro do intervalo (mínimo, máximo)
    return {
        chave: round(random.uniform(valor[0], valor[1]), 4) if isinstance(valor, tuple) else valor
        for chave, valor in nivel_config.items()
    }


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
        taxas = obter_taxas_por_nivel_continuo(nivel_taxa)
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

            # Aplicação da nova lógica da taxa de manutenção como valor fixo por km
            taxa_manutencao_fixa = Decimal(str(taxas["taxa_manutencao"]))

            taxas_aplicadas = {
                "taxa_manutencao": taxa_manutencao_fixa,
                "taxa_limpeza": Decimal(str(taxas["taxa_limpeza"]))
            }

            if horario_pico(horario_pedido):
                taxas_aplicadas["taxa_pico"] = Decimal(str(taxas["taxa_pico"]))
            if eh_horario_noturno(horario_pedido):
                taxas_aplicadas["taxa_noturna"] = Decimal(str(taxas["taxa_noturna"]))
            if excesso_de_corridas(horario_pedido, todas_corridas):
                taxas_aplicadas["taxa_excesso_corridas"] = Decimal(str(taxas["taxa_excesso_corridas"]))

            # Soma apenas das taxas percentuais (limpeza, pico, noturna, excesso)
            taxas_percentuais = sum([
                taxas_aplicadas.get("taxa_limpeza", Decimal(0)),
                taxas_aplicadas.get("taxa_pico", Decimal(0)),
                taxas_aplicadas.get("taxa_noturna", Decimal(0)),
                taxas_aplicadas.get("taxa_excesso_corridas", Decimal(0))
            ])

            # Cálculo do preço por km:
            preco_por_km = tarifa_base * (1 + taxas_percentuais) + taxa_manutencao_fixa

            # Preço total pela distância
            preco_total = preco_por_km * distancia

            # Valor do motorista (95% sobre o valor base menos a taxa de manutenção)
            valor_motorista = round(
                ((preco_por_km - taxa_manutencao_fixa) * distancia) * Decimal("0.95"), 2
            )

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
                return 1
            else:
                print(f"❌ Corrida {id_corrida} falhou: {status} - {texto}")
                return 0


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
        taxas_aplicadas = sum(resultados)

        tempo_total = time.time() - inicio
        minutos, segundos = divmod(tempo_total, 60)

        print("\n✅ Resumo da aplicação de taxas:")
        print(f"✔️ {sum(resultados)}/{qtd_alvo} corridas com taxas aplicadas.")
        print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")
        print("\n🏁 Finalizado!")
        return taxas_aplicadas




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplicar taxas em corridas disponíveis")
    parser.add_argument("--corridas", type=int, default=1, help="Quantidade de corridas a processar")
    argumentos = parser.parse_args()

    asyncio.run(executar_simulacao_taxas(argumentos.corridas))
