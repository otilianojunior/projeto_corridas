import argparse
import asyncio
import time

from simulador.inserir_carros import run_inserir_carros
from simulador.inserir_clientes import run_inserir_clientes
from simulador.inserir_motoristas import run_inserir_motoristas
from simulador.simular_taxas import executar_simulacao_taxas
from simulador.solicitar_corridas import executar_solicitacoes_corrida


# Função principal para executar a simulação completa de forma sequencial.
def main():
    parser = argparse.ArgumentParser(description="Executar simulação completa da API de Corridas")
    parser.add_argument("--carros", type=int, default=0, help="Quantidade de carros a serem cadastrados (None = todos)")
    parser.add_argument("--motoristas", type=int, default=0, help="Quantidade de motoristas a serem cadastrados")
    parser.add_argument("--clientes", type=int, default=0, help="Quantidade de clientes a serem cadastrados")
    parser.add_argument("--corridas", type=int, default=1, help="Quantidade de corridas a serem solicitadas")
    parser.add_argument("--taxas", type=int, default=1, help="Quantidade de corridas a aplicar taxas")
    args = parser.parse_args()

    print("\n🚀 Iniciando simulação completa...\n")
    inicio_geral = time.time()

    # Executa cada etapa da simulação
    carros_criados = run_inserir_carros(quantidade=args.carros)
    motoristas_criados = run_inserir_motoristas(total=args.motoristas)
    clientes_criados = run_inserir_clientes(total=args.clientes)
    corridas_criadas = asyncio.run(executar_solicitacoes_corrida(args.corridas))
    corridas_taxadas = asyncio.run(executar_simulacao_taxas(args.taxas))

    # Calcula o tempo total da simulação
    duracao_total = time.time() - inicio_geral
    minutos, segundos = divmod(duracao_total, 60)

    # Exibe o resumo da simulação
    print("\n✅ Simulação finalizada com sucesso!")
    print(f"✔️ Carros: {carros_criados}, Clientes: {clientes_criados}, Motoristas: {motoristas_criados}")
    print(f"✔️ Corridas: {corridas_criadas}, Taxas aplicadas: {corridas_taxadas}")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.\n")


if __name__ == "__main__":
    main()
