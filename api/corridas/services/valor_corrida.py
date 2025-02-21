from decimal import Decimal
import asyncio


async def calcular_preco_km(distancia_km):
    """Calcula o preço baseado na distância percorrida em quilômetros."""
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal("10")  # km/litro
    margem_lucro = Decimal("0.50")  # R$/km

    distancia_km = Decimal(str(distancia_km))

    return await asyncio.to_thread(
        lambda: ((preco_combustivel / consumo_veiculo) + margem_lucro) * distancia_km
    )


async def calcular_valor_base(distancia_km):
    """Calcula o valor base da corrida considerando custos fixos."""
    preco_combustivel = Decimal("6")  # R$/litro
    consumo_veiculo = Decimal("10")  # km/litro
    margem_lucro = Decimal("0.50")  # R$/km
    taxa_manutencao = Decimal("2")  # R$

    distancia_km = Decimal(str(distancia_km))

    return await asyncio.to_thread(
        lambda: (((preco_combustivel / consumo_veiculo) + margem_lucro) * distancia_km) + taxa_manutencao
    )


async def calcular_preco_corrida(
        valor_base,
        taxa_noturna,
        taxa_pico,
        taxa_excesso_corridas,
        taxa_limpeza,
        taxa_cancelamento,
):
    """Calcula o preço final da corrida com base no valor base e nas taxas adicionais."""
    valor_base = Decimal(valor_base)
    taxa_noturna = Decimal(taxa_noturna)
    taxa_pico = Decimal(taxa_pico)
    taxa_excesso_corridas = Decimal(taxa_excesso_corridas)
    taxa_limpeza = Decimal(taxa_limpeza)
    taxa_cancelamento = Decimal(taxa_cancelamento)

    if taxa_cancelamento > 0:
        return taxa_cancelamento  # Prioriza a taxa de cancelamento, se houver

    return await asyncio.to_thread(
        lambda: valor_base + taxa_noturna + taxa_pico + taxa_excesso_corridas + taxa_limpeza
    )
