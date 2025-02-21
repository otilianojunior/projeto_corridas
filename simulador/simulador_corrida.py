import requests
import random
import csv
import os
from datetime import datetime, timedelta

# Configuração da API
API_URL = "//0.0.0.0:8000/corridas/simular"

# Definição de bairros e locais aleatórios
BAIRROS = ["Alto Maron", "Ayrton Senna", "Bateias", "Boa Vista", "Brasil", "Campinhos", "Candeias", "Centro", "Cruzeiro", "Distrito Industrial",
           "Espírito Santo", "Felícia", "Guarani", "Ibirapuera", "Jatobá", "Jurema", "Lagohttp://127.0.0.1:8000/corridas/simulara das Flores", "Nossa Senhora Aparecida", "Patagônia",
           "Primavera", "Recreio", "São Pedro", "Universidade", "Zabelê"]

TAXAS = ["cancelamento", "adicional_noturno", "horario_pico", "manutencao_app"]

# Configuração de Simulação
NUM_CORRIDAS_POR_DIA = 10_000
DIAS_SIMULADOS = 30
DATA_INICIAL = datetime.now() - timedelta(days=DIAS_SIMULADOS)

# Criar diretório para salvar os dados
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Criar arquivo CSV para armazenar os dados simulados
CSV_FILE = os.path.join(DATA_DIR, "corridas_simuladas.csv")

# Criar e escrever cabeçalho no CSV
with open(CSV_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "id_corrida", "data", "origem", "destino", "distancia_km",
        "preco_total", "taxas_aplicadas", "lucro_motorista", "lucro_empresa"
    ])


def gerar_corrida(data_corrida):
    """Gera uma corrida aleatória com taxas aplicadas"""
    origem = random.choice(BAIRROS)
    destino = random.choice([b for b in BAIRROS if b != origem])
    distancia_km = round(random.uniform(2, 20), 2)  # Distância aleatória entre 2km e 20km
    preco_total = round(distancia_km * random.uniform(2.5, 3.5), 2)  # Preço por km entre 2.5 e 3.5
    taxas_aplicadas = random.sample(TAXAS, random.randint(0, len(TAXAS)))  # Taxas aleatórias
    lucro_empresa = round(preco_total * 0.2, 2)  # Empresa fica com 20% do valor
    lucro_motorista = round(preco_total - lucro_empresa, 2)  # Motorista fica com 80%

    return {
        "local_origem": origem,
        "local_destino": destino,
        "distancia_km": distancia_km,
        "preco_total": preco_total,
        "taxas_aplicadas": ", ".join(taxas_aplicadas),
        "id_motorista": random.randint(1, 5000),  # Motorista aleatório
        "valor_motorista": lucro_motorista,
        "created_at": data_corrida.strftime("%Y-%m-%d %H:%M:%S")
    }, lucro_empresa, lucro_motorista


def enviar_corrida(corrida):
    """Envia a corrida para a API"""
    try:
        response = requests.post(API_URL, json=corrida)
        response.raise_for_status()
        return response.json().get("id")  # Retorna o ID da corrida criada
    except requests.RequestException as e:
        print(f"Erro ao enviar corrida: {e}")
        return None


def simular_corridas():
    """Simula 30 dias de corridas, 10.000 por dia"""
    lucro_total_empresa = 0
    lucro_total_motoristas = 0

    for i in range(DIAS_SIMULADOS):
        data_corrida = DATA_INICIAL + timedelta(days=i)

        for _ in range(NUM_CORRIDAS_POR_DIA):
            corrida, lucro_empresa, lucro_motorista = gerar_corrida(data_corrida)
            id_corrida = enviar_corrida(corrida)

            if id_corrida:
                # Escrever corrida no CSV
                with open(CSV_FILE, mode="a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        id_corrida, data_corrida.strftime("%Y-%m-%d"), corrida["local_origem"],
                        corrida["local_destino"], corrida["distancia_km"], corrida["preco_total"],
                        corrida["taxas_aplicadas"], corrida["valor_motorista"], lucro_empresa
                    ])

                lucro_total_empresa += lucro_empresa
                lucro_total_motoristas += lucro_motorista

        print(f"✔️ Simulação do dia {i + 1}/{DIAS_SIMULADOS} concluída.")

    print(f"\n🔹 Lucro total da empresa em {DIAS_SIMULADOS} dias: R$ {lucro_total_empresa:.2f}")
    print(f"🔹 Lucro total dos motoristas em {DIAS_SIMULADOS} dias: R$ {lucro_total_motoristas:.2f}")


if __name__ == "__main__":
    simular_corridas()
