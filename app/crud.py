from sqlalchemy.orm import Session
from . import models, schemas

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_dispositivo_confiable(db: Session, usuario_id: int, hardware_id: str):
    return db.query(models.DispositivoConfiable).filter(
        models.DispositivoConfiable.usuario_id == usuario_id,
        models.DispositivoConfiable.hardware_id == hardware_id,
        models.DispositivoConfiable.es_confiable == True
    ).first()

def get_ip_confiable(db: Session, usuario_id: int, direccion_ip: str):
    return db.query(models.IPConfiable).filter(
        models.IPConfiable.usuario_id == usuario_id,
        models.IPConfiable.direccion_ip == direccion_ip,
        models.IPConfiable.es_confiable == True
    ).first()

def obtener_o_crear_cuenta_destino(db: Session, numero_cuenta: str):
    cuenta = db.query(models.CuentaDestino).filter(models.CuentaDestino.numero_cuenta == numero_cuenta).first()
    if not cuenta:
        nueva_cuenta = models.CuentaDestino(
            numero_cuenta=numero_cuenta,
            nombre_titular="Desconocido",
            tipo="Desconocida",
            nivel_confianza=0
        )
        db.add(nueva_cuenta)
        db.commit()
        db.refresh(nueva_cuenta)
        return nueva_cuenta
    return cuenta

def crear_transaccion(db: Session, transaccion: models.Transaccion):
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion
