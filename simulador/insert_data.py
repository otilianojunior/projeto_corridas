import requests
import random
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
    """Cria clientes ou motoristas na API"""
    criados = 0
    for _ in range(total):
        pessoa = gerar_dados_pessoa()
        response = requests.post(f"{API_URL}/{endpoint}/", json=pessoa)

        if response.status_code == 201:
            print(f"✔️ {tipo.capitalize()} criado: {pessoa['nome']}")
            criados += 1
        elif response.status_code == 422:
            print(f"❌ Erro 422 - JSON inválido: {response.json()}")
            continue  # Continua o loop ao invés de interrompê-lo
        else:
            print(f"⚠️ Erro desconhecido: {response.status_code} - {response.text}")
            continue  # Continua o loop mesmo em caso de erro desconhecido

    print(f"\n✅ {criados} {tipo}s cadastrados com sucesso!")

if __name__ == "__main__":
    print("🔄 Criando motoristas...")
    criar_pessoas("motoristas", NUM_MOTORISTAS, "motorista")

    print("\n🔄 Criando clientes...")
    criar_pessoas("clientes", NUM_CLIENTES, "cliente")

    print("\n🎉 Processo finalizado!")
