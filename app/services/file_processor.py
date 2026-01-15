import csv
import io
import string
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

    def clean_value(self, value: Any) -> str:
        """
        Limpiar un valor: remover espacios y puntuación al final

        Args:
            value: Valor a limpiar

        Returns:
            String limpio
        """
        if value is None:
            return ""

        # Convertir a string y limpiar
        cleaned = str(value).strip()
        # Remover puntuación y espacios al final
        cleaned = cleaned.rstrip(string.punctuation + string.whitespace)

        return cleaned

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
            Batches de documentos con _id = primera columna
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

        # Obtener headers y primera columna
        headers = csv_reader.fieldnames
        if not headers or len(headers) == 0:
            raise ValueError("El archivo CSV no tiene headers")

        first_column = headers[0]
        logger.info(f"📋 Primera columna (será _id): {first_column}")

        batch = []
        row_count = 0

        for row in csv_reader:
            row_count += 1

            # Limpiar todos los valores
            clean_row = {k: self.clean_value(v) for k, v in row.items()}

            # Usar primera columna como _id
            document = {
                "_id": clean_row.get(first_column, ""),
                **clean_row
            }

            batch.append(document)

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
            Batches de documentos con _id = primera columna
        """
        try:
            # Leer Excel con pandas
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')

            # Reemplazar NaN con string vacío
            df = df.fillna("")

            # Primera columna como _id
            first_column = df.columns[0]
            logger.info(f"📋 Primera columna (será _id): {first_column}")

            # Convertir a lista de diccionarios con _id y limpieza
            records = []
            for _, row in df.iterrows():
                # Limpiar todos los valores
                clean_row = {k: self.clean_value(v) for k, v in row.to_dict().items()}

                document = {
                    "_id": clean_row.get(first_column, ""),
                    **clean_row
                }
                records.append(document)

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