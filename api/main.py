import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# ROTAS
from corridas.routers import Corridas
from mapas.routers import Mapas
from clientes.routers import Clientes
from motoristas.routers import Motoristas

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="API de Corridas",
    description="API para gerenciamento de corridas, motoristas e clientes.",
    version="1.0.0"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Função de gerenciamento do ciclo de vida da aplicação"""
    print("🚀 Aplicação iniciando...")
    yield  # Aqui fica o ponto de execução principal da API
    print("🛑 Aplicação sendo encerrada...")


# Criar a aplicação FastAPI com o novo Lifespan
app = FastAPI(lifespan=lifespan)

# Incluir rotas
app.include_router(Corridas.router)
app.include_router(Mapas.router)
app.include_router(Clientes.router)
app.include_router(Motoristas.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
