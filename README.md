# Sentinel TX Engine (AI-Powered)

> [!WARNING]
> **Prueba de Concepto (PoC)**: Este proyecto ha sido diseñado como una prueba de concepto para demostrar algoritmos de decisión contextuales y aprendizaje no supervisado. **NO utiliza datos bancarios reales**, opera con datasets sintéticos generados programáticamente y su estructura de base de datos relacional está altamente simplificada. Los sistemas bancarios reales poseen arquitecturas distribuidas, esquemas de datos mucho más robustos (ej: event-sourcing, arquitecturas en malla) y regulaciones estrictas de privacidad (PCI-DSS).

Motor de Decisión de Transacciones Contextuales inteligente diseñado para validar pagos evaluando el "Trust Score" de una transacción mediante el uso de aprendizaje no supervisado (K-Means). En lugar de basarse en reglas estáticas de bloqueo por montos altos (que a menudo causan falsos positivos en pagos legítimos como matrículas universitarias), el motor clasifica el nivel de riesgo en base a métricas ponderadas.

## 🚀 Arquitectura y Tecnologías
- **Backend**: Python, FastAPI.
- **Base de Datos**: PostgreSQL (con auto-registro de entidades desconocidas).
- **Machine Learning**: Scikit-Learn (K-Means Clustering).
- **Despliegue**: Docker & Docker Compose.

## 📊 Modelo K-Means y Evaluación
El modelo evalúa las transacciones ponderando tres características principales bajo la siguiente lógica de seguridad:
1. **Origen (IP + Dispositivo)**: Peso `x3` (El factor más vulnerable).
2. **Destino (Nivel de confianza de la cuenta)**: Peso `x2` (Indicio de legitimidad).
3. **Monto**: Peso `x1` (El monto por sí solo no determina el fraude si el contexto es altamente seguro).

### Rendimiento (F1-Score y Matriz de Confusión)
Se ha generado un script de evaluación (`scripts/evaluate_model.py`) que enfrenta las predicciones del modelo no supervisado contra un "Ground Truth" lógico predefinido. 

**Resultados Actuales (Dataset de Prueba N=500)**:
- **F1-Score (Macro Average)**: `0.6860`
- **F1-Score por Clase**:
  - `Fraude (0)`: 1.00 *(Precisión perfecta detectando fraude claro)*
  - `Sospechoso (1)`: 0.74
  - `Seguro (2)`: 0.32 *(El modelo es estricto y conservador para clasificar algo como completamente seguro)*

**Matriz de Confusión**:
```text
[[161   0   0]
 [  0 181 128]
 [  0   0  30]]
```
*Interpretación: De los casos clasificados como Fraude Real (Fila 1), el modelo detectó los 161 correctamente sin falsos negativos. Existe un solapamiento entre lo que es 'Sospechoso' y 'Seguro', lo cual es ideal en sistemas financieros (preferimos marcar algo seguro como sospechoso para pedir un SMS de validación, que dejar pasar un fraude).*

### 📁 Revisión Granular (Excel)
Al ejecutar la evaluación, se genera un archivo `resultados_evaluacion.xlsx` en la carpeta `scripts/`. Puedes abrir este archivo para graficar las desviaciones, revisar los falsos positivos fila por fila, y ajustar los pesos del algoritmo.

## 🛠️ Cómo Ejecutar

1. **Levantar la Infraestructura**:
```bash
docker-compose up -d --build
```

2. **Poblar la Base de Datos Inicial**:
```bash
docker-compose exec api python scripts/seed_db.py
```

3. **Re-entrenar el Modelo K-Means**:
```bash
docker-compose exec api python scripts/train_kmeans.py
```

4. **Ejecutar la Evaluación (Métricas y Excel)**:
```bash
docker-compose exec api python scripts/evaluate_model.py
```

## 🌐 Endpoints Principales
- `POST /api/v1/validar_pago`: Recibe un payload JSON con `monto`, `cuenta_destino`, `ip_origen` y `hardware_id`. Retorna la clasificación de la IA (Aprobada, Requiere Validación, Declinada).

## 📈 Rendimiento y Pruebas de Estrés (Requisitos del Sistema)

Al tratarse de un motor de validación en tiempo real (crítico para la experiencia del usuario), el rendimiento bajo concurrencia es vital. A continuación se presentan los requisitos técnicos según la demanda de la red:

### Resultados Reales en Desarrollo (PoC)
Para demostrar el comportamiento del sistema bajo su actual esquema sincrónico local, se ha ejecutado una prueba de estrés escalonada contra la API (Uvicorn + FastAPI + SQLAlchemy Sync).

| Peticiones Totales | Concurrencia | Tiempo Total | Transacciones/Seg (RPS) | Tasa de Éxito |
|--------------------|--------------|--------------|-------------------------|---------------|
| 1,000              | 10           | 9.95 seg     | 100.49 RPS              | 100%          |
| 5,000              | 20           | 46.97 seg    | 106.46 RPS              | 100%          |
| 10,000             | 30           | 92.86 seg    | 107.69 RPS              | 100%          |

*Hardware utilizado para el test: 2 Cores CPU, 2 GB RAM (Contenedor Docker).*

### ¿Por qué se requiere escalar la arquitectura para entornos bancarios? (Justificación Técnica)
Como se observa en la tabla, el entorno actual alcanza un **techo rígido de ~107 RPS**. Si bien el 100% de las transacciones son exitosas gracias a que el sistema las encola pacientemente, en el mundo bancario real (por ejemplo, pagos de nóminas masivos a fin de mes, o eventos de e-commerce como Black Friday), la carga no es de 30 concurrencias controladas, sino de **miles de transacciones exactas en un solo milisegundo**.

Si inyectáramos 10,000 peticiones 100% simultáneas contra el motor actual:
1. **Saturación del Pool de Conexiones**: El ORM actual (`SQLAlchemy Sync`) mantiene bloqueado el hilo de ejecución mientras espera respuesta de PostgreSQL. Al agotarse el pool base (usualmente de 5 a 20 conexiones), el resto de las peticiones fallarían por *Timeout*.
2. **Latencia Matemática (K-Means)**: Extraer matrices, escalar (`scaler.transform()`) y hacer inferencia matemática por CPU toma milisegundos que se acumulan fatalmente si el código es bloqueante.
3. **TCP Port Exhaustion**: El sistema operativo del servidor colapsaría sus puertos de entrada HTTP antes siquiera de llegar al motor de validación.

### Requisitos Recomendados (Para 10,000 - 1,000,000 Transacciones Simultáneas)
Para erradicar el techo de 107 RPS y procesar altos volúmenes sin latencia, es imperativo pasar a una **Arquitectura Distribuida y Asíncrona**:

1. **ORM Asíncrono (`asyncpg`)**: Es el paso más crítico. Permite liberar el *Event Loop* mientras la BD responde, logrando que un solo servidor pase de procesar 100 RPS a +5,000 RPS.
2. **Pooler de Base de Datos (PgBouncer/RDS Proxy)**: Indispensable para multiplexar miles de transacciones concurrentes en unas pocas conexiones reales a PostgreSQL sin colapsar la RAM de la base de datos.
3. **Caché Ultrasónica (Redis)**: Para mantener el modelo K-Means y los metadatos en memoria viva, evitando tocar el disco o instanciar objetos pesados por cada *request*.
4. **Mensajería Asíncrona (Apache Kafka)**: Para registrar el historial de las peticiones procesadas *offline*. La API devolvería inmediatamente "Aprobado", y por detrás un proceso encolado insertaría el historial en PostgreSQL sin penalizar al usuario final.
5. **Auto-Scaling (Kubernetes)**: Para instanciar 100 o más réplicas de la API dinámicamente cuando el tráfico reviente, detrás de un balanceador de carga global.
