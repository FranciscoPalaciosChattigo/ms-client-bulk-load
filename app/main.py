from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from app.api.routes import router
from app.config.settings import get_settings

# Logging a stdout (para evitar logs en rojo)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando MS Client Bulk Load")
    logger.info(f"🔗 ig-db-mongo URL: {settings.IG_DB_MONGO_URL}")
    yield
    # Shutdown
    logger.info("🛑 Cerrando MS Client Bulk Load")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Microservicio para carga masiva de archivos CSV/Excel",
    lifespan=lifespan  # ← Reemplaza on_event
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "ms-client-bulk-load",
        "version": settings.API_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8088, reload=True)