# 🚗 Projeto Corridas

Este repositório contém tanto a API quanto os scripts necessários para o gerenciamento de corridas. Este README serve como um guia para configurar e executar o projeto corretamente.

---

## 🛠 Requisitos do Sistema

Certifique-se de ter instalado os seguintes softwares em sua máquina:

- **Python 3.12 ou superior**
- **MySQL Server**
- **Git**

Além disto, você precisará configurar variáveis de ambiente e dependências descritas nas seções abaixo.

---

## 📁 Configuração do Projeto

### 1. Clonando o Repositório

Para iniciar, clone este repositório e navegue até o diretório do projeto:


bash git clone [https://github.com/otilianojunior/projeto_corridas.git](https://github.com/otilianojunior/projeto_corridas.git) cd projeto_corridas


### 2. Configurando o Ambiente Virtual

Crie e ative um ambiente virtual para gerenciar as dependências de forma isolada.

#### No Windows:

bash python -m venv venv venv\Scripts\activate


#### No Linux/macOS:
bash python3 -m venv venv source venv/bin/activate

### 3. Instalando Dependências

Com o ambiente virtual ativado, instale as dependências do projeto listadas no arquivo `requirements.txt`:

bash pip install -r requirements.txt

---

## 💾 Configurando o Banco de Dados

### 1. Instalar o MySQL

- Baixe e instale o MySQL em sua máquina caso ele ainda não esteja configurado.
- Crie um banco de dados chamado `db_corridas`.
- Certifique-se de configurar um usuário com permissões e anote as credenciais.

### 2. Configurando o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (se ainda não existir) e insira as configurações de conexão ao banco. O formato padrão é o seguinte:
dotenv SQLALCHEMY_USER=root SQLALCHEMY_PASSWORD=12345678 SQLALCHEMY_HOST=localhost SQLALCHEMY_PORT=3306 SQLALCHEMY_DATABASE=db_corridas SQLALCHEMY_DATABASE_URL=mysql+mysqldb://root:12345678@localhost/db_corridas

Substitua os valores conforme suas configurações.

### 3. Configurando o Alembic (Migrações do Banco)

Se o Alembic ainda não estiver configurado no repositório, siga estas etapas:

- Inicialize o Alembic:
bash alembic init alembic

- Atualize o arquivo `alembic.ini` com sua URL do banco de dados:
ini sqlalchemy.url = mysql+mysqldb://root:12345678@localhost/db_corridas

- Aplique as migrações para criar as tabelas no banco de dados:
bash alembic upgrade head

Caso adicione alterações ao modelo, gere novas migrações e aplique novamente:
bash alembic revision --autogenerate -m "Descrição das modificações" alembic upgrade head

---

## 🚀 Executando o Projeto

### 1. Inicializar a API

Execute o servidor FastAPI utilizando o Uvicorn:
bash uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

- O servidor estará disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000).
- A documentação interativa estará em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Scripts e Simulações

Caso o projeto inclua scripts de simulação ou extração de dados, siga as instruções específicas desses scripts diretamente no repositório ou utilize os comandos fornecidos na documentação adicional.

---

## 🧪 Testando o Projeto

O projeto inclui testes automatizados utilizando o **pytest**. Para rodar todos os testes, utilize:
bash pytest

Certifique-se de configurar um banco de teste para evitar impactos em dados reais.

---

## 📚 Dependências Principais

### Módulos de API

- `fastapi`: Criação e execução de APIs.
- `uvicorn`: Servidor ASGI para rodar o FastAPI.

### Bancos de Dados

- `sqlalchemy`: ORM para interagir com o MySQL.
- `mysqlclient`: Driver para conectividade entre Python e MySQL.

### Dados e Mapas

- `osmnx`
- `networkx`
- `folium`
- `matplotlib`
- `pandas`
- Outros: Para análise de dados geoespaciais.

### Testes

- `pytest`: Framework para execução de testes.

---

## 🛠 Suporte

Caso tenha dúvidas ou encontre problemas, abra uma **issue** no repositório ou entre em contato com os mantenedores do projeto.

---