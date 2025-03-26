import pandas as pd
import os


def tratar_dados_modelo_I(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    # Carrega o arquivo pulando as 5 primeiras linhas
    df = pd.read_csv(caminho_entrada, skiprows=3)

    # Corrigir linhas onde a categoria aparece na coluna 25 (índice 24)
    if df.shape[1] > 25:
        # Preencher coluna 0 (categoria) com valores da coluna 25 quando estiverem ausentes
        df.iloc[:, 0] = df.iloc[:, 0].fillna(df.iloc[:, 25])

    # Selecionar colunas úteis
    colunas_desejadas = [
        df.columns[0],   # categoria
        df.columns[1],   # marca
        df.columns[2],   # modelo
        df.columns[3],   # motor
        df.columns[4],   # versao
        df.columns[5],   # transmissao
        df.columns[6],   # ar_cond
        df.columns[7],   # direcao
        df.columns[8],   # combustivel
        df.columns[15],  # km_etanol_cidade
        df.columns[16],  # km_etanol_estrada
        df.columns[17],  # km_gasolina_cidade
        df.columns[18],  # km_gasolina_estrada
        df.columns[24]   # ano
    ]
    df = df[colunas_desejadas]

    # Renomear colunas corretamente
    df.columns = [
        'categoria', 'marca', 'modelo', 'motor', 'versao',
        'transmissao', 'ar_cond', 'direcao', 'combustivel',
        'km_etanol_cidade', 'km_etanol_estrada',
        'km_gasolina_cidade', 'km_gasolina_estrada', 'ano'
    ]

    # Preencher categorias ausentes com o valor da linha anterior
    df['categoria'] = df['categoria'].ffill()

    # Remover linhas totalmente vazias
    df = df.dropna(how='all')

    # Remover linhas com dados essenciais ausentes
    for col in ['marca', 'modelo', 'motor', 'versao', 'km_etanol_estrada']:
        df = df[df[col].notna()]

    # Resetar índice
    df = df.reset_index(drop=True)

    # Salvar, se necessário
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df




def tratar_dados_modelo_II(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    # Carregar o arquivo
    df = pd.read_csv(caminho_entrada)

    # Remover linhas totalmente vazias
    df = df.dropna(how='all')

    # Remover linhas com títulos desnecessários
    palavras_chave = [
        'Marca', 'Modelo', 'Versão', 'Motor', 'Transmissão',
        'Velocidades', 'Ar', 'Direção', 'Combustível',
        'Cidade', 'Estrada', 'Gasolina', 'Diesel'
    ]
    filtro = ~df.apply(lambda row: any(str(cell).strip().startswith(tuple(palavras_chave)) for cell in row), axis=1)
    df = df[filtro]

    # Remover linhas com valores ausentes nas colunas essenciais
    colunas_essenciais = ['marca', 'modelo', 'motor', 'versao']
    for coluna in colunas_essenciais:
        df = df[df[coluna].notna()]

    # Resetar índice
    df = df.reset_index(drop=True)

    # Salvar, se for desejado
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


def tratar_dados_modelo_III(caminho_entrada: str, caminho_saida: str = None, ano: int = 2021) -> pd.DataFrame:

    # Carregar CSV
    df = pd.read_csv(caminho_entrada)

    # Remover colunas totalmente vazias
    df = df.dropna(axis=1, how='all')

    # Garantir que as colunas essenciais existem
    colunas_essenciais = ['marca', 'modelo', 'motor', 'versao']
    for coluna in colunas_essenciais:
        if coluna not in df.columns:
            raise ValueError(f"Coluna essencial ausente: '{coluna}'")

    # Remover linhas que tenham valores ausentes nas colunas essenciais
    for coluna in colunas_essenciais:
        df = df[df[coluna].notna()]

    # Adicionar coluna 'ano' se ainda não existir
    if 'ano' not in df.columns:
        df['ano'] = ano

    # Resetar índice
    df = df.reset_index(drop=True)

    # Salvar o resultado se o caminho de saída for informado
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


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

    # Concatenar todos os dataframes
    df_final = pd.concat(dataframes, ignore_index=True)

    # Salvar o arquivo unificado
    df_final.to_csv(caminho_saida, index=False)
    print(f"[✔] Arquivo final salvo como: {caminho_saida} ({len(df_final)} linhas)")

    return df_final


if __name__ == '__main__':
    # tratar_dados_modelo_I("tabela_PBEV_2015.csv", "tabela_PBEV_2015_tratada.csv")
    # tratar_dados_modelo_I("tabela_PBEV_2016.csv", "tabela_PBEV_2016_tratada.csv")
    # tratar_dados_modelo_I("tabela_PBEV_2017.csv", "tabela_PBEV_2017_tratada.csv")
    # tratar_dados_modelo_I("tabela_PBEV_2018.csv", "tabela_PBEV_2018_tratada.csv")
    # tratar_dados_modelo_I("tabela_PBEV_2019.csv", "tabela_PBEV_2019_tratada.csv")
    # tratar_dados_modelo_I("tabela_PBEV_2020.csv", "tabela_PBEV_2020_tratada.csv")

    tratar_dados_modelo_III("tabela_PBEV_2021.csv", "tabela_PBEV_2021_tratada.csv")
    # tratar_dados_modelo_II("tabela_PBEV_2022.csv", "tabela_PBEV_2022_tratada.csv")
    # tratar_dados_modelo_II("tabela_PBEV_2023.csv", "tabela_PBEV_2023_tratada.csv")
    # tratar_dados_modelo_II("tabela_PBEV_2024.csv", "tabela_PBEV_2024_tratada.csv")
    # tratar_dados_modelo_II("tabela_PBEV_2025.csv", "tabela_PBEV_2025_tratada.csv")

    arquivos_tratados = [
        "tabela_PBEV_2015_tratada.csv",
        "tabela_PBEV_2016_tratada.csv",
        "tabela_PBEV_2017_tratada.csv",
        "tabela_PBEV_2018_tratada.csv",
        "tabela_PBEV_2019_tratada.csv",
        "tabela_PBEV_2020_tratada.csv",
        "tabela_PBEV_2021_tratada.csv",
        "tabela_PBEV_2022_tratada.csv",
        "tabela_PBEV_2023_tratada.csv",
        "tabela_PBEV_2024_tratada.csv",
        "tabela_PBEV_2025_tratada.csv"
    ]

    # unir_tabelas_tratadas(arquivos_tratados, "dados_tratados.csv")