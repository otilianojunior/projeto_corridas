import pdfplumber
import pandas as pd
import os
import fitz
import re

# Função para tornar os nomes das colunas únicos
# def dedup_columns(columns):
#     seen = {}
#     result = []
#     for col in columns:
#         if col in seen:
#             seen[col] += 1
#             new_col = f"{col}_{seen[col]}"
#         else:
#             seen[col] = 0
#             new_col = col
#         result.append(new_col)
#     return result
#
# # Diretório onde estão os PDFs
# caminho_pdfs = "./"  # ou ajuste para o caminho exato
#
# # Loop de 2015 a 2025
# for ano in range(2015, 2026):
#     nome_pdf = f"PBEV-{ano}.pdf"
#     caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)
#
#     if not os.path.exists(caminho_pdf):
#         print(f"[!] Arquivo não encontrado: {nome_pdf}")
#         continue
#
#     print(f"[+] Processando: {nome_pdf}")
#     tables = []
#
#     with pdfplumber.open(caminho_pdf) as pdf:
#         for i, page in enumerate(pdf.pages):
#             table = page.extract_table()
#             if table:
#                 header = dedup_columns(table[0])
#                 df = pd.DataFrame(table[1:], columns=header)
#                 df["Página"] = i + 1
#                 df["Ano"] = ano
#                 tables.append(df)
#
#     if tables:
#         final_df = pd.concat(tables, ignore_index=True)
#         nome_csv = f"tabela_PBEV_{ano}.csv"
#         caminho_csv = os.path.join(caminho_pdfs, nome_csv)
#         final_df.to_csv(caminho_csv, index=False)
#         print(f"[✔] CSV gerado: {nome_csv}")
#     else:
#         print(f"[!] Nenhuma tabela encontrada em {nome_pdf}")


def extrair_tabela_pbev_2021_pdfplumber(caminho_pdf: str, caminho_csv: str = "tabela_PBEV_2021.csv") -> pd.DataFrame:
    dados = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    # Ignorar linhas completamente vazias ou de cabeçalho repetido
                    if linha and not all(c is None or str(c).strip() == '' for c in linha):
                        dados.append(linha)

    # Remover linhas duplicadas e criar DataFrame
    df = pd.DataFrame(dados)

    # Filtrar colunas com base na quantidade correta de colunas (por exemplo, 23)
    df = df[df.columns[:23]]  # Ajuste conforme o número real de colunas válidas

    # Salvar como CSV
    df.to_csv(caminho_csv, index=False)
    print(f"[✔] Dados extraídos e salvos em: {caminho_csv} ({len(df)} linhas)")

    return df

# Execução direta
if __name__ == "__main__":
    extrair_tabela_pbev_2021_pdfplumber("PBEV-2021.pdf")