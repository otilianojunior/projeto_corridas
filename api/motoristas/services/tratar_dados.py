import pandas as pd


def tratar_arquivo_modelo_I(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    # Carrega o arquivo
    df = pd.read_csv(caminho_entrada)

    # Remove linhas vazias
    df = df.dropna(how='all')

    # Remove linhas com cabeçalhos repetidos
    df = df[~df['marca'].isin(['Marca(?)'])]

    # Corrige a coluna 'categoria' com valores da última coluna, se necessário
    df['categoria'] = df['categoria'].fillna(df['Unnamed: 14'])

    # Remove coluna desnecessária
    df = df.drop(columns=['Unnamed: 14'])

    # Remove linhas com dados essenciais ausentes
    colunas_essenciais = ['marca', 'modelo', 'motor', 'versao']
    for coluna in colunas_essenciais:
        df = df[df[coluna].notna()]

    # Resetar índice
    df = df.reset_index(drop=True)

    # Salvar, se necessário
    if caminho_saida:
        df.to_csv(caminho_saida, index=False)

    return df


import pandas as pd


def tratar_arquivo_modelo_II(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    """
    Lê, trata e retorna um DataFrame limpo para arquivos com estrutura modelo II (ex: PBEV 2017).

    Parâmetros:
    - caminho_entrada: str -> Caminho do arquivo CSV original.
    - caminho_saida: str -> Caminho do arquivo CSV tratado (opcional).

    Retorna:
    - pd.DataFrame com os dados tratados.
    """
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


if __name__ == '__main__':
    tratar_arquivo_modelo_I("tabela_PBEV_2015.csv", "tabela_PBEV_2015_tratada.csv")
    tratar_arquivo_modelo_I("tabela_PBEV_2016.csv", "tabela_PBEV_2016_tratada.csv")
    tratar_arquivo_modelo_II("tabela_PBEV_2017.csv", "tabela_PBEV_2017_tratada.csv")
