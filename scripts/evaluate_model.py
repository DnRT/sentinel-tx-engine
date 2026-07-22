import pandas as pd
import numpy as np
import joblib
import os
from sklearn.metrics import classification_report, confusion_matrix, f1_score

def evaluate_model():
    print("Iniciando evaluación del modelo K-Means...")
    
    # 1. Cargar el modelo entrenado
    app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app')
    model_path = os.path.join(app_dir, 'ml', 'tx_model.pkl')
    
    if not os.path.exists(model_path):
        print(f"Error: No se encontró el modelo en {model_path}. Entrena primero con train_kmeans.py")
        return
        
    model_data = joblib.load(model_path)
    kmeans = model_data['kmeans']
    scaler = model_data['scaler']
    weights = model_data['weights']
    cluster_mapping = model_data['cluster_mapping'] # 0: Fraude, 1: Sospechoso, 2: Seguro
    
    # 2. Generar un dataset de prueba (Test Set)
    np.random.seed(99) # Semilla diferente a la de entrenamiento
    n_samples = 500
    
    montos = np.random.exponential(scale=500, size=n_samples)
    confianza_origen = np.random.randint(0, 3, size=n_samples)
    nivel_confianza_destino = np.random.randint(0, 101, size=n_samples)
    
    df_test = pd.DataFrame({
        'monto': montos,
        'confianza_origen': confianza_origen,
        'nivel_confianza_destino': nivel_confianza_destino
    })
    
    # 3. Definir "Ground Truth" (La realidad para poder evaluar el IA)
    # Regla: Si origen es 0 -> Fraude (0). 
    #        Si origen es 2 y destino > 80 y monto < 2000 -> Seguro (2).
    #        Resto -> Sospechoso / Validación (1).
    def define_truth(row):
        if row['confianza_origen'] == 0:
            return 0 # Fraude
        elif row['confianza_origen'] == 2 and row['nivel_confianza_destino'] >= 80 and row['monto'] <= 2000:
            return 2 # Seguro
        else:
            return 1 # Sospechoso
            
    df_test['y_true'] = df_test.apply(define_truth, axis=1)
    
    # 4. Predecir con K-Means
    scaled_data = scaler.transform(df_test[['monto', 'confianza_origen', 'nivel_confianza_destino']])
    weighted_data = scaled_data.copy()
    weighted_data[:, 0] *= weights[0]
    weighted_data[:, 1] *= weights[1]
    weighted_data[:, 2] *= weights[2]
    
    predictions = kmeans.predict(weighted_data)
    # Mapear predicción al estado usando el cluster mapping
    df_test['y_pred'] = [cluster_mapping[p] for p in predictions]
    
    # Mapear a etiquetas legibles para el Excel
    label_map = {0: 'Fraude', 1: 'Sospechoso', 2: 'Seguro'}
    df_test['Clase_Real'] = df_test['y_true'].map(label_map)
    df_test['Clase_Predicha_KMeans'] = df_test['y_pred'].map(label_map)
    
    # 5. Guardar en Excel
    output_excel = os.path.join(os.path.dirname(__file__), 'resultados_evaluacion.xlsx')
    df_test.to_excel(output_excel, index=False)
    print(f"\n✅ Resultados detallados guardados en: {output_excel}")
    print("Puedes abrir este archivo en Excel para graficar y revisar fila por fila.")
    
    # 6. Calcular Métricas
    print("\n--- MATRIZ DE CONFUSIÓN ---")
    cm = confusion_matrix(df_test['y_true'], df_test['y_pred'], labels=[0, 1, 2])
    print(cm)
    
    print("\n--- REPORTE DE CLASIFICACIÓN (F1-SCORE) ---")
    report = classification_report(df_test['y_true'], df_test['y_pred'], target_names=['Fraude (0)', 'Sospechoso (1)', 'Seguro (2)'])
    print(report)
    
    f1_macro = f1_score(df_test['y_true'], df_test['y_pred'], average='macro')
    print(f"F1-Score (Macro Average): {f1_macro:.4f}")

if __name__ == "__main__":
    evaluate_model()
