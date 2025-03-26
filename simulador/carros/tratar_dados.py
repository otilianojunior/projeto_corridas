import pandas as pd
import os


# === FUNÇÕES DE TRATAMENTO DE CADA MODELO ===

def tratar_dados_modelo_I(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)

    if df.shape[1] > 25:
        df.iloc[:, 0] = df.iloc[:, 0].fillna(df.iloc[:, 25])

    colunas_desejadas = [df.columns[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 24]]
    df = df[colunas_desejadas]
    df.columns = [
        'categoria', 'marca', 'modelo', 'motor', 'versao',
        'transmissao', 'ar_cond', 'direcao', 'combustivel',
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada', 'ano'
    ]
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)

    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


def tratar_dados_modelo_II(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)

    if df.shape[1] > 25:
        df.iloc[:, 0] = df.iloc[:, 0].fillna(df.iloc[:, 25])

    colunas_desejadas = [df.columns[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 24]]
    df = df[colunas_desejadas]
    df.columns = [
        'categoria', 'marca', 'modelo', 'versao', 'motor',
        'transmissao', 'ar_cond', 'direcao', 'combustivel',
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada', 'ano'
    ]
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)

    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


def tratar_dados_modelo_III(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    try:
        df = pd.read_csv(caminho_entrada, skiprows=14)
        colunas_indices = [0, 1, 2, 3, 4, 5, 6, 7, 9, 16, 17, 18, 19]
        df = df[[df.columns[i] for i in colunas_indices]]
        df.columns = [
            'categoria', 'marca', 'modelo', 'versao', 'motor',
            'transmissao', 'ar_cond', 'direcao', 'combustivel',
            'km_etanol_cidade', 'km_etanol_estrada',
            'km_gasolina_cidade', 'km_gasolina_estrada'
        ]
        df['categoria'] = df['categoria'].ffill()
        df = df.dropna(how='all')
        df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
        df['ano'] = 2021
        df = df.reset_index(drop=True)

        if caminho_saida:
            df.to_csv(caminho_saida, index=False)
            print(f"[✔] Arquivo tratado salvo em: {caminho_saida}")

        return df
    except Exception as e:
        print(f"[Erro] Falha ao processar arquivo: {e}")
        return pd.DataFrame()


def tratar_dados_modelo_IV(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=2)
    colunas = [0, 1, 2, 3, 4, 6, 7, 8, 9, 17, 18, 19, 20, 29]
    df = df[[df.columns[i] for i in colunas]]
    df.columns = [
        'categoria', 'marca', 'modelo', 'versao', 'motor',
        'transmissao', 'ar_cond', 'direcao', 'combustivel',
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada', 'ano'
    ]
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)

    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


def tratar_dados_modelo_V(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)
    colunas = [0, 1, 2, 3, 4, 6, 7, 8, 9, 17, 18, 19, 20, 29]
    df = df[[df.columns[i] for i in colunas]]
    df.columns = [
        'categoria', 'marca', 'modelo', 'versao', 'motor',
        'transmissao', 'ar_cond', 'direcao', 'combustivel',
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada', 'ano'
    ]
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)

    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


# === FUNÇÃO PARA UNIR TABELAS ===

def unir_tabelas_tratadas(arquivos_csv: list, caminho_saida: str = "dados_tratados.csv") -> pd.DataFrame:
    dataframes = []

    for caminho in arquivos_csv:
        if os.path.exists(caminho):
            print(f"[✔] Lendo: {caminho}")
            df = pd.read_csv(caminho)
            dataframes.append(df)
        else:
            print(f"[⚠] Arquivo não encontrado: {caminho}")

    if not dataframes:
        raise ValueError("Nenhum arquivo válido foi fornecido.")

    df_final = pd.concat(dataframes, ignore_index=True)
    df_final.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo final salvo como: {caminho_saida} ({len(df_final)} linhas)")

    return df_final


def limpar_e_padronizar_dados(caminho_entrada: str, caminho_saida: str = "dados_tratados.csv") -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada)

    # 1. Remover linhas com combustivel "E", "Elétrico" ou "ELÉTRICO"
    df = df[~df['combustivel'].str.upper().isin(["E", "ELÉTRICO"])]

    # 2. Atualizar coluna 'ar_cond'
    df['ar_cond'] = df['ar_cond'].map({
        'S': 'sim',
        'N': 'não'
    }).fillna(df['ar_cond'])  # mantém valores originais se não forem S/N

    # 3. Atualizar coluna 'combustivel'
    combustiveis = {
        'E': 'Elétrico',
        'G': 'Gasolina',
        'F': 'Flex',
        'D': 'Diesel',
    }
    df['combustivel'] = df['combustivel'].map(combustiveis).fillna(df['combustivel'])

    # 4. Atualizar coluna 'direcao'
    direcoes = {
        'H': 'Hidráulica',
        'M': 'Mecânica',
        'E': 'Elétrica',
        'E-H': 'Eletro-hidráulica',
        'E-h': 'Eletro-hidráulica',
        'E­H':'Eletro-hidráulica'
    }
    df['direcao'] = df['direcao'].map(direcoes).fillna(df['direcao'])

    # 5. Atualizar coluna 'transmissao'
    transmissoes = {
        'M': 'Manual',
        'A': 'Automática',
        'DCT': 'Automática Dupla Embreagem',
        'MTA': 'Automatizada',
        'CVT': 'Contínua'
    }
    df['transmissao'] = df['transmissao'].map(transmissoes).fillna(df['transmissao'])

    # Salvar o resultado
    df.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo final limpo salvo como: {caminho_saida} ({len(df)} linhas)")

    return df


# === EXECUÇÃO PRINCIPAL ===

if __name__ == '__main__':
    tratadores = {
        2015: tratar_dados_modelo_I,
        2016: tratar_dados_modelo_I,
        2017: tratar_dados_modelo_II,
        2018: tratar_dados_modelo_II,
        2019: tratar_dados_modelo_II,
        2020: tratar_dados_modelo_I,
        2021: tratar_dados_modelo_III,
        2022: tratar_dados_modelo_II,
        2023: tratar_dados_modelo_IV,
        2024: tratar_dados_modelo_V,
        2025: tratar_dados_modelo_V
    }

    arquivos_tratados = []

    for ano, func in tratadores.items():
        entrada = f"tabela_PBEV_{ano}.csv"
        saida = f"tabela_PBEV_{ano}_tratada.csv"
        func(entrada, saida)
        arquivos_tratados.append(saida)

    unir_tabelas_tratadas(arquivos_tratados, "tabela_PBEV_unida.csv")
    limpar_e_padronizar_dados("tabela_PBEV_unida.csv")
