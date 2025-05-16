import os

import pandas as pd


# Trata dados de acordo com o modelo 1, selecionando e ajustando colunas específicas.
def tratar_modelo_1(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)
    if df.shape[1] > 25:
        df.iloc[:, 0] = df.iloc[:, 0].fillna(df.iloc[:, 25])
    colunas = [df.columns[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 24]]
    df = df[colunas]
    df.columns = ['categoria', 'marca', 'modelo', 'motor', 'versao', 'transmissao', 'ar_condicionado', 'direcao',
                  'combustivel', 'km_etanol_cidade', 'km_etanol_estrada', 'km_gasolina_cidade', 'km_gasolina_estrada',
                  'ano']
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)
    return df

# Trata dados de acordo com o modelo 2, com ajustes em colunas específicas.
def tratar_modelo_2(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)
    if df.shape[1] > 25:
        df.iloc[:, 0] = df.iloc[:, 0].fillna(df.iloc[:, 25])
    colunas = [df.columns[i] for i in [0, 1, 2, 3, 4, 6, 7, 8, 9, 16, 17, 18, 19, 25]]
    df = df[colunas]
    df.columns = ['categoria', 'marca', 'modelo', 'versao', 'motor', 'transmissao', 'ar_condicionado', 'direcao',
                  'combustivel', 'km_etanol_cidade', 'km_etanol_estrada', 'km_gasolina_cidade', 'km_gasolina_estrada',
                  'ano']
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)
    return df

# Trata dados do modelo 3, ajustando colunas e fixando o ano.
def tratar_modelo_3(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=14)
    colunas = [df.columns[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 9, 16, 17, 18, 19]]
    df = df[colunas]
    df.columns = ['categoria', 'marca', 'modelo', 'versao', 'motor', 'transmissao', 'ar_condicionado', 'direcao',
                  'combustivel', 'km_etanol_cidade', 'km_etanol_estrada', 'km_gasolina_cidade', 'km_gasolina_estrada']
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df['ano'] = 2021
    df = df.reset_index(drop=True)
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)
    return df

# Trata dados do modelo 4, ajustando para a estrutura específica.
def tratar_modelo_4(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=2)
    colunas = [df.columns[i] for i in [0, 1, 2, 3, 4, 6, 7, 8, 9, 17, 18, 19, 20, 29]]
    df = df[colunas]
    df.columns = ['categoria', 'marca', 'modelo', 'versao', 'motor', 'transmissao', 'ar_condicionado', 'direcao',
                  'combustivel', 'km_etanol_cidade', 'km_etanol_estrada', 'km_gasolina_cidade', 'km_gasolina_estrada',
                  'ano']
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)
    return df

# Trata dados do modelo 5, ajustando colunas e formatos.
def tratar_modelo_5(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    df = pd.read_csv(caminho_entrada, skiprows=3)
    colunas = [df.columns[i] for i in [0, 1, 2, 3, 4, 6, 7, 8, 9, 17, 18, 19, 20, 29]]
    df = df[colunas]
    df.columns = ['categoria', 'marca', 'modelo', 'versao', 'motor', 'transmissao', 'ar_condicionado', 'direcao',
                  'combustivel', 'km_etanol_cidade', 'km_etanol_estrada', 'km_gasolina_cidade', 'km_gasolina_estrada',
                  'ano']
    df['categoria'] = df['categoria'].ffill()
    df = df.dropna(how='all')
    df = df.dropna(subset=['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada'])
    df = df.reset_index(drop=True)
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)
    return df

# Une múltiplos arquivos CSV em um único DataFrame.
def unir_tabelas(arquivos: list, caminho_saida: str = "dados_tratados.csv") -> pd.DataFrame:
    tabelas = []
    for caminho in arquivos:
        if os.path.exists(caminho):
            print(f"[✔] Lendo: {caminho}")
            tabela = pd.read_csv(caminho)
            tabelas.append(tabela)
        else:
            print(f"[⚠] Arquivo não encontrado: {caminho}")

    if not tabelas:
        raise ValueError("Nenhum arquivo válido foi encontrado.")

    tabela_final = pd.concat(tabelas, ignore_index=True)
    tabela_final.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo unido salvo em: {caminho_saida} ({len(tabela_final)} linhas)")
    return tabela_final

# Padroniza dados específicos, como combustível e transmissão.
def padronizar_dados(df: pd.DataFrame, caminho_saida: str = "data/carros/dados_tratados.csv") -> pd.DataFrame:
    df = df[~df['combustivel'].str.upper().isin(["E", "ELÉTRICO"])]

    df.loc[:, 'ar_condicionado'] = df['ar_condicionado'].map({
        'S': 'sim',
        'N': 'não'
    }).fillna(df['ar_condicionado'])

    combustiveis = {
        'E': 'elétrico',
        'G': 'gasolina',
        'F': 'flex',
        'D': 'diesel'
    }
    df.loc[:, 'combustivel'] = df['combustivel'].map(combustiveis).fillna(df['combustivel'])

    direcoes = {
        'H': 'hidráulica',
        'M': 'mecânica',
        'E': 'elétrica',
        'E-H': 'eletro-hidráulica',
        'E-h': 'eletro-hidráulica',
        'E­H': 'eletro-hidráulica'
    }
    df.loc[:, 'direcao'] = df['direcao'].map(direcoes).fillna(df['direcao'])

    transmissoes = {
        'M': 'manual',
        'A': 'automática',
        'DCT': 'automática dupla embreagem',
        'MTA': 'automatizada',
        'CVT': 'contínua'
    }
    df.loc[:, 'transmissao'] = df['transmissao'].map(transmissoes).fillna(df['transmissao'])

    df.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo padronizado salvo em: {caminho_saida} ({len(df)} linhas)")
    return df

# Converte valores e ajusta campos textuais do DataFrame.
def tratar_valores(df: pd.DataFrame) -> pd.DataFrame:
    colunas_km = [
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada'
    ]
    for coluna in colunas_km:
        df.loc[:, coluna] = df[coluna].astype(str).str.replace(',', '.')
        df.loc[:, coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0)

    colunas_texto = [
        'categoria', 'marca', 'modelo', 'motor', 'versao',
        'transmissao', 'ar_condicionado', 'direcao', 'combustivel'
    ]
    for coluna in colunas_texto:
        df.loc[:, coluna] = df[coluna].astype(str).str.replace(r'\n', '', regex=True)
        df.loc[:, coluna] = df[coluna].str.replace(r'\xad', '', regex=True)
        df.loc[:, coluna] = df[coluna].str.strip().str.lower()

    df.loc[:, 'transmissao'] = df['transmissao'].fillna('n/d')
    df.loc[:, 'ar_condicionado'] = df['ar_condicionado'].fillna('n/d')
    df.loc[:, 'direcao'] = df['direcao'].fillna('não informado')

    df.loc[:, 'marca'] = df['marca'].replace('vw', 'volkswagen')

    return df

# Filtra modelos específicos e salva o resultado.
def filtrar_modelos(df: pd.DataFrame, modelos: list,
                    caminho_saida: str = "data/carros/dados_tratados_filtrado.csv") -> pd.DataFrame:
    df_filtrado = df[df['modelo'].isin(modelos)]
    df_filtrado.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo filtrado salvo em: {caminho_saida} ({len(df_filtrado)} linhas)")
    return df_filtrado


def main():
    tratadores = {
        2015: tratar_modelo_1,
        2016: tratar_modelo_1,
        2017: tratar_modelo_1,
        2018: tratar_modelo_1,
        2019: tratar_modelo_1,
        2020: tratar_modelo_1,
        2021: tratar_modelo_3,
        2022: tratar_modelo_2,
        2023: tratar_modelo_4,
        2024: tratar_modelo_5,
        2025: tratar_modelo_5
    }

    arquivos_tratados = []

    for ano, funcao_tratar in tratadores.items():
        caminho_entrada = f"data/carros/tabela_pbev_{ano}.csv"
        caminho_saida = f"data/carros/tabela_pbev_{ano}_tratada.csv"
        funcao_tratar(caminho_entrada, caminho_saida)
        arquivos_tratados.append(caminho_saida)

    df_unido = unir_tabelas(arquivos_tratados, "data/carros/tabela_pbev_unida.csv")
    df_padronizado = padronizar_dados(df_unido, "data/carros/tabela_pbev_padronizada.csv")
    df_tratado = tratar_valores(df_padronizado)

    modelos_desejados = [
        'onix', 'argo', 'mobi', 'gol', 'uno', 'logan', 'kwid',
        'hb20', 'hb20s', 'voyage', 'siena', 'versa', 'chery', 'kicks',
        'ka', 'sandero', '208', 'cronos', 'c3', 'polo', 'city', 'fit',
        'civic', 'yaris', 'spin', 'picanto', 'corolla', 'doblò'
    ]

    df_filtrado = filtrar_modelos(df_tratado, modelos_desejados)
    print(df_tratado.head())


if __name__ == "__main__":
    main()
