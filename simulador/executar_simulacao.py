import argparse
import time
import asyncio

from simulador.inserir_carros import run_inserir_carros
from simulador.inserir_motoristas import run_inserir_motoristas
from simulador.inserir_clientes import run_inserir_clientes
from simulador.solicitar_corridas import executar_solicitacoes_corrida
from simulador.simular_taxas import executar_simulacao_taxas

def main():
    parser = argparse.ArgumentParser(description="Executar simulação completa da API de Corridas")
    parser.add_argument("--carros", type=int, default=None, help="Quantidade de carros a serem cadastrados (None = todos)")
    parser.add_argument("--motoristas", type=int, default=20, help="Quantidade de motoristas a serem cadastrados")
    parser.add_argument("--clientes", type=int, default=40, help="Quantidade de clientes a serem cadastrados")
    parser.add_argument("--corridas", type=int, default=10, help="Quantidade de corridas a serem solicitadas")
    parser.add_argument("--taxas", type=int, default=5, help="Quantidade de corridas a aplicar taxas")
    args = parser.parse_args()

    print("\n🚀 Iniciando simulação completa...\n")
    inicio_geral = time.time()
    carros_criados = run_inserir_carros(quantidade=args.carros)
    motoristas_criados = run_inserir_motoristas(total=args.motoristas)
    clientes_criados = run_inserir_clientes(total=args.clientes)
    corridas_criadas = asyncio.run(executar_solicitacoes_corrida(args.corridas))
    corridas_taxadas = asyncio.run(executar_simulacao_taxas(args.taxas))

    duracao_total = time.time() - inicio_geral
    minutos, segundos = divmod(duracao_total, 60)

    print("\n✅ Simulação finalizada com sucesso!")
    print(f"✔️ Carros: {carros_criados}, Clientes: {clientes_criados}, Motoristas: {motoristas_criados}")
    print(f"✔️ Corridas: {corridas_criadas}, Taxas aplicadas: {corridas_taxadas}")
    print(f"⏱️ Tempo total: {int(minutos)} min {segundos:.2f} seg.\n")

if __name__ == "__main__":
    main()
