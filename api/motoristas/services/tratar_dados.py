import pandas as pd
import os
import glob

def tratar_colunas(df):
    # Padroniza nomes de colunas
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Remover colunas indesejadas (mesmo que tenham variações de nome)
    colunas_para_remover = [
        "emissões_no_escapamento",
        "poluentes_gás_efeito_estufa_consumo_energético_(mj/km)",
        "classificação_pbe",
        "selo_conpet_de_eficiência_energética",
        "página"
    ]
    df = df[[col for col in df.columns if col not in colunas_para_remover]]

    # Remover linhas completamente vazias
    df.dropna(how="all", inplace=True)

    # Corrigir duplicação da coluna categoria (manter a da esquerda)
    categorias = [col for col in df.columns if col.startswith("categoria")]
    if len(categorias) > 1:
        col_a_manter = categorias[0]
        colunas_a_excluir = categorias[1:]
        df.drop(columns=colunas_a_excluir, inplace=True)

    # Converter colunas numéricas quando possível
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')

    # Limpar caracteres como \ e -
    df.replace(r"[\\\-]", "", regex=True, inplace=True)

    return df

# Caminho onde estão os CSVs gerados
caminho_csvs = "./"
arquivos = glob.glob(os.path.join(caminho_csvs, "tabela_PBEV_*.csv"))

dfs = []
for arq in arquivos:
    df = pd.read_csv(arq)
    df = tratar_colunas(df)
    dfs.append(df)

# Unificar todos os CSVs tratados
df_total = pd.concat(dfs, ignore_index=True)

# Exportar CSV final tratado
df_total.to_csv("dados_tratados_PBEV.csv", index=False)
print("✅ Arquivo final tratado salvo como: dados_tratados_PBEV.csv")
