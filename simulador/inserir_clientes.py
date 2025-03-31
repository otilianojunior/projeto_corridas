import requests
import random
import time
import argparse
from faker import Faker

API_URL = "http://127.0.0.1:8000"
fake = Faker("pt_BR")

def formatar_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")

def gerar_dados_cliente(status: str = "disponivel") -> dict:
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),
        "telefone": f"7{random.randint(100000000, 999999999)}",
        "email": fake.email(),
        "status": status
    }

def criar_clientes(total: int, status: str = "disponivel") -> int:
    criados = 0

    while criados < total:
        cliente = gerar_dados_cliente(status)
        response = requests.post(f"{API_URL}/clientes/", json=cliente)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            continue

    return criados

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cadastro de clientes na API")
    parser.add_argument("--clientes", type=int, default=5000, help="Quantidade de clientes a serem cadastrados")
    args = parser.parse_args()

    inicio = time.time()
    print("\n👥 Criando clientes...")
    clientes_criados = criar_clientes(args.clientes)
    tempo_total = time.time() - inicio
    minutos, segundos = divmod(tempo_total, 60)

    print(f"\n✔️ {clientes_criados}/{args.clientes} clientes cadastrados.")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")
