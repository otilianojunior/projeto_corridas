import requests
import pandas as pd
import time
import argparse
import os

# Importações diretas dos scripts de geração de dados
from data.carros import extrair_tabelas_pbev, tratar_dados

# URL base da API
API_URL = "http://127.0.0.1:8000"

# Caminho para o CSV contendo os dados dos carros
ARQUIVO_CSV = "data/carros/dados_tratados_filtrado.csv"


def verificar_ou_gerar_csv():
    """
    Verifica se o CSV de carros existe. Caso não exista, executa os scripts necessários para gerá-lo.
    """
    if not os.path.exists(ARQUIVO_CSV):
        print("📂 Arquivo CSV não encontrado. Gerando dados...")
        try:
            extrair_tabelas_pbev.processar_pdfs("data/carros")
            extrair_tabelas_pbev.extrair_tabela_2021("data/carros/PBEV-2021.pdf")
            tratar_dados.main()
        except Exception as e:
            print(f"❌ Erro ao gerar dados: {e}")
            exit(1)


def gerar_dados_carro(row: pd.Series) -> dict:
    """
    Converte uma linha do DataFrame em um dicionário, substituindo NaNs por None.
    """
    row = row.where(pd.notna(row), None)
    return row.to_dict()


def cadastrar_carros(quantidade: int = None) -> int:
    """
    Lê o CSV, envia os dados dos carros para a API e retorna a quantidade de carros cadastrados com sucesso.
    """
    try:
        df_carros = pd.read_csv(ARQUIVO_CSV)
        if quantidade:
            df_carros = df_carros.head(quantidade)
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

    except FileNotFoundError:
        print(f"❌ Arquivo CSV não encontrado: {ARQUIVO_CSV}")
        return 0
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return 0


def run_inserir_carros(quantidade: int = None) -> int:
    """
    Executa o processo de verificação, cadastro de carros e imprime o resumo do processo.
    Essa função pode ser chamada tanto quando o script é executado diretamente quanto por outro módulo.
    """
    verificar_ou_gerar_csv()

    tempo_inicio = time.time()
    print("\n🚗 Iniciando cadastro de carros...")
    carros_cadastrados = cadastrar_carros(quantidade=quantidade)
    tempo_total = time.time() - tempo_inicio
    minutos, segundos = divmod(tempo_total, 60)

    print("\n✅ Resumo do cadastro:")
    print(f"✔️ {carros_cadastrados} carros cadastrados com sucesso.")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.")

    return carros_cadastrados


# Bloco de execução para quando o script é executado diretamente
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inserir carros na API a partir de um CSV")
    parser.add_argument("--carros",type=int,default=None,help="Quantidade padrão: todos)")
    args = parser.parse_args()
    run_inserir_carros(quantidade=args.carros)
