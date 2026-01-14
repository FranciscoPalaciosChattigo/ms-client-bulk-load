from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import time
import logging
import uuid
from app.dto.schemas import UploadResponse
from app.services.file_processor import file_processor
from app.client.mongo_client import mongo_client
from app.mapper.data_mapper import DataMapper
from app.config.settings import get_settings
from app.utils.constants import ErrorMessages, LogMessages, FileFormats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bulk-load-data", tags=["bulk-load"])
settings = get_settings()
mapper = DataMapper()

# Almacenamiento en memoria de estados de tareas (después reemplazar con Redis/DB)
task_status_store = {}


async def process_file_async(
        task_id: str,
        file_content: bytes,
        filename: str,
        cliente: str,
        numero_cliente: str
):
    """
    Procesar archivo en background y actualizar estado
    """
    start_time = time.time()

    try:
        # Actualizar estado: iniciando
        task_status_store[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Iniciando procesamiento...",
            "total_rows": 0,
            "processed_rows": 0
        }
        print(f"🔄 [SOCKET] Task {task_id}: Iniciando procesamiento")

        # Procesar archivo en batches
        total_rows = 0
        batch_count = 0
        failed_batches = 0

        async for batch in file_processor.process_file(file_content, filename):
            batch_count += 1
            batch_size = len(batch)
            total_rows += batch_size

            # Calcular progreso estimado
            progress = min(int((total_rows / 100000) * 100), 99)

            # Actualizar estado
            task_status_store[task_id] = {
                "status": "processing",
                "progress": progress,
                "message": f"Procesando batch {batch_count}...",
                "total_rows": total_rows,
                "processed_rows": total_rows
            }
            print(f"📊 [SOCKET] Task {task_id}: Progreso {progress}% - Batch {batch_count} ({batch_size} docs)")

            # Enviar batch a ig-db-mongo
            success = await mongo_client.bulk_import(
                cliente=cliente,
                numero_cliente=numero_cliente,
                all_documents=batch
            )

            if not success:
                failed_batches += 1
                logger.error(f"❌ Falló batch {batch_count}")

        # Calcular tiempo
        processing_time = time.time() - start_time
        collection_name = mapper.build_collection_name(cliente, numero_cliente)

        # Estado final
        if failed_batches == 0:
            task_status_store[task_id] = {
                "status": "completed",
                "progress": 100,
                "message": f"Completado exitosamente. {total_rows} documentos insertados.",
                "total_rows": total_rows,
                "processed_rows": total_rows,
                "collection_name": collection_name,
                "processing_time_seconds": round(processing_time, 2),
                "failed_batches": 0
            }
            print(f"✅ [SOCKET] Task {task_id}: Completado - {total_rows} documentos en {processing_time:.2f}s")
        else:
            task_status_store[task_id] = {
                "status": "completed_with_errors",
                "progress": 100,
                "message": f"Completado con errores. {failed_batches}/{batch_count} batches fallidos.",
                "total_rows": total_rows,
                "processed_rows": total_rows,
                "collection_name": collection_name,
                "processing_time_seconds": round(processing_time, 2),
                "failed_batches": failed_batches
            }
            print(f"⚠️ [SOCKET] Task {task_id}: Completado con {failed_batches} errores")

    except Exception as e:
        # Estado de error
        task_status_store[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Error: {str(e)}",
            "total_rows": 0,
            "processed_rows": 0
        }
        print(f"❌ [SOCKET] Task {task_id}: Error - {str(e)}")
        logger.error(f"❌ Error procesando tarea {task_id}: {e}")


@router.post("/file")
async def upload_excel_file(
        background_tasks: BackgroundTasks,
        cliente: str = Form(..., description="Nombre del cliente"),
        numero_cliente: str = Form(..., description="ID/número del cliente o archivo"),
        file: UploadFile = File(..., description="Archivo CSV o Excel")
):
    """
    Endpoint para cargar archivo CSV o Excel

    Retorna inmediatamente un task_id y procesa el archivo en background.
    El progreso se puede consultar con GET /bulk-load-data/status/{task_id}
    """

    # Validar tipo de archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail=ErrorMessages.FILE_NO_NAME)

    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in FileFormats.ALL_SUPPORTED):
        raise HTTPException(status_code=400, detail=ErrorMessages.FILE_NOT_SUPPORTED)

    try:
        # Leer contenido del archivo
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        # Validar tamaño
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=ErrorMessages.FILE_TOO_LARGE.format(max_size=settings.MAX_FILE_SIZE_MB)
            )

        # Generar task ID único
        task_id = str(uuid.uuid4())

        logger.info(f"📁 Archivo recibido: {file.filename} ({file_size_mb:.2f}MB)")
        logger.info(f"👤 Cliente: {cliente}, Número: {numero_cliente}")
        logger.info(f"🆔 Task ID: {task_id}")

        # Inicializar estado
        task_status_store[task_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Archivo recibido, en cola para procesamiento",
            "total_rows": 0,
            "processed_rows": 0
        }

        # Agregar tarea en background
        background_tasks.add_task(
            process_file_async,
            task_id,
            file_content,
            file.filename,
            cliente,
            numero_cliente
        )

        print(f"🎫 [SOCKET] Task {task_id}: Creado y en cola")

        # Responder INMEDIATAMENTE
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Archivo recibido. Procesando en background.",
            "cliente": cliente,
            "numero_cliente": numero_cliente,
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"❌ Error recibiendo archivo: {e}")
        raise HTTPException(status_code=500, detail=f"{ErrorMessages.INTERNAL_ERROR}: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Consultar el estado de una tarea en progreso
    """
    if task_id not in task_status_store:
        raise HTTPException(status_code=404, detail="Task ID no encontrado")

    return task_status_store[task_id]


@router.get("/health")
async def health_check():
    """
    Health check del servicio
    """
    return {
        "status": "healthy",
        "service": "ms-client-bulk-load",
        "ig_db_mongo_url": settings.IG_DB_MONGO_URL
    }