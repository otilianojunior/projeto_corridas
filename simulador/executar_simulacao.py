import subprocess
import argparse

parser = argparse.ArgumentParser(description="Executar simulação completa da API de Corridas")
parser.add_argument("--motoristas", type=int, default=10, help="Quantidade de motoristas a serem cadastrados")
parser.add_argument("--clientes", type=int, default=500, help="Quantidade de clientes a serem cadastrados")
parser.add_argument("--corridas", type=int, default=20, help="Quantidade de corridas a serem solicitadas")
parser.add_argument("--taxas", type=int, default=20, help="Quantidade de corridas a aplicar taxas")

args = parser.parse_args()

print("\n🚀 Iniciando simulação completa...")

# Inserir todos os carros do CSV
def executar_insercao_carros():
    print("\n🚗 Inserindo todos os carros do CSV...")
    subprocess.run(["python", "simulador/inserir_carros.py"])

# Inserir clientes
def executar_insercao_clientes():
    print("\n👥 Inserindo clientes...")
    subprocess.run([
        "python", "simulador/inserir_clientes.py",
        "--clientes", str(args.clientes)
    ])

# Inserir motoristas
def executar_insercao_motoristas():
    print("\n🧍 Inserindo motoristas...")
    subprocess.run([
        "python", "simulador/inserir_motoristas.py",
        "--motoristas", str(args.motoristas)
    ])

# Solicitar corridas
def executar_solicitacao_corridas():
    print("\n🚕 Solicitando corridas...")
    subprocess.run([
        "python", "simulador/solicitar_corridas.py",
        "--corridas", str(args.corridas)
    ])

# Aplicar taxas
def executar_simulacao_taxas():
    print("\n💸 Aplicando taxas...")
    subprocess.run([
        "python", "simulador/simular_taxas.py",
        "--taxas", str(args.taxas)
    ])

# Executa a sequência completa
executar_insercao_carros()
executar_insercao_clientes()
executar_insercao_motoristas()
executar_solicitacao_corridas()
executar_simulacao_taxas()

print("\n✅ Simulação finalizada com sucesso!")
