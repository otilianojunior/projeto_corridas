import requests
import random
import time
import argparse
from faker import Faker

API_URL = "http://127.0.0.1:8000"
fake = Faker("pt_BR")

def formatar_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")

def gerar_dados_motorista(status: str = "disponivel") -> dict:
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),
        "telefone": f"7{random.randint(100000000, 999999999)}",
        "email": fake.email(),
        "status": status
    }

def criar_motoristas(total: int, status: str = "disponivel") -> int:
    criados = 0
    tentativas = 0
    MAX_TENTATIVAS = total * 5

    resposta = requests.get(f"{API_URL}/carros/listar/")
    if resposta.status_code != 200:
        print(f"❌ Erro ao obter carros. Status: {resposta.status_code}")
        return criados

    carros = resposta.json()
    if not carros:
        print("❌ Nenhum carro cadastrado. Cadastre carros antes.")
        return criados

    ids_carros = [carro["id"] for carro in carros]

    while criados < total and tentativas < MAX_TENTATIVAS:
        tentativas += 1
        motorista = gerar_dados_motorista(status)
        motorista["id_carro"] = random.choice(ids_carros)
        response = requests.post(f"{API_URL}/motoristas/", json=motorista)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            continue

    if tentativas >= MAX_TENTATIVAS and criados < total:
        print("⚠️ Limite de tentativas atingido para motoristas.")

    return criados

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cadastro de motoristas na API")
    parser.add_argument("--motoristas", type=int, default=1, help="Quantidade de motoristas a serem cadastrados")
    args = parser.parse_args()

    NUM_MOTORISTAS = args.motoristas

    inicio = time.time()
    print("\n🚗 Criando motoristas...")
    motoristas_criados = criar_motoristas(NUM_MOTORISTAS)
    tempo_total = time.time() - inicio
    minutos, segundos = divmod(tempo_total, 60)
    print(f"\n✔️ {motoristas_criados}/{NUM_MOTORISTAS} motoristas cadastrados.")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")