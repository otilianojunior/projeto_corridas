import pdfplumber
import pandas as pd
import os


def dedup_columns(columns):
    seen = {}
    result = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
            new_col = col
        result.append(new_col)
    return result


def extrair_tabelas_padrao(caminho_pdf: str, ano: int) -> pd.DataFrame:
    tables = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            if table:
                header = dedup_columns(table[0])
                df = pd.DataFrame(table[1:], columns=header)
                df["Página"] = i + 1
                df["Ano"] = ano
                tables.append(df)
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()


def salvar_csv(df: pd.DataFrame, caminho_csv: str):
    df.to_csv(caminho_csv, index=False)
    print(f"[✔] CSV gerado: {caminho_csv}")


def processar_pdfs_padrao(caminho_pdfs: str = "./", anos: range = range(2015, 2026)):
    for ano in anos:
        if ano == 2021:
            continue

        nome_pdf = f"PBEV-{ano}.pdf"
        caminho_pdf = os.path.join(caminho_pdfs, nome_pdf)

        if not os.path.exists(caminho_pdf):
            print(f"[!] Arquivo não encontrado: {nome_pdf}")
            continue

        print(f"[+] Processando: {nome_pdf}")
        df = extrair_tabelas_padrao(caminho_pdf, ano)

        if not df.empty:
            caminho_csv = os.path.join(caminho_pdfs, f"tabela_PBEV_{ano}.csv")
            salvar_csv(df, caminho_csv)
        else:
            print(f"[!] Nenhuma tabela encontrada em {nome_pdf}")


def extrair_tabela_pbev_2021_pdfplumber(caminho_pdf: str, caminho_csv: str = "tabela_PBEV_2021.csv") -> pd.DataFrame:
    dados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if linha and not all(c is None or str(c).strip() == '' for c in linha):
                        dados.append(linha)

    df = pd.DataFrame(dados)
    df = df[df.columns[:23]]

    salvar_csv(df, caminho_csv)
    return df


if __name__ == "__main__":
    processar_pdfs_padrao()
    extrair_tabela_pbev_2021_pdfplumber("PBEV-2021.pdf")
