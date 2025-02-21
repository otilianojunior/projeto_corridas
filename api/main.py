import uvicorn
from fastapi import FastAPI

# ROTAS
from corridas.routers import Corridas
from mapas.routers import Mapas
from clientes.routers import Clientes
from motoristas.routers import Motoristas

app = FastAPI()

app.include_router(Corridas.router)
app.include_router(Mapas.router)
app.include_router(Clientes.router)
app.include_router(Motoristas.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
