import requests
import pandas as pd
import time

# Configuração da API
API_URL = "http://127.0.0.1:8000"
file_path = 'carros/dados_tratados_filtrado.csv'
df_carros = pd.read_csv(file_path)

NUM_CARROS = len(df_carros)

def gerar_dados_carro(row):
    """Gera dados do carro a partir de uma linha do CSV"""
    carro = {
        "categoria": row['categoria'],
        "marca": row['marca'],
        "modelo": row['modelo'],
        "motor": row['motor'],
        "versao": row['versao'],
        "transmissao": row['transmissao'],
        "ar_cond": row['ar_cond'],
        "direcao": row['direcao'],
        "combustivel": row['combustivel'],
        "km_etanol_cidade": row['km_etanol_cidade'] if pd.notna(row['km_etanol_cidade']) else 0,
        "km_etanol_estrada": row['km_etanol_estrada'] if pd.notna(row['km_etanol_estrada']) else 0,
        "km_gasolina_cidade": row['km_gasolina_cidade'] if pd.notna(row['km_gasolina_cidade']) else 0,
        "km_gasolina_estrada": row['km_gasolina_estrada'] if pd.notna(row['km_gasolina_estrada']) else 0,
        "ano": row['ano']
    }
    return carro

def cadastrar_carros(df_carros):
    """Cadastra todos os carros do DataFrame na API"""
    criados = 0

    # Itera sobre todas as linhas do DataFrame
    for index, row in df_carros.iterrows():
        carro = gerar_dados_carro(row)

        # Imprime os dados do carro que está sendo enviado
        print(f"\nEnviando carro para cadastro: {carro}")

        response = requests.post(f"{API_URL}/carros/", json=carro)

        if response.status_code == 201:
            criados += 1
        elif response.status_code == 422:
            print(f"⚠️ Erro de validação no cadastro para o carro {carro['modelo']}")
        else:
            print(f"❌ Erro ao tentar criar carro {carro['modelo']}. Código de status: {response.status_code}")

    return criados

if __name__ == "__main__":
    start_time = time.time()  # Inicia o contador de tempo

    print("🔄 Criando carros...")
    carros_criados = cadastrar_carros(df_carros)

    elapsed_time = time.time() - start_time  # Calcula o tempo total
    minutes, seconds = divmod(elapsed_time, 60)

    # Exibir resultado final
    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {carros_criados}/{NUM_CARROS} carros cadastrados com sucesso.")
    print(f"\n⏳ Tempo total de execução: {int(minutes)} min {seconds:.2f} seg.")
    print("\n🎉 Processo finalizado!")
