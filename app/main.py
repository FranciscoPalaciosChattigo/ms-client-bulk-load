from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.routes import router
# from app.api.routes import router
from app.config.settings import get_settings
import logging
import sys

# Configurar logging para que vaya a stdout (blanco) en lugar de stderr (rojo)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # ← Clave: usar stdout
    ],
    force=True  # ← Sobreescribir configuración existente
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Microservicio para carga masiva de archivos CSV/Excel"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando MS Client Bulk Load")
    logger.info(f"🔗 ig-db-mongo URL: {settings.IG_DB_MONGO_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Cerrando MS Client Bulk Load")


@app.get("/")
async def root():
    return {
        "service": "ms-client-bulk-load",
        "version": settings.API_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8088,
        reload=True
    )

#
#
# import pandas as pd
#
# # Nombre de tu archivo de entrada y salida
# input_csv = '/Users/franciscopalacios/Desktop/ms-client-bulk-load 2/app/test-data-100k.csv'  # Asegúrate que este nombre coincida con tu archivo
# output_json = 'test_data_mongo.json'
#
# print("Leyendo archivo CSV...")
# # Leemos el CSV
# df = pd.read_csv(input_csv)
#
# print("Convirtiendo a JSON...")
# # Convertimos a JSON con formato 'records' que crea una lista de objetos
# # indent=4 es para que sea legible, quítalo si quieres reducir el tamaño del archivo
# df.to_json(output_json, orient='records', indent=4)
#
# print(f"¡Listo! Archivo guardado como: {output_json}")