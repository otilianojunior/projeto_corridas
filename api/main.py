import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# ROTAS
from corridas.routers import corridas_routers
from mapas_rotas.routers import mapas_routers
from clientes.routers import clientes_routers
from motoristas.routers import motoristas_routers
from carros.routers import carros_router

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
app.include_router(Carros.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
