import argparse
import asyncio
import json
import random
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import aiohttp

API_URL = "http://0.0.0.0:8000"
TIMEOUT = 120
MAX_CONCORRENTES = 5

# Semáforo para limitar concorrência de requisições simultâneas
semaforo = asyncio.Semaphore(MAX_CONCORRENTES)
corridas_disponiveis_global = []


# Carrega os níveis de taxas otimizadas a partir de um arquivo JSON
def carregar_niveis_taxas_otimizadas(caminho: str = "../data/ml/resultados/niveis_taxas_otimizadas.json") -> dict:
    caminho_arquivo = Path(caminho)
    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo.resolve()}")
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        niveis = json.load(f)

    # Adiciona nível 6 (personalizado) com apenas taxa de manutenção e cancelamento
    nivel_6 = {
        "taxa_manutencao": 1.0,
        "taxa_limpeza": 0.0,
        "taxa_pico": 0.0,
        "taxa_noturna": 0.0,
        "taxa_excesso_corridas": 0.0,
        "taxa_cancelamento": 4.0
    }
    niveis["6"] = nivel_6
    return niveis


NIVEIS_TAXAS_OTIMIZADAS = carregar_niveis_taxas_otimizadas()


# Retorna as taxas para um dado nível de taxa
def obter_taxas_por_nivel_continuo(nivel: int) -> dict:
    return NIVEIS_TAXAS_OTIMIZADAS.get(str(nivel), NIVEIS_TAXAS_OTIMIZADAS["5"])


# Verifica se o horário está dentro de faixas de horário de pico
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


# Verifica se é horário noturno (entre 22h e 6h)
def eh_horario_noturno(horario: str) -> bool:
    data_hora = datetime.strptime(horario, "%Y-%m-%dT%H:%M:%S")
    hora = data_hora.time()
    return hora >= datetime.strptime("22:00:00", "%H:%M:%S").time() or hora <= datetime.strptime("06:00:00",
                                                                                                 "%H:%M:%S").time()


# Verifica se há excesso de corridas em um mesmo horário
def excesso_de_corridas(horario: str, corridas) -> bool:
    return sum(1 for corrida in corridas if corrida["horario_pedido"] == horario) > 10


# Obtém a lista de corridas disponíveis via API
async def listar_corridas_disponiveis(session):
    url = f"{API_URL}/corridas/listar_disponiveis"
    async with session.get(url, timeout=TIMEOUT) as resposta:
        if resposta.status == 200:
            dados = await resposta.json()
            return dados.get("corridas_disponiveis", [])
        return []


# Calcula o valor da tarifa base por km com base no consumo do veículo
async def calcular_tarifa_base_por_km(consumo) -> Decimal:
    preco_combustivel = Decimal("6")  # valor fixo do combustível
    return preco_combustivel / Decimal(str(consumo)) + Decimal("0.50")


# Aplica as taxas a uma corrida específica e envia o resultado via API
async def aplicar_taxas_corrida(session, todas_corridas):
    async with semaforo:
        if not corridas_disponiveis_global:
            return 0

        corrida = corridas_disponiveis_global.pop(0)
        id_corrida = corrida["id"]
        distancia = Decimal(str(corrida["distancia_km"]))
        horario_pedido = corrida["horario_pedido"]
        nivel_taxa = random.randint(1, 6)
        taxas = obter_taxas_por_nivel_continuo(nivel_taxa)

        combustivel = (corrida.get("combustivel") or "").lower()
        consumo = corrida.get("km_gasolina_cidade", 10) if combustivel in ["gasolina", "flex"] else corrida.get(
            "km_etanol_cidade", 10)

        taxas_aplicadas = {}
        taxa_manutencao_fixa = Decimal(str(taxas["taxa_manutencao"]))
        taxas_aplicadas["taxa_manutencao"] = taxa_manutencao_fixa
        preco_total = Decimal("0.0")

        if nivel_taxa == 6:
            # Somente manutenção e cancelamento para o nível 6
            taxa_cancelamento = Decimal(str(taxas.get("taxa_cancelamento", 0)))
            taxas_aplicadas["taxa_cancelamento"] = taxa_cancelamento
            preco_total = taxa_manutencao_fixa + taxa_cancelamento
        else:
            tarifa_base = await calcular_tarifa_base_por_km(consumo)
            if "taxa_limpeza" in taxas:
                taxas_aplicadas["taxa_limpeza"] = Decimal(str(taxas["taxa_limpeza"]))
            if horario_pico(horario_pedido):
                taxas_aplicadas["taxa_pico"] = Decimal(str(taxas["taxa_pico"]))
            if eh_horario_noturno(horario_pedido):
                taxas_aplicadas["taxa_noturna"] = Decimal(str(taxas["taxa_noturna"]))
            if excesso_de_corridas(horario_pedido, todas_corridas):
                taxas_aplicadas["taxa_excesso_corridas"] = Decimal(str(taxas["taxa_excesso_corridas"]))

            taxas_percentuais = sum([
                taxas_aplicadas.get("taxa_limpeza", Decimal(0)),
                taxas_aplicadas.get("taxa_pico", Decimal(0)),
                taxas_aplicadas.get("taxa_noturna", Decimal(0)),
                taxas_aplicadas.get("taxa_excesso_corridas", Decimal(0))
            ])

            preco_por_km = tarifa_base * (1 + taxas_percentuais) + taxa_manutencao_fixa
            preco_total = preco_por_km * distancia

        # Valor do motorista corresponde a 78% do valor total da corrida
        valor_motorista = round(preco_total * Decimal("0.78"), 2)

        payload = {
            **{k: float(v) for k, v in taxas_aplicadas.items()},
            "valor_motorista": float(valor_motorista),
            "preco_total": float(preco_total),
            "preco_km": float(preco_total / distancia) if distancia > 0 else 0,
            "nivel_taxa": nivel_taxa
        }

        url = f"{API_URL}/corridas/finalizar_corrida/{id_corrida}"
        async with session.put(url, json=payload, timeout=TIMEOUT) as resposta:
            status = resposta.status
            texto = await resposta.text()
            if status == 200:
                print(f"Corrida {id_corrida} finalizada: R$ {preco_total:.2f} (Nível {nivel_taxa})")
                return 1
            else:
                print(f"Corrida {id_corrida} falhou: {status} - {texto}")
                return 0


# Executa a simulação para múltiplas corridas
async def executar_simulacao_taxas(qtd_corridas: int):
    print("Aplicando taxas nas corridas:")
    inicio = time.time()
    async with aiohttp.ClientSession() as session:
        global corridas_disponiveis_global
        corridas_disponiveis_global = await listar_corridas_disponiveis(session)
        if not corridas_disponiveis_global:
            print("Nenhuma corrida disponível.")
            return

        qtd_alvo = min(qtd_corridas, len(corridas_disponiveis_global))
        tarefas = [aplicar_taxas_corrida(session, corridas_disponiveis_global) for _ in range(qtd_alvo)]
        resultados = await asyncio.gather(*tarefas)
        taxas_aplicadas = sum(resultados)

        tempo_total = time.time() - inicio
        minutos, segundos = divmod(tempo_total, 60)

        print("\nResumo da aplicação de taxas:")
        print(f"{taxas_aplicadas}/{qtd_alvo} corridas com taxas aplicadas.")
        print(f"Tempo total: {int(minutos)} min {segundos:.2f} seg.")
        print("\nFinalizado!")
        return taxas_aplicadas


# Ponto de entrada principal para execução via linha de comando
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplicar taxas em corridas disponíveis")
    parser.add_argument("--corridas", type=int, default=1, help="Quantidade de corridas a processar")
    argumentos = parser.parse_args()
    asyncio.run(executar_simulacao_taxas(argumentos.corridas))
