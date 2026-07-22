from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    dispositivos = relationship("DispositivoConfiable", back_populates="usuario")
    ips = relationship("IPConfiable", back_populates="usuario")
    transacciones = relationship("Transaccion", back_populates="usuario")

class DispositivoConfiable(Base):
    __tablename__ = "dispositivos_confiables"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    hardware_id = Column(String, index=True)
    es_confiable = Column(Boolean, default=True)
    fecha_ultimo_uso = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="dispositivos")

class IPConfiable(Base):
    __tablename__ = "ips_confiables"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    direccion_ip = Column(String, index=True)
    es_confiable = Column(Boolean, default=True)
    fecha_ultimo_uso = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="ips")

class CuentaDestino(Base):
    __tablename__ = "cuentas_destino"

    id = Column(Integer, primary_key=True, index=True)
    numero_cuenta = Column(String, unique=True, index=True)
    nombre_titular = Column(String)
    tipo = Column(String) # 'Institucion Educativa', 'Comercio', 'Particular'
    nivel_confianza = Column(Integer, default=50) # 0-100 (100 = Máxima confianza)

class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    monto = Column(Float)
    cuenta_destino = Column(String, ForeignKey("cuentas_destino.numero_cuenta"))
    estado = Column(String) # 'APROBADA', 'DECLINADA', 'REQUIERE_VALIDACION'
    razon_estado = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)
    ip_origen = Column(String)
    hardware_id_origen = Column(String)
    score_riesgo_calculado = Column(Float)

    usuario = relationship("Usuario", back_populates="transacciones")
    cuenta = relationship("CuentaDestino")
