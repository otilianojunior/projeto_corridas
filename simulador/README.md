# Documentação do Simulador de Corridas

Este projeto contém um simulador completo para gerenciar uma API de corridas, incluindo cadastramento de carros, motoristas, clientes, solicitação de corridas e aplicação de taxas.

---

## Estrutura dos Arquivos

### **1. `executar_simulacao.py`**
Esta é a entrada principal do simulador. Ele organiza e executa todas as etapas da simulação de forma sequencial:
- **Cadastro de carros** (`inserir_carros.py`)
- **Cadastro de motoristas** (`inserir_motoristas.py`)
- **Cadastro de clientes** (`inserir_clientes.py`)
- **Solicitação de corridas** (`solicitar_corridas.py`)
- **Simulação de taxas em corridas concluídas** (`simular_taxas.py`)

#### Principais Funções:
- **`main()`**: Processa os argumentos fornecidos no terminal e executa todas as etapas da simulação, exibindo um resumo final ao usuário.

---

### **2. `inserir_carros.py`**

Este arquivo é usado para cadastrar carros a partir de dados previamente tratados em um arquivo CSV.

#### Principais Funções:
- **`verificar_ou_gerar_csv()`**: Verifica se o arquivo CSV contendo os dados dos carros existe no sistema. Caso contrário, gera o arquivo utilizando scripts externos.
- **`gerar_dados_carro()`**: Converte uma linha do arquivo CSV em um dicionário.
- **`cadastrar_carros()`**: Envia os dados de cada carro para a API via `POST`.
- **`run_inserir_carros()`**: Executa todo o fluxo de validação e cadastramento de carros.

---

### **3. `inserir_motoristas.py`**

Responsável por cadastrar motoristas fictícios na API utilizando a biblioteca Faker.

#### Principais Funções:
- **`formatar_cpf()`**: Formata o CPF gerado pelo Faker.
- **`gerar_dados_motorista()`**: Cria os dados de um motorista (nome, CPF, telefone, email, status).
- **`criar_motoristas()`**: Faz chamadas `POST` para a API, cadastrando motoristas aleatórios.
- **`run_inserir_motoristas()`**: Executa o processo de cadastro de motoristas e exibe os resultados.

---

### **4. `inserir_clientes.py`**

Semelhante ao script de motoristas, mas com foco no cadastramento de clientes na API.

#### Principais Funções:
- **`formatar_cpf()`**: Formata o CPF dos clientes.
- **`gerar_dados_cliente()`**: Gera dados fictícios de clientes com bibliotecas como o Faker.
- **`criar_clientes()`**: Faz as requisições `POST` para a API para cadastrar os clientes.
- **`run_inserir_clientes()`**: Controla a sequência do processo e exibe um resumo final.

---

### **5. `solicitar_corridas.py`**

É usado para realizar solicitações automáticas de corridas na API, associando motoristas e clientes aleatórios.

#### Principais Funções:
- **`executar_solicitacoes_corrida()`**: Faz um número definido de solicitações de corridas entre motoristas e clientes registrados, gerando dados de origem/destino.

---

### **6. `simular_taxas.py`**

Introduz taxas adicionais (ex.: taxa noturna, taxa de manutenção, etc.) em corridas previamente cadastradas.

#### Principais Funções:
- **`executar_simulacao_taxas()`**: Aplica condições de taxas baseadas em regras, atualizando os dados das corridas cadastradas.

---

## Modelos

Os modelos representam a estrutura de dados armazenada no banco de dados.

### **1. `carro_model.py`**
O modelo `CarroModel` representa os detalhes sobre os carros cadastrados, incluindo:
- **Atributos:** `marca`, `modelo`, `transmissao`, `ar_condicionado`, `direcao`, entre outros.
- **Relacionamentos:** Associa o carro com motoristas via a tabela de motoristas.

---

### **2. `corrida_model.py`**
O modelo `CorridaModel` mapeia os dados de uma corrida, incluindo:
- **Localizações:** Origem e destino da corrida (incluindo latitude/longitude e bairros).
- **Taxas:** Representadas separadamente (noturna, pico, limpeza, etc.).
- **Relacionamentos:** Relaciona-se ao cliente e ao motorista da corrida pelo ID.

---

## Rotas da API

### **Arquivo: `carros_router.py`**
Define as operações relacionadas aos carros na API (CRUD):
- **`/listar/`**: Lista todos os carros cadastrados.
- **`POST /`**: Cria um novo carro.
- **`PUT /{carro_id}`**: Atualiza os dados de um carro existente.
- **`DELETE /{carro_id}`**: Remove um carro da base de dados.

---

## Outras Partes Importantes

### **1. `dependencies.py`**
Fornece a dependência para obter uma instância do banco de dados (sessões assíncronas usando SQLAlchemy).

### **2. `__init__.py`**
Arquivo de inicialização do pacote utilizado para organização do projeto.

---

## Como Executar

### **Passo 1: Configuração do Ambiente**
1. Clone o repositório: