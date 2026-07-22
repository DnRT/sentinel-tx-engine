from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransaccionRequest(BaseModel):
    usuario_id: int
    monto: float = Field(..., gt=0)
    cuenta_destino: str
    ip_origen: str
    hardware_id: str

class TransaccionResponse(BaseModel):
    estado: str
    razon_estado: str
    monto: float
    score_riesgo_calculado: float
    cuenta_destino: str

class UsuarioBase(BaseModel):
    nombre: str
    email: str

class CuentaDestinoBase(BaseModel):
    numero_cuenta: str
    nombre_titular: str
    tipo: str
    nivel_confianza: int
