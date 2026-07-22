import sys
import os
import json

# Agregar el directorio principal al sys.path para importar app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models

def seed_database():
    print("Iniciando poblado de la base de datos...")
    
    # Crear tablas si no existen
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        with open(os.path.join(os.path.dirname(__file__), 'seed_data.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Limpiar datos anteriores (opcional, cuidado en prod)
        db.query(models.Historial_Transaccion).delete() if hasattr(models, 'Historial_Transaccion') else None
        db.query(models.Transaccion).delete()
        db.query(models.DispositivoConfiable).delete()
        db.query(models.IPConfiable).delete()
        db.query(models.CuentaDestino).delete()
        db.query(models.Usuario).delete()
        db.commit()

        # Insertar Usuarios
        for u in data.get('usuarios', []):
            u.pop('id', None)
            usuario = models.Usuario(**u)
            db.add(usuario)
        
        # Insertar Dispositivos
        for d in data.get('dispositivos_confiables', []):
            d.pop('id', None)
            dispositivo = models.DispositivoConfiable(**d)
            db.add(dispositivo)
            
        # Insertar IPs
        for i in data.get('ips_confiables', []):
            i.pop('id', None)
            ip = models.IPConfiable(**i)
            db.add(ip)
            
        # Insertar Cuentas Destino
        for c in data.get('cuentas_destino', []):
            c.pop('id', None)
            cuenta = models.CuentaDestino(**c)
            db.add(cuenta)
            
        db.commit()
        print("¡Base de datos poblada exitosamente!")
        
    except Exception as e:
        print(f"Error poblando la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
