
---

## 🚀 Quick Start - MS Client Bulk Load

### ¿Qué es?
Un microservicio **Python + FastAPI** que permite cargar archivos **CSV y Excel** de forma masiva hacia MongoDB a través del servicio `ig-db-mongo`.

### Arquitectura

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│   CSV / Excel   │ ───► │  MS-Client-Bulk-Load │ ───► │  ig-db-mongo    │ ───► MongoDB
│   (archivo)     │      │  (FastAPI :8088)     │      │  (API :8087)    │
└─────────────────┘      └──────────────────────┘      └─────────────────┘
```

### Flujo de trabajo
1. **Recibes** un archivo CSV o Excel vía POST
2. **Parsea** el archivo con Pandas
3. **Divide** en batches de X filas
4. **Envía** cada batch a `ig-db-mongo` para guardarlo en MongoDB

---

### ⚡ Pasos para ejecutar

```bash
# 1. Crear y activar entorno virtual
cd /Users/franciscopalacios/Desktop/ms-client-bulk-load
python -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# (Edita .env si necesitas cambiar IG_DB_MONGO_URL)

# 4. Ejecutar el servicio
python app/main.py
```

El servicio arranca en **http://localhost:8088**

---

### 📡 Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/bulk-load-data/file` | Subir archivo CSV/Excel |
| `GET` | `/bulk-load-data/health` | Health check |

### Ejemplo de uso

```bash
# Subir un archivo CSV
curl -X 'POST' \
  'http://localhost:8088/bulk-load-data/file' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'cliente=test' \
  -F 'numero_cliente=22' \
  -F 'file=@test-data-100k - test_data.csv;type=text/csv'

```

---

### 📂 Estructura del proyecto

| Carpeta/Archivo | Descripción |
|-----------------|-------------|
| [app/main.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/main.py:0:0-0:0) | Punto de entrada FastAPI |
| [app/api/routes.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/api/routes.py:0:0-0:0) | Endpoints REST |
| [app/services/file_processor.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/services/file_processor.py:0:0-0:0) | Procesador de archivos |
| [app/services/csv_processor.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/services/csv_processor.py:0:0-0:0) | Parseo de CSV/Excel |
| [app/services/mongo_service.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/services/mongo_service.py:0:0-0:0) | Cliente para ig-db-mongo |
| [app/config/settings.py](cci:7://file:///Users/franciscopalacios/Desktop/ms-client-bulk-load/app/config/settings.py:0:0-0:0) | Configuración desde .env |

---

### 📋 Requisitos previos
- **Python 3.12+**
- **ig-db-mongo** corriendo en `http://localhost:8087` (o la URL que configures)

### 📚 Documentación API
Una vez corriendo, puedes acceder a:
- **Swagger UI**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc

---

¿Quieres que te ayude a levantar el proyecto o que profundice en alguna parte específica?