import os

import pandas as pd
import pdfplumber


# Remove duplicatas nos nomes das colunas de uma tabela.
def remover_duplicatas_colunas(colunas):
    ocorrencias = {}
    resultado = []

    for coluna in colunas:
        if coluna in ocorrencias:
            ocorrencias[coluna] += 1
            nova_coluna = f"{coluna}_{ocorrencias[coluna]}"
        else:
            ocorrencias[coluna] = 0
            nova_coluna = coluna
        resultado.append(nova_coluna)

    return resultado


# Extrai tabelas padrão do PDF, ajustando colunas e inserindo metadados adicionais.
def extrair_tabelas_padrão(caminho_pdf: str, ano: int) -> pd.DataFrame:
    tabelas = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for indice, pagina in enumerate(pdf.pages):
            tabela = pagina.extract_table()
            if tabela:
                cabecalho = remover_duplicatas_colunas(tabela[0])
                df = pd.DataFrame(tabela[1:], columns=cabecalho)
                df["Página"] = indice + 1
                df["Ano"] = ano
                tabelas.append(df)

    return pd.concat(tabelas, ignore_index=True) if tabelas else pd.DataFrame()


# Salva um DataFrame em um arquivo CSV.
def salvar_como_csv(df: pd.DataFrame, caminho_csv: str):
    df.to_csv(caminho_csv, index=False)
    print(f"[✔] CSV gerado: {caminho_csv}")


# Processa PDFs em um diretório para diferentes anos e extrai tabelas padrão.
def processar_pdfs(caminho_diretorio: str = "./", anos: range = range(2015, 2026)):
    for ano in anos:
        if ano == 2021:
            continue

        nome_pdf = f"PBEV-{ano}.pdf"
        caminho_pdf = os.path.join(caminho_diretorio, nome_pdf)

        if not os.path.exists(caminho_pdf):
            print(f"[!] Arquivo não encontrado: {nome_pdf}")
            continue

        print(f"[+] Processando: {nome_pdf}")
        df = extrair_tabelas_padrão(caminho_pdf, ano)

        if not df.empty:
            caminho_csv = os.path.join(caminho_diretorio, f"tabela_pbev_{ano}.csv")
            salvar_como_csv(df, caminho_csv)
        else:
            print(f"[!] Nenhuma tabela encontrada em {nome_pdf}")


# Extrai e salva a tabela específica do PDF de 2021, com uma estrutura diferente.
def extrair_tabela_2021(caminho_pdf: str, caminho_csv: str = "data/carros/tabela_pbev_2021.csv") -> pd.DataFrame:
    dados = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if linha and not all(c is None or str(c).strip() == '' for c in linha):
                        dados.append(linha)

    df = pd.DataFrame(dados)
    df = df[df.columns[:23]]  # Limita ao número esperado de colunas

    salvar_como_csv(df, caminho_csv)
    return df


# Ponto de entrada principal para processamento dos PDFs e extração específica para 2021.
if __name__ == "__main__":
    processar_pdfs()
    extrair_tabela_2021("PBEV-2021.pdf")
