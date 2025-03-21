import requests
import random
import time
from faker import Faker

# Configuração da API
API_URL = "http://127.0.0.1:8000"
NUM_MOTORISTAS = 30
NUM_CLIENTES = 100

fake = Faker("pt_BR")

def formatar_cpf(cpf):
    """Remove pontos e traço do CPF"""
    return cpf.replace(".", "").replace("-", "")

def gerar_dados_pessoa(status="disponivel"):
    """Gera dados fictícios para clientes e motoristas"""
    return {
        "nome": fake.name(),
        "cpf": formatar_cpf(fake.cpf()),  # Remove a formatação do CPF
        "telefone": f"7{random.randint(100000000, 999999999)}",  # Garante telefone como string válida
        "email": fake.email(),
        "status": status  # Definir o status do motorista
    }

def criar_pessoas(endpoint, total, status="disponivel"):
    """Cria clientes ou motoristas na API e garante que o número total seja atingido"""
    criados = 0

    while criados < total:
        pessoa = gerar_dados_pessoa(status)
        response = requests.post(f"{API_URL}/{endpoint}/", json=pessoa)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            print(f"⚠️ Erro de validação no cadastro, tentando novamente para o CPF {pessoa['cpf']}")
            continue  # JSON inválido, gera outro registro
        else:
            print(f"❌ Erro ao tentar criar {endpoint} com CPF {pessoa['cpf']}. Código de status: {response.status_code}")
            continue  # Outros erros, tenta novamente

    return criados

if __name__ == "__main__":
    start_time = time.time()  # Inicia o contador de tempo

    # Criar motoristas
    print("🔄 Criando motoristas...")
    motoristas_criados = criar_pessoas("motoristas", NUM_MOTORISTAS)

    # Criar clientes
    print("🔄 Criando clientes...")
    clientes_criados = criar_pessoas("clientes", NUM_CLIENTES)

    elapsed_time = time.time() - start_time  # Calcula o tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    # Exibir resultado final
    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {motoristas_criados}/{NUM_MOTORISTAS} motoristas cadastrados com sucesso.")
    print(f"✔️ {clientes_criados}/{NUM_CLIENTES} clientes cadastrados com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")

    print("\n🎉 Processo finalizado!")
