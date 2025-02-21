import requests
import random
import time
from faker import Faker

# Configuração da API
API_URL = "http://127.0.0.1:8000"
NUM_MOTORISTAS = 5000
NUM_CLIENTES = 10000

fake = Faker("pt_BR")

def formatar_cpf(cpf):
    """Remove pontos e traço do CPF"""
    return cpf.replace(".", "").replace("-", "")

def gerar_dados_pessoa():
    """Gera dados fictícios para clientes e motoristas"""
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),  # Remove a formatação do CPF
        "telefone": f"7{random.randint(100000000, 999999999)}",  # Garante telefone como string válida
        "email": fake.email()
    }

def criar_pessoas(endpoint, total, tipo):
    """Cria clientes ou motoristas na API e garante que o número total seja atingido"""
    criados = 0

    while criados < total:
        pessoa = gerar_dados_pessoa()
        response = requests.post(f"{API_URL}/{endpoint}/", json=pessoa)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            continue  # JSON inválido, gera outro registro
        else:
            continue  # Outros erros, tenta novamente

        if criados % 500 == 0:  # Mostra progresso a cada 500 criados
            print(f"✔️ {criados}/{total} {tipo}s cadastrados...")

    return criados

if __name__ == "__main__":
    start_time = time.time()  # Inicia o contador de tempo

    print("🔄 Criando motoristas...")
    motoristas_criados = criar_pessoas("motoristas", NUM_MOTORISTAS, "motorista")

    print("\n🔄 Criando clientes...")
    clientes_criados = criar_pessoas("clientes", NUM_CLIENTES, "cliente")

    elapsed_time = time.time() - start_time  # Calcula o tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {motoristas_criados}/{NUM_MOTORISTAS} motoristas cadastrados com sucesso.")
    print(f"✔️ {clientes_criados}/{NUM_CLIENTES} clientes cadastrados com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")

    print("\n🎉 Processo finalizado!")
