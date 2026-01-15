"""
API Routes - Endpoints REST
"""
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
import logging
from app.services.task_processor import task_processor
from app.config.settings import get_settings
from app.utils.constants import ErrorMessages, FileFormats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bulk-load-data", tags=["bulk-load"])
settings = get_settings()


@router.post("/file")
async def upload_file(
    background_tasks: BackgroundTasks,
    client_id: str = Form(..., description="ID del cliente"),
    business_name: str = Form(..., description="Nombre del negocio"),
    file: UploadFile = File(..., description="Archivo CSV o Excel")
):
    """
    ...
    Args:
        client_id: ID del cliente
        business_name: Nombre del negocio
        file: Archivo a procesar

    Returns:
        task_id: ID de la tarea para consultar progreso
        status: Estado inicial (queued)
        message: Mensaje descriptivo
    """

    # Validar que el archivo tenga nombre
    if not file.filename:
        raise HTTPException(status_code=400, detail=ErrorMessages.FILE_NO_NAME)

    # Validar formato de archivo
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in FileFormats.ALL_SUPPORTED):
        raise HTTPException(status_code=400, detail=ErrorMessages.FILE_NOT_SUPPORTED)

    try:
        # Leer contenido del archivo
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        # Validar tamaño del archivo
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=ErrorMessages.FILE_TOO_LARGE.format(max_size=settings.MAX_FILE_SIZE_MB)
            )

        logger.info(f"📁 Archivo recibido: {file.filename} ({file_size_mb:.2f}MB)")
        logger.info(f"👤 Cliente ID: {client_id}, Negocio: {business_name}")

        # Crear tarea
        task_id = task_processor.create_task(
            client_id=client_id,
            business_name=business_name,
            filename=file.filename
        )

        # Agregar procesamiento en background
        background_tasks.add_task(
            task_processor.process_file_async,
            task_id,
            file_content,
            file.filename,
            client_id,
            business_name
        )

        # Responder inmediatamente
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Archivo recibido. Procesando en background.",
            "client_id": client_id,
            "business_name": business_name,
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recibiendo archivo: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"{ErrorMessages.INTERNAL_ERROR}: {str(e)}"
        )


@router.get("/{clientId}/{businessName}/search/{id}")
async def search_document(
        clientId: str,
        businessName: str,
        id: str
):
    """
    Buscar un documento específico por su ID en una colección

    Args:
        clientId: ID del cliente
        businessName: Nombre del negocio
        id: ID del documento (valor de la primera columna del Excel)

    Returns:
        Documento encontrado o mensaje de no encontrado
    """
    try:
        url = f"{settings.IG_DB_MONGO_URL}/api/rest/v1/google-sheet/{clientId}/{businessName}/search?id={id}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error consultando ig-db-mongo: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout consultando ig-db-mongo")
    except Exception as e:
        logger.error(f"❌ Error buscando documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{clientId}/collections")
async def list_collections(clientId: str):
    """
    Listar todas las colecciones de un cliente

    Args:
        clientId: ID del cliente

    Returns:
        Lista de colecciones que pertenecen al cliente
    """
    try:
        url = f"{settings.IG_DB_MONGO_URL}/api/rest/v1/google-sheet/{clientId}/collections"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error consultando ig-db-mongo: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout consultando ig-db-mongo")
    except Exception as e:
        logger.error(f"❌ Error listando colecciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Consultar el estado de una tarea en progreso

    Args:
        task_id: ID único de la tarea

    Returns:
        Estado completo de la tarea incluyendo progreso y resultados

    Raises:
        404: Si el task_id no existe
    """
    status = task_processor.get_task_status(task_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task ID '{task_id}' no encontrado"
        )

    return status


@router.get("/health")
async def health_check():
    """
    Health check del servicio

    Verifica que el servicio esté corriendo y muestra configuración básica

    Returns:
        status: Estado del servicio
        service: Nombre del servicio
        ig_db_mongo_url: URL del servicio externo
    """
    return {
        "status": "healthy",
        "service": "ms-client-bulk-load",
        "ig_db_mongo_url": settings.IG_DB_MONGO_URL,
        "version": settings.API_VERSION
    }