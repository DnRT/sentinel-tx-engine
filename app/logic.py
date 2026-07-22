from sqlalchemy.orm import Session
from . import crud, models, schemas
import joblib
import os
import numpy as np

# Cargar modelo al iniciar (si existe)
model_path = os.path.join(os.path.dirname(__file__), 'ml', 'tx_model.pkl')
try:
    model_data = joblib.load(model_path)
    kmeans = model_data['kmeans']
    scaler = model_data['scaler']
    weights = model_data['weights']
    cluster_mapping = model_data['cluster_mapping']
    IA_READY = True
except Exception as e:
    print(f"Advertencia: Modelo ML no encontrado o error al cargar ({e}). Se usará modo degradado (rechazo por defecto).")
    IA_READY = False

def evaluar_transaccion(db: Session, request: schemas.TransaccionRequest) -> models.Transaccion:
    razon = []
    
    # 1. Obtener Features
    dispositivo = crud.get_dispositivo_confiable(db, request.usuario_id, request.hardware_id)
    ip_conocida = crud.get_ip_confiable(db, request.usuario_id, request.ip_origen)
    
    # Confianza origen: 0 (nada), 1 (parcial), 2 (total)
    confianza_origen = (1 if dispositivo else 0) + (1 if ip_conocida else 0)
    if dispositivo: razon.append("Dispositivo OK")
    if ip_conocida: razon.append("IP OK")
    if confianza_origen == 0: razon.append("Origen Desconocido")
    
    # Obtener o Auto-crear cuenta destino
    cuenta = crud.obtener_o_crear_cuenta_destino(db, request.cuenta_destino)
    nivel_confianza_destino = cuenta.nivel_confianza
    
    if cuenta.tipo == 'Desconocida':
        razon.append("Cuenta auto-registrada (Desconocida).")
    else:
        razon.append(f"Destino: {cuenta.tipo} ({nivel_confianza_destino}% conf).")

    score_final = 0
    estado = "DECLINADA"

    if IA_READY:
        # 2. Preparar el vector para el modelo [monto, confianza_origen, nivel_confianza_destino]
        feature_vector = np.array([[request.monto, confianza_origen, nivel_confianza_destino]])
        
        # Escalar
        scaled_vector = scaler.transform(feature_vector)
        
        # Aplicar pesos (Monto x1, Origen x3, Destino x2)
        weighted_vector = scaled_vector.copy()
        weighted_vector[:, 0] *= weights[0]
        weighted_vector[:, 1] *= weights[1]
        weighted_vector[:, 2] *= weights[2]
        
        # 3. Predicción del Cluster
        cluster_pred = kmeans.predict(weighted_vector)[0]
        riesgo_mapped = cluster_mapping[cluster_pred] # 0: Fraude, 1: Riesgo Medio, 2: Seguro
        
        if riesgo_mapped == 2:
            estado = "APROBADA"
            score_final = 90
            razon.append("[IA-KMeans] Clasificado: SEGURO.")
        elif riesgo_mapped == 1:
            estado = "REQUIERE_VALIDACION"
            score_final = 50
            razon.append("[IA-KMeans] Clasificado: RIESGO MEDIO.")
        else:
            estado = "DECLINADA"
            score_final = 10
            razon.append("[IA-KMeans] Clasificado: FRAUDE (Alto Riesgo).")
    else:
        razon.append("IA NO DISPONIBLE. Transacción declinada por seguridad.")

    # 4. Registrar en Historial
    tx = models.Transaccion(
        usuario_id=request.usuario_id,
        monto=request.monto,
        cuenta_destino=request.cuenta_destino,
        estado=estado,
        razon_estado=" | ".join(razon),
        ip_origen=request.ip_origen,
        hardware_id_origen=request.hardware_id,
        score_riesgo_calculado=score_final
    )
    
    return crud.crear_transaccion(db, tx)
