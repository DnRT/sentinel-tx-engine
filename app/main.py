from fastapi import FastAPI
from .database import engine, Base
from .routers import pagos

# Crear las tablas en la BD (para PoC está bien, en prod usar Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sentinel TX Engine",
    description="Motor de Decisión de Transacciones Contextuales basado en Reglas de Confianza.",
    version="1.0.0"
)

# Incluir rutas
app.include_router(pagos.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a Sentinel TX Engine API"}
