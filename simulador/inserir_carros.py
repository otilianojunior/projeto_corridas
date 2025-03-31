import requests
import pandas as pd
import time

# URL base da API
API_URL = "http://127.0.0.1:8000"

# Caminho para o CSV contendo os dados dos carros
ARQUIVO_CSV = "data/carros/dados_tratados_filtrado.csv"

def gerar_dados_carro(row: pd.Series) -> dict:
    """
    Gera um dicionário com os dados de um carro a partir de uma linha do DataFrame.
    """
    return {
        "categoria": row["categoria"],
        "marca": row["marca"],
        "modelo": row["modelo"],
        "motor": row["motor"],
        "versao": row["versao"],
        "transmissao": row["transmissao"],
        "ar_cond": row["ar_cond"],
        "direcao": row["direcao"],
        "combustivel": row["combustivel"],
        "km_etanol_cidade": row["km_etanol_cidade"] if pd.notna(row["km_etanol_cidade"]) else 0,
        "km_etanol_estrada": row["km_etanol_estrada"] if pd.notna(row["km_etanol_estrada"]) else 0,
        "km_gasolina_cidade": row["km_gasolina_cidade"] if pd.notna(row["km_gasolina_cidade"]) else 0,
        "km_gasolina_estrada": row["km_gasolina_estrada"] if pd.notna(row["km_gasolina_estrada"]) else 0,
        "ano": row["ano"]
    }

def cadastrar_carros(df_carros: pd.DataFrame) -> int:
    """
    Envia os dados de carros para a API e retorna a quantidade de registros criados.
    """
    total_criados = 0

    for _, row in df_carros.iterrows():
        carro = gerar_dados_carro(row)
        response = requests.post(f"{API_URL}/carros/", json=carro)

        if response.status_code == 201:
            total_criados += 1
        elif response.status_code == 422:
            print(f"⚠️ Erro de validação no cadastro para o carro: {carro['modelo']}")
        else:
            print(f"❌ Erro ao tentar criar carro {carro['modelo']} (status: {response.status_code})")

    return total_criados

if __name__ == "__main__":
    tempo_inicio = time.time()

    print("🔄 Iniciando cadastro de carros...")
    try:
        df_carros = pd.read_csv(ARQUIVO_CSV)
        total_carros = len(df_carros)
        carros_cadastrados = cadastrar_carros(df_carros)

        tempo_total = time.time() - tempo_inicio
        minutos, segundos = divmod(tempo_total, 60)

        print("\n✅ Cadastro finalizado:")
        print(f"✔️ {carros_cadastrados}/{total_carros} carros cadastrados com sucesso.")
        print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")

    except FileNotFoundError:
        print(f"❌ Arquivo CSV não encontrado: {ARQUIVO_CSV}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")