import requests
import random
import time
from faker import Faker

# Configuração da API
API_URL = "http://127.0.0.1:8000"
NUM_MOTORISTAS = 1
NUM_CLIENTES = 1

fake = Faker("pt_BR")


def formatar_cpf(cpf):
    """Remove pontos e traço do CPF"""
    return cpf.replace(".", "").replace("-", "")


def gerar_dados_pessoa(status="disponivel"):
    """Gera dados fictícios para clientes e motoristas"""
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),
        "telefone": f"7{random.randint(100000000, 999999999)}",
        "email": fake.email(),
        "status": status
    }


def criar_motoristas(total, status="disponivel"):
    criados = 0
    attempts = 0
    MAX_ATTEMPTS = total * 5  # Define um limite para evitar loop infinito

    # Obter a lista de carros cadastrados
    resposta = requests.get(f"{API_URL}/carros/listar/")
    if resposta.status_code != 200:
        print(f"❌ Erro ao obter a lista de carros. Código de status: {resposta.status_code}")
        return criados

    carros = resposta.json()
    if not carros:
        print("❌ Nenhum carro cadastrado. Cadastre carros antes de criar motoristas.")
        return criados

    # Extraindo a lista de IDs dos carros disponíveis
    lista_carro_ids = [carro["id"] for carro in carros]

    while criados < total and attempts < MAX_ATTEMPTS:
        attempts += 1
        pessoa = gerar_dados_pessoa(status)
        # Atribuir aleatoriamente um id_carro ao motorista
        pessoa["id_carro"] = random.choice(lista_carro_ids)
        response = requests.post(f"{API_URL}/motoristas/", json=pessoa)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            continue

    if attempts >= MAX_ATTEMPTS and criados < total:
        print("Limite máximo de tentativas atingido. Motoristas criados:", criados)
    return criados


def criar_clientes(total, status="disponivel"):
    """Cria clientes na API"""
    criados = 0

    while criados < total:
        pessoa = gerar_dados_pessoa(status)
        response = requests.post(f"{API_URL}/clientes/", json=pessoa)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            continue

    return criados


if __name__ == "__main__":
    start_time = time.time()  # Inicia o contador de tempo

    # Criar motoristas
    print("🔄 Criando motoristas...")
    motoristas_criados = criar_motoristas(NUM_MOTORISTAS)

    # Criar clientes (descomente se desejar criar clientes)
    print("🔄 Criando clientes...")
    clientes_criados = criar_clientes(NUM_CLIENTES)

    elapsed_time = time.time() - start_time  # Calcula o tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    # Exibir resultado final
    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {motoristas_criados}/{NUM_MOTORISTAS} motoristas cadastrados com sucesso.")
    print(f"✔️ {clientes_criados}/{NUM_CLIENTES} clientes cadastrados com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")

    print("\n🎉 Processo finalizado!")
