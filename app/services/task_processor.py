"""
Task Processor Service - Manejo de tareas en background
"""
import time
import logging
import uuid
from typing import Dict, Any
from app.services.file_processor import file_processor
from app.client.mongo_client import mongo_client
from app.mapper.data_mapper import DataMapper
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Servicio para procesar tareas en background"""

    def __init__(self):
        self.settings = get_settings()
        self.mapper = DataMapper()
        # Almacenamiento en memoria (después reemplazar con Redis/DB)
        self.task_store: Dict[str, Dict[str, Any]] = {}

    def create_task(self, cliente: str, numero_cliente: str, filename: str) -> str:
        """
        Crear una nueva tarea y retornar su ID

        Args:
            cliente: Nombre del cliente
            numero_cliente: ID del cliente
            filename: Nombre del archivo

        Returns:
            task_id generado
        """
        task_id = str(uuid.uuid4())

        self.task_store[task_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Archivo recibido, en cola para procesamiento",
            "total_rows": 0,
            "processed_rows": 0,
            "cliente": cliente,
            "numero_cliente": numero_cliente,
            "filename": filename
        }

        logger.info(f"🆔 Task creado: {task_id}")
        print(f"🎫 [SOCKET] Task {task_id}: Creado y en cola")

        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtener el estado de una tarea

        Args:
            task_id: ID de la tarea

        Returns:
            Estado de la tarea o None si no existe
        """
        return self.task_store.get(task_id)

    def update_task_status(
            self,
            task_id: str,
            status: str,
            progress: int,
            message: str,
            **kwargs
    ):
        """
        Actualizar el estado de una tarea

        Args:
            task_id: ID de la tarea
            status: Estado actual (queued, processing, completed, failed)
            progress: Progreso en porcentaje (0-100)
            message: Mensaje descriptivo
            **kwargs: Campos adicionales
        """
        if task_id in self.task_store:
            self.task_store[task_id].update({
                "status": status,
                "progress": progress,
                "message": message,
                **kwargs
            })

            # Log para simular WebSocket
            emoji = {
                "queued": "🎫",
                "processing": "🔄",
                "completed": "✅",
                "completed_with_errors": "⚠️",
                "failed": "❌"
            }.get(status, "📊")

            print(f"{emoji} [SOCKET] Task {task_id}: {message}")

    async def process_file_async(
            self,
            task_id: str,
            file_content: bytes,
            filename: str,
            cliente: str,
            numero_cliente: str
    ):
        """
        Procesar archivo en background y actualizar estado

        Args:
            task_id: ID de la tarea
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            cliente: Nombre del cliente
            numero_cliente: ID del cliente
        """
        start_time = time.time()

        try:
            # Estado: iniciando procesamiento
            self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=0,
                message="Iniciando procesamiento...",
                total_rows=0,
                processed_rows=0
            )

            # Procesar archivo en batches
            total_rows = 0
            batch_count = 0
            failed_batches = 0

            async for batch in file_processor.process_file(file_content, filename):
                batch_count += 1
                batch_size = len(batch)
                total_rows += batch_size

                # Calcular progreso estimado (asumiendo 100K filas max)
                progress = min(int((total_rows / 100000) * 100), 99)

                # Actualizar estado
                self.update_task_status(
                    task_id=task_id,
                    status="processing",
                    progress=progress,
                    message=f"Procesando batch {batch_count}...",
                    total_rows=total_rows,
                    processed_rows=total_rows,
                    current_batch=batch_count
                )

                logger.info(f"📦 Task {task_id}: Batch {batch_count} ({batch_size} docs)")

                # Enviar batch a ig-db-mongo
                success = await mongo_client.bulk_import(
                    cliente=cliente,
                    numero_cliente=numero_cliente,
                    all_documents=batch
                )

                if not success:
                    failed_batches += 1
                    logger.error(f"❌ Task {task_id}: Falló batch {batch_count}")

            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            collection_name = self.mapper.build_collection_name(cliente, numero_cliente)

            # Estado final
            if failed_batches == 0:
                self.update_task_status(
                    task_id=task_id,
                    status="completed",
                    progress=100,
                    message=f"Completado exitosamente. {total_rows} documentos insertados.",
                    total_rows=total_rows,
                    processed_rows=total_rows,
                    collection_name=collection_name,
                    processing_time_seconds=round(processing_time, 2),
                    total_batches=batch_count,
                    failed_batches=0
                )
                logger.info(f"✅ Task {task_id}: Completado - {total_rows} docs en {processing_time:.2f}s")

            else:
                self.update_task_status(
                    task_id=task_id,
                    status="completed_with_errors",
                    progress=100,
                    message=f"Completado con errores. {failed_batches}/{batch_count} batches fallidos.",
                    total_rows=total_rows,
                    processed_rows=total_rows,
                    collection_name=collection_name,
                    processing_time_seconds=round(processing_time, 2),
                    total_batches=batch_count,
                    failed_batches=failed_batches
                )
                logger.warning(f"⚠️ Task {task_id}: Completado con {failed_batches} errores")

        except Exception as e:
            # Estado de error
            self.update_task_status(
                task_id=task_id,
                status="failed",
                progress=0,
                message=f"Error: {str(e)}",
                total_rows=0,
                processed_rows=0,
                error_detail=str(e)
            )
            logger.error(f"❌ Task {task_id}: Error - {e}", exc_info=True)


# Instancia global
task_processor = TaskProcessor()