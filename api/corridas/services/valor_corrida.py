from decimal import Decimal


def calcular_preco_km(distancia_km):
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal("10")  # km/litro
    margem_lucro = Decimal("0.50")  # R$/km

    # Converter distância para Decimal (caso não seja)
    distancia_km = Decimal(str(distancia_km))
    valor_km = (((preco_combustivel / consumo_veiculo) + margem_lucro) * distancia_km)
    return valor_km


def calcular_valor_base(distancia_km):
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal("10")  # km/litro
    margem_lucro = Decimal("0.50")  # R$/km
    taxa_manutencao = Decimal("2")  # R$

    distancia_km = Decimal(str(distancia_km))
    valor_base = (((preco_combustivel / consumo_veiculo) + margem_lucro) * distancia_km) + taxa_manutencao
    return valor_base


def calcular_preco_corrida(
        valor_base,
        taxa_noturna,
        taxa_pico,
        taxa_excesso_corridas,
        taxa_limpeza,
        taxa_cancelamento,
):
    """
    Calcula o preço final da corrida com base no valor base e nas taxas adicionais.
    """
    # Converter as taxas para Decimal, se necessário
    valor_base = Decimal(valor_base)
    taxa_noturna = Decimal(taxa_noturna)
    taxa_pico = Decimal(taxa_pico)
    taxa_excesso_corridas = Decimal(taxa_excesso_corridas)
    taxa_limpeza = Decimal(taxa_limpeza)
    taxa_cancelamento = Decimal(taxa_cancelamento)

    # Se a taxa de cancelamento estiver ativa, o valor final será o da taxa de cancelamento
    if taxa_cancelamento > 0:
        return taxa_cancelamento

    # Somar todas as taxas adicionais ao valor base
    preco_total = (
            valor_base
            + taxa_noturna
            + taxa_pico
            + taxa_excesso_corridas
            + taxa_limpeza
    )

    return preco_total
