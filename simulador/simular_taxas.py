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

def gerar_taxas_por_nivel(nivel: int) -> dict:
    niveis = {
        1: {"taxa_manutencao": 1.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0},
        2: {"taxa_manutencao": 1.00, "taxa_limpeza": 2.00, "taxa_pico": 1.50, "taxa_noturna": 3.00, "taxa_excesso_corridas": 2.00},
        3: {"taxa_manutencao": 1.50, "taxa_limpeza": 5.00, "taxa_pico": 3.00, "taxa_noturna": 3.50, "taxa_excesso_corridas": 3.00},
        4: {"taxa_manutencao": 2.00, "taxa_limpeza": 7.00, "taxa_pico": 5.00, "taxa_noturna": 4.00, "taxa_excesso_corridas": 4.00},
        5: {"taxa_manutencao": 3.00, "taxa_limpeza": 10.00, "taxa_pico": 7.00, "taxa_noturna": 5.00, "taxa_excesso_corridas": 5.00},
        6: {"taxa_manutencao": 1.00, "taxa_cancelamento": 4.00, "taxa_limpeza": 0, "taxa_pico": 0, "taxa_noturna": 0, "taxa_excesso_corridas": 0}
    }
    return niveis.get(nivel, niveis[3])

def is_horario_pico(horario: str) -> bool:
    try:
        horario_dt = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        horario_dt = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = horario_dt.time()
    intervalos = [("07:00:00", "08:00:00"), ("12:00:00", "13:00:00"), ("17:30:00", "18:30:00")]
    return any(datetime.strptime(i, "%H:%M:%S").time() <= hora <= datetime.strptime(f, "%H:%M:%S").time() for i, f in intervalos)

def is_horario_noturno(horario: str) -> bool:
    horario_dt = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = horario_dt.time()
    return hora >= datetime.strptime("22:00:00", "%H:%M:%S").time() or hora <= datetime.strptime("06:00:00", "%H:%M:%S").time()

def verificar_excesso_corridas(horario, corridas) -> bool:
    return sum(1 for c in corridas if c["horario_pedido"] == horario) > 10

async def obter_corridas(session):
    url = f"{API_URL}/corridas/listar_disponiveis"
    async with session.get(url, timeout=TIMEOUT) as r:
        return (await r.json()).get("corridas_disponiveis", []) if r.status == 200 else []

async def calcular_preco_km(distancia_km, consumo):
    preco_comb = Decimal("6")
    return (preco_comb / Decimal(str(consumo)) + Decimal("0.50")) * Decimal(str(distancia_km))

async def aplicar_taxas(session, corrida, corridas):
    async with semaforo:
        id_ = corrida["id"]
        dist = corrida["distancia_km"]
        horario = corrida["horario_pedido"]
        nivel = random.randint(1, 6)
        taxas = gerar_taxas_por_nivel(nivel)

        comb = (corrida.get("combustivel") or "").lower()
        consumo = corrida.get("km_gasolina_cidade", 10) if comb in ["gasolina", "flex"] else corrida.get("km_etanol_cidade", 10)

        preco_km = await calcular_preco_km(dist, consumo)
        if is_horario_pico(horario): preco_km += Decimal(str(taxas["taxa_pico"]))
        if is_horario_noturno(horario): preco_km += Decimal(str(taxas["taxa_noturna"]))
        if verificar_excesso_corridas(horario, corridas): preco_km += Decimal(str(taxas["taxa_excesso_corridas"]))

        if nivel == 6:
            preco_total = Decimal(str(taxas["taxa_manutencao"])) + Decimal(str(taxas.get("taxa_cancelamento", 0)))
        else:
            preco_total = preco_km + sum(Decimal(str(v)) for v in taxas.values())

        valor_motorista = round((preco_total - Decimal(str(taxas["taxa_manutencao"]))) * Decimal("0.95"), 2)

        payload = {**taxas, "valor_motorista": float(valor_motorista), "preco_total": float(preco_total), "preco_km": float(preco_km), "nivel_taxa": nivel}
        url = f"{API_URL}/corridas/finalizar_corrida/{id_}"
        async with session.put(url, json=payload, timeout=TIMEOUT) as r:
            status = r.status
            texto = await r.text()
            if status == 200:
                print(f"✅ Corrida {id_} finalizada: R$ {preco_total:.2f} (Nível {nivel})")
                return True
            else:
                print(f"❌ Corrida {id_} falhou: {status} - {texto}")
                return False

async def executar_simulacao_taxas(num_corridas: int):
    print("\n💸 Aplicando taxas nas corridas...")
    inicio = time.time()
    async with aiohttp.ClientSession() as session:
        corridas = await obter_corridas(session)
        if not corridas:
            print("⚠️ Nenhuma corrida disponível.")
            return

        alvo = min(num_corridas, len(corridas))
        amostra = random.sample(corridas, alvo)
        tarefas = [aplicar_taxas(session, c, corridas) for c in amostra]
        resultados = await asyncio.gather(*tarefas)

        fim = time.time() - inicio
        minutos, segundos = divmod(fim, 60)

        print("\n✅ Resumo da aplicação de taxas:")
        print(f"✔️ {sum(resultados)}/{alvo} corridas com taxas aplicadas.")
        print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")
        print("\n🏁 Finalizado!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplicar taxas em corridas disponíveis")
    parser.add_argument("--corridas", type=int, default=10, help="Quantidade de corridas a processar")
    args = parser.parse_args()

    asyncio.run(executar_simulacao_taxas(args.corridas))
