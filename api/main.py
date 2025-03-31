import uvicorn
from fastapi import FastAPI

from carros.routers import carros_router
from clientes.routers import clientes_router
from corridas.routers import corridas_router
from mapas_rotas.routers import mapas_router
from motoristas.routers import motoristas_router

app = FastAPI(
    title="API de Corridas",
    description="API para gerenciamento de corridas, motoristas, clientes e mapas.",
    version="1.0.0",
)

app.include_router(mapas_router.router)
app.include_router(carros_router.router)
app.include_router(motoristas_router.router)
app.include_router(clientes_router.router)
app.include_router(corridas_router.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
