# Importa bibliotecas para manipulação de dados, cálculo numérico e machine learning
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor  # Modelo de IA escolhido
from sklearn.model_selection import train_test_split

# === 1. Carregar os dados simulados ===
# Lê um arquivo CSV com os dados das corridas simuladas, incluindo distância, taxas e valores calculados
df = pd.read_csv("../simulador/data/corridas/tb_corrida_202506101658.csv")

# === 2. Corrigir vírgulas e converter colunas numéricas ===
# Substitui vírgulas por pontos (caso números estejam em formato brasileiro) e converte para float
colunas = [
    "preco_total", "valor_motorista", "taxa_manutencao",
    "taxa_limpeza", "taxa_pico", "taxa_noturna", "taxa_excesso_corridas"
]
for col in colunas:
    df[col] = df[col].astype(str).str.replace(",", ".")  # troca vírgula por ponto
    df[col] = pd.to_numeric(df[col], errors="coerce")  # converte para número

# === 3. Limpar dados ===
# Remove linhas com valores ausentes nas colunas importantes para evitar erros no modelo
df = df.dropna(subset=colunas)

# === 4. Treinar modelo de ML (Machine Learning) para prever preco_total com base nas taxas ===
# Define as variáveis de entrada (features) e a saída (target)
features = [
    "taxa_manutencao", "taxa_limpeza", "taxa_pico",
    "taxa_noturna", "taxa_excesso_corridas"
]
target = "preco_total"

# Prepara os dados para treinamento
X = df[features]
y = df[target]

# Divide os dados em treino e teste para validar o modelo (20% teste por padrão)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

# Cria e treina o modelo de IA (Random Forest Regressor)
# Por que usar RandomForest?
# → É robusto, lida bem com não-linearidades e mistura de variáveis, e funciona bem sem normalização dos dados
modelo = RandomForestRegressor(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)  # treino do modelo


# === 5. Otimização: simular combinações válidas de taxas para encontrar a melhor ===

# Função auxiliar que sorteia um valor dentro de um intervalo de taxa
def gerar_taxa(intervalo):
    return round(np.random.uniform(intervalo[0], intervalo[1]), 4)


# Define os intervalos de cada taxa com base em regras internas ou limites testados
intervalos_taxas = {
    "taxa_manutencao": (0.30, 0.35),
    "taxa_limpeza": (0.95, 1.12),
    "taxa_pico": (0.70, 0.77),
    "taxa_noturna": (0.30, 0.56),
    "taxa_excesso_corridas": (0.27, 0.56)
}

# Inicializa variáveis para guardar a melhor simulação encontrada
melhor_preco = 0
melhor_config = {}

# Simula 10.000 cenários aleatórios com diferentes combinações de taxas
for _ in range(10000):
    # Gera uma combinação de taxas
    config = {k: gerar_taxa(v) for k, v in intervalos_taxas.items()}

    # Cria DataFrame com essa configuração e faz a previsão de preco_total usando o modelo IA
    entrada = pd.DataFrame([config])
    preco_estimado = modelo.predict(entrada)[0]

    # Calcula o valor para o motorista com base em 78% do valor estimado da corrida
    valor_motorista = preco_estimado * 0.78
    lucro = preco_estimado - valor_motorista

    # Verifica se essa simulação gerou um preco_total maior do que o atual melhor
    if preco_estimado > melhor_preco:
        melhor_preco = preco_estimado
        melhor_config = {
            **config,
            "preco_total": round(preco_estimado, 2),
            "valor_motorista (78%)": round(valor_motorista, 2),
            "lucro_plataforma (22%)": round(lucro, 2)
        }

# === 6. Exibir melhor resultado encontrado ===
# Ao final das 10.000 simulações, mostra a configuração de taxas que resultou no maior preço possível
# respeitando que 78% desse valor será destinado ao motorista

print("\n🚀 MELHOR CONFIGURAÇÃO DE TAXAS ENCONTRADA (pagando 78% ao motorista):")
for k, v in melhor_config.items():
    print(f"{k}: {v}")
