import argparse
import random
import time

import requests
from faker import Faker

API_URL = "http://127.0.0.1:8000"
fake = Faker("pt_BR")


# Formata o número de CPF removendo caracteres especiais.
def formatar_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")


# Gera dados fictícios para um cliente utilizando a biblioteca Faker.
def gerar_dados_cliente(status: str = "disponivel") -> dict:
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),
        "telefone": f"7{random.randint(100000000, 999999999)}",
        "email": fake.email(),
        "status": status
    }


# Realiza a criação de clientes na API até atingir o total desejado.
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


# Executa o processo de cadastro de clientes com dados gerados aleatoriamente.
def run_inserir_clientes(total: int, status: str = "disponivel") -> int:

    inicio = time.time()
    print("\n👥 Iniciando cadastro de clientes...")
    clientes_criados = criar_clientes(total, status)
    tempo_total = time.time() - inicio
    minutos, segundos = divmod(tempo_total, 60)

    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {clientes_criados}/{total} clientes cadastrados com sucesso.")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")

    return clientes_criados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cadastro de clientes na API")
    parser.add_argument("--clientes", type=int, default=1, help="Quantidade de clientes a serem cadastrados")
    args = parser.parse_args()

    run_inserir_clientes(total=args.clientes)
