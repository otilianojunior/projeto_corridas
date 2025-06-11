
---

# Projeto Corridas  

Este repositório contém a API e o script de simulação para gerenciamento de corridas.  

## Clonando o Repositório  

Para começar, clone este repositório em sua máquina:  

```bash
git clone https://github.com/otilianojunior/projeto_corridas.git
cd projeto_corridas
```

## Criando e Ativando o Ambiente Virtual  

Antes de instalar as dependências, é recomendável criar e ativar um ambiente virtual para isolar as bibliotecas do projeto.  

### No Windows (cmd/powershell):  

```bash
python -m venv venv
venv\Scripts\activate
```

### No Linux/macOS (bash/zsh):  

```bash
python3 -m venv venv
source venv/bin/activate
```

## Instalando as Dependências  

Com o ambiente virtual ativado, instale todas as dependências listadas no `requirements.txt`:  

```bash
pip install -r requirements.txt
```

---

## Configuração do Alembic  

O **Alembic** é usado para gerenciar as migrações do banco de dados neste projeto.  

### Inicializando o Alembic  

Antes de rodar as migrações, é necessário inicializar o Alembic. Caso ainda não tenha sido inicializado, use o seguinte comando:  

```bash
alembic init alembic
```

Isso criará a estrutura necessária para gerenciar as migrações.  

### Configurando o `alembic.ini`  

Para conectar o Alembic ao banco de dados corretamente, edite o arquivo `alembic.ini` e configure a URL do banco de dados na linha:  

```
sqlalchemy.url = sqlite:///./database.db  # Exemplo usando SQLite
```

Se estiver usando PostgreSQL ou outro banco, substitua pela URL correspondente, como:  

```
sqlalchemy.url = postgresql+asyncpg://usuario:senha@localhost:5432/nome_do_banco
```

### Configurando o `env.py`  

Para configurar corretamente o **Alembic**, utilize o arquivo de exemplo `env_example_alembic.py` para criar o `env.py`:  

```bash
cp alembic/env_example_alembic.py alembic/env.py
```

Edite o arquivo `alembic/env.py`, se necessário, para garantir que está buscando a URL do banco corretamente.

### Aplicando as Migrações  

Após a configuração, crie as tabelas no banco de dados executando:  

```bash
alembic upgrade head
```

Caso precise criar novas migrações após modificar os modelos, use:  

```bash
alembic revision --autogenerate -m "Descrição da mudança"
alembic upgrade head
```
