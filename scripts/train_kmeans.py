import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os

def train_and_save_model():
    print("Generando dataset sintético de entrenamiento...")
    
    # 1. Generar Dataset Sintético
    np.random.seed(42)
    n_samples = 1000
    
    # Features base
    montos = np.random.exponential(scale=500, size=n_samples) # Montos exponenciales, muchos pequeños, pocos grandes
    confianza_origen = np.random.randint(0, 3, size=n_samples) # 0: Nada (fraude), 1: Parcial (ip o dispositivo), 2: Confiable (ambos)
    nivel_confianza_destino = np.random.randint(0, 101, size=n_samples) # 0 a 100
    
    df = pd.DataFrame({
        'monto': montos,
        'confianza_origen': confianza_origen,
        'nivel_confianza_destino': nivel_confianza_destino
    })

    # 2. Aplicar los pesos específicos solicitados por el usuario
    # - Monto: peso 1
    # - Origen (Dispositivo/IP): peso 3
    # - Destino: peso 2
    
    peso_monto = 1
    peso_origen = 3
    peso_destino = 2
    
    # Escalamos todo para que estén en la misma magnitud (StandardScaler lo lleva a media 0, varianza 1)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    
    # Aplicamos los pesos matemáticamente multiplicando la feature escalada por su peso
    # Col 0: monto, Col 1: origen, Col 2: destino
    weighted_data = scaled_data.copy()
    weighted_data[:, 0] *= peso_monto
    weighted_data[:, 1] *= peso_origen
    weighted_data[:, 2] *= peso_destino
    
    print(f"Pesos aplicados -> Monto: {peso_monto}x, Origen: {peso_origen}x, Destino: {peso_destino}x")
    
    # 3. Entrenamiento de K-Means
    print("Entrenando modelo K-Means con 3 clusters (Seguro, Sospechoso, Riesgoso)...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(weighted_data)
    
    df['cluster'] = kmeans.labels_
    
    # Analizamos qué significa cada cluster para asignarles etiquetas consistentes
    # Calculamos la media de 'confianza_origen' en cada cluster para deducir cuál es el riesgoso (menor confianza origen)
    cluster_origen_means = df.groupby('cluster')['confianza_origen'].mean()
    
    # Ordenar los clusters de menor a mayor confianza de origen
    # Cluster 0 -> Mayor Riesgo (Menor confianza)
    # Cluster 1 -> Riesgo Medio
    # Cluster 2 -> Seguro (Mayor confianza)
    sorted_clusters = cluster_origen_means.sort_values().index.tolist()
    
    # Creamos un mapeo para estandarizar los números de clusters en la API
    # 2 = Seguro, 1 = Revisar, 0 = Declinado
    cluster_mapping = {
        sorted_clusters[0]: 0, # Peor origen -> Declinado (Fraude)
        sorted_clusters[1]: 1, # Origen medio -> Requiere validación
        sorted_clusters[2]: 2  # Mejor origen -> Seguro
    }
    
    # Guardamos los modelos y metadatos
    app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app')
    ml_dir = os.path.join(app_dir, 'ml')
    os.makedirs(ml_dir, exist_ok=True)
    
    model_data = {
        'kmeans': kmeans,
        'scaler': scaler,
        'weights': [peso_monto, peso_origen, peso_destino],
        'cluster_mapping': cluster_mapping
    }
    
    model_path = os.path.join(ml_dir, 'tx_model.pkl')
    joblib.dump(model_data, model_path)
    
    print(f"Modelo guardado exitosamente en: {model_path}")
    
    # Pequeño reporte para el log
    for c in range(3):
        mapped_c = cluster_mapping[c]
        estado = "SEGURO" if mapped_c == 2 else "SOSPECHOSO" if mapped_c == 1 else "FRAUDE"
        subset = df[df['cluster'] == c]
        print(f"Cluster original {c} (Mapeado a {mapped_c} - {estado}): "
              f"Media Origen={subset['confianza_origen'].mean():.2f}, "
              f"Media Destino={subset['nivel_confianza_destino'].mean():.2f}, "
              f"Media Monto=${subset['monto'].mean():.2f}")

if __name__ == "__main__":
    train_and_save_model()
