import pandas as pd
import numpy as np
import json
import time
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from pathlib import Path

# Início da contagem de tempo
inicio_execucao = time.time()

# Carregar os dados simulados
df = pd.read_csv("../data/ml/brutos/dataset_treino.csv")

# Corrigir vírgulas e converter colunas numéricas
colunas = [
    "preco_total", "valor_motorista", "taxa_manutencao",
    "taxa_limpeza", "taxa_pico", "taxa_noturna", "taxa_excesso_corridas"
]
for col in colunas:
    df[col] = df[col].astype(str).str.replace(",", ".")
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remover linhas com valores ausentes
df = df.dropna(subset=colunas)

# Features e target
features = [
    "taxa_manutencao", "taxa_limpeza", "taxa_pico",
    "taxa_noturna", "taxa_excesso_corridas"
]
target = "preco_total"
X = df[features]
y = df[target]

# Treinar modelo
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
modelo = RandomForestRegressor(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

# Função para gerar taxa aleatória
def gerar_taxa(intervalo):
    return round(np.random.uniform(intervalo[0], intervalo[1]), 4)

# Intervalos possíveis
intervalos_taxas = {
    "taxa_manutencao": (0.25, 0.35),
    "taxa_limpeza": (0.85, 1.0),
    "taxa_pico": (0.65, 0.70),
    "taxa_noturna": (0.25, 0.35),
    "taxa_excesso_corridas": (0.25, 0.35)
}

quantidade_simulacoes = 1000000
top_configs = []

for _ in range(quantidade_simulacoes):
    config = {k: gerar_taxa(v) for k, v in intervalos_taxas.items()}
    preco_estimado = modelo.predict(pd.DataFrame([config]))[0]
    resultado = {
        **config,
        "preco_total": round(preco_estimado, 2),
    }
    top_configs.append(resultado)

# Ordenar pelas melhores
top_configs_ordenadas = sorted(top_configs, key=lambda x: x["preco_total"], reverse=True)[:5]

# Converter para o formato com níveis
niveis = {
    i + 1: {
        "taxa_manutencao": round(config["taxa_manutencao"], 4),
        "taxa_limpeza": round(config["taxa_limpeza"], 4),
        "taxa_pico": round(config["taxa_pico"], 4),
        "taxa_noturna": round(config["taxa_noturna"], 4),
        "taxa_excesso_corridas": round(config["taxa_excesso_corridas"], 4)
    }
    for i, config in enumerate(top_configs_ordenadas)
}

# Mostrar
print("\n📊 TABELA DE NÍVEIS (1 a 5):\n")
for nivel, config in niveis.items():
    print(f"Nível {nivel}: {config}")

# Salvar como JSON
caminho_saida = Path("../data/ml/resultados/niveis_taxas_otimizadas.json")
caminho_saida.parent.mkdir(parents=True, exist_ok=True)
with open(caminho_saida, "w") as f:
    json.dump(niveis, f, indent=4)

# Fim da contagem de tempo
fim_execucao = time.time()
tempo_total = fim_execucao - inicio_execucao

# Exibir informações finais
print(f"\n Níveis salvos em: {caminho_saida}")
print(f"\n Tempo total de execução: {tempo_total:.2f} segundos")
print(f" Total de simulações realizadas: {quantidade_simulacoes}")