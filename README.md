# MS-Client-Bulk-Load

Microservicio Python para carga masiva de archivos CSV y Excel a MongoDB via ig-db-mongo.

## 🚀 Características

- ✅ Procesa archivos CSV y Excel (.xlsx, .xls)
- ✅ Procesamiento por batches de 1000 filas
- ✅ Integración con ig-db-mongo service
- ✅ API REST con FastAPI
- ✅ Soporte para archivos hasta 100MB
- ✅ Manejo robusto de errores
- ✅ Logging detallado

## 📋 Requisitos

- Python 3.12+
- ig-db-mongo corriendo en `http://localhost:8087`

## 🔧 Instalación

### 1. Clonar y configurar

```bash
cd ms-client-bulk-load
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` si es necesario:
```env
IG_DB_MONGO_URL=http://localhost:8087
BATCH_SIZE=1000
MAX_FILE_SIZE_MB=100
```

### 3. Ejecutar

```bash
python app/main.py
```

O con uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servicio estará en: `http://localhost:8000`

## 🐳 Docker

```bash
# Build y run
docker-compose up --build

# Solo build
docker build -t ms-client-bulk-load .

# Run
docker run -p 8000:8000 -e IG_DB_MONGO_URL=http://host.docker.internal:8087 ms-client-bulk-load
```

## 📡 API Endpoints

### 1. Upload File

**POST** `/api/v1/upload`

Carga un archivo CSV o Excel.

**Form Data:**
- `client_id` (string): ID del cliente (nombre de colección en MongoDB)
- `file` (file): Archivo CSV o Excel

**Ejemplo con curl:**

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "client_id=cliente_123" \
  -F "file=@datos.csv"
```

**Respuesta:**

```json
{
  "success": true,
  "message": "Archivo procesado exitosamente. 5000 filas en 5 batches.",
  "client_id": "cliente_123",
  "filename": "datos.csv",
  "total_rows": 5000,
  "total_batches": 5,
  "failed_batches": 0,
  "processing_time_seconds": 12.34
}
```

### 2. Delete Collection

**DELETE** `/api/v1/collection/{client_id}`

Elimina una colección completa.

**Ejemplo:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/collection/cliente_123"
```

### 3. Health Check

**GET** `/api/v1/health`

```bash
curl "http://localhost:8000/api/v1/health"
```

## 📊 Flujo de Procesamiento

```
1. Recibe archivo (CSV/Excel)
2. Valida formato y tamaño
3. Lee y parsea archivo
4. Divide en batches de 1000 filas
5. Por cada batch:
   - Convierte filas a documentos JSON
   - POST a ig-db-mongo (/google-sheet/save)
6. Retorna resumen (total filas, batches, errores)
```

## 🔗 Integración con ig-db-mongo

El servicio envía datos en el formato:

```json
{
  "googleSheetId": "cliente_123",
  "listData": [
    {"columna1": "valor1", "columna2": "valor2"},
    {"columna1": "valor3", "columna2": "valor4"}
  ]
}
```

**Endpoints usados:**
- `POST http://localhost:8087/google-sheet/save` - Guardar batch
- `DELETE http://localhost:8087/google-sheet/{sheetId}` - Eliminar colección

## 📝 Formatos Soportados

### CSV
- Encoding: UTF-8, UTF-8-BOM, Latin-1
- Delimitador: coma (,)
- Headers requeridos

### Excel
- Formatos: .xlsx, .xls
- Primera hoja se usa por defecto
- Headers en primera fila

## 🎯 Ejemplo de Uso

### 1. Crear archivo CSV de prueba

```csv
id,nombre,email,edad
1,Juan Pérez,juan@example.com,30
2,María García,maria@example.com,25
3,Pedro López,pedro@example.com,35
```

### 2. Subir archivo

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "client_id=clientes" \
  -F "file=@prueba.csv"
```

### 3. Verificar en MongoDB

Los documentos se guardan en la colección `clientes` con el formato:

```json
{
  "id": "1",
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "edad": "30"
}
```

## 📚 Documentación API

Acceder a la documentación interactiva:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Logs

El servicio genera logs detallados:

```
2025-01-13 10:00:00 - app.api.routes - INFO - 📁 Archivo recibido: datos.csv (2.5MB) - Cliente: cliente_123
2025-01-13 10:00:01 - app.services.file_processor - INFO - 📦 Batch de 1000 filas listo
2025-01-13 10:00:02 - app.services.mongo_client - INFO - ✅ Batch guardado: 1000 documentos en 'cliente_123'
2025-01-13 10:00:15 - app.api.routes - INFO - 🎉 Archivo procesado exitosamente. 5000 filas en 5 batches.
```

## ⚙️ Configuración

Variables de entorno disponibles:

| Variable | Descripción | Default |
|----------|-------------|---------|
| IG_DB_MONGO_URL | URL del servicio ig-db-mongo | http://localhost:8087 |
| BATCH_SIZE | Tamaño de batch | 1000 |
| MAX_FILE_SIZE_MB | Tamaño máximo de archivo | 100 |

## 🐛 Troubleshooting

### Error: Connection refused to ig-db-mongo

**Solución:** Verificar que ig-db-mongo esté corriendo en `http://localhost:8087`

```bash
curl http://localhost:8087/health
```

### Error: File too large

**Solución:** Aumentar `MAX_FILE_SIZE_MB` en `.env`

### Error: Unsupported file format

**Solución:** Verificar que el archivo sea CSV o Excel (.xlsx, .xls)

## 📈 Performance

- Batch size: 1000 documentos
- Tiempo promedio: ~2-3 segundos por 1000 filas
- Memoria: ~100-200MB para archivos de 50K filas

## 🔐 Seguridad

- Validación de formato de archivo
- Límite de tamaño configurable
- Sanitización de datos
- Usuario no-root en Docker

## 📞 Soporte

Para problemas o preguntas, revisar los logs del servicio.
