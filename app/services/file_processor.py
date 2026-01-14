import csv
import io
import pandas as pd
from typing import List, Dict, Any, AsyncGenerator
import logging
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class FileProcessor:
    """Servicio para procesar archivos CSV y Excel"""

    def __init__(self):
        self.settings = get_settings()
        self.batch_size = self.settings.BATCH_SIZE

    async def process_csv(
            self,
            file_content: bytes,
            filename: str
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Procesar archivo CSV en batches

        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo

        Yields:
            Batches de documentos
        """
        try:
            # Intentar UTF-8 primero
            content_str = file_content.decode('utf-8-sig')
        except UnicodeDecodeError:
            # Fallback a latin-1
            content_str = file_content.decode('latin-1')
            logger.info(f"Usando encoding latin-1 para {filename}")

        csv_file = io.StringIO(content_str)
        csv_reader = csv.DictReader(csv_file)

        batch = []
        row_count = 0

        for row in csv_reader:
            row_count += 1
            # Convertir None a string vacío
            clean_row = {k: (v if v is not None else "") for k, v in row.items()}
            batch.append(clean_row)

            if len(batch) >= self.batch_size:
                logger.info(f"📦 Batch de {len(batch)} filas listo")
                yield batch
                batch = []

        # Último batch
        if batch:
            logger.info(f"📦 Último batch de {len(batch)} filas")
            yield batch

        logger.info(f"✅ Total procesado: {row_count} filas")

    async def process_excel(
            self,
            file_content: bytes,
            filename: str
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Procesar archivo Excel en batches

        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo

        Yields:
            Batches de documentos
        """
        try:
            # Leer Excel con pandas
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')

            # Reemplazar NaN con string vacío
            df = df.fillna("")

            # Convertir a lista de diccionarios
            records = df.to_dict('records')
            total = len(records)

            logger.info(f"📊 Excel leído: {total} filas")

            # Dividir en batches
            for i in range(0, total, self.batch_size):
                batch = records[i:i + self.batch_size]
                logger.info(f"📦 Batch de {len(batch)} filas listo")
                yield batch

        except Exception as e:
            logger.error(f"❌ Error procesando Excel: {e}")
            raise

    async def process_file(
            self,
            file_content: bytes,
            filename: str
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Procesar archivo según su tipo

        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo

        Yields:
            Batches de documentos
        """
        filename_lower = filename.lower()

        if filename_lower.endswith('.csv'):
            async for batch in self.process_csv(file_content, filename):
                yield batch

        elif filename_lower.endswith(('.xlsx', '.xls')):
            async for batch in self.process_excel(file_content, filename):
                yield batch

        else:
            raise ValueError(f"Formato de archivo no soportado: {filename}")


# Instancia global
file_processor = FileProcessor()