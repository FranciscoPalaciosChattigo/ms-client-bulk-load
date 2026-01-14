import csv
import io
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
import logging
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Servicio para procesar archivos CSV en lotes"""
    
    def __init__(self):
        self.settings = get_settings()
        self.batch_size = self.settings.BATCH_SIZE
    
    async def process_csv_in_batches(
        self,
        file_content: bytes,
        client_id: str,
        file_id: str
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Procesar archivo CSV en lotes
        
        Args:
            file_content: Contenido del archivo CSV en bytes
            client_id: ID del cliente
            file_id: ID del archivo
            
        Yields:
            Lotes de documentos listos para insertar en MongoDB
        """
        try:
            # Decodificar contenido
            content_str = file_content.decode('utf-8-sig')  # utf-8-sig maneja BOM
            csv_file = io.StringIO(content_str)
            
            # Leer CSV
            csv_reader = csv.DictReader(csv_file)
            
            batch = []
            row_number = 1
            
            for row in csv_reader:
                # Crear documento
                document = {
                    "client_id": client_id,
                    "file_id": file_id,
                    "row_number": row_number,
                    "data": row,
                    "created_at": datetime.utcnow()
                }
                
                batch.append(document)
                row_number += 1
                
                # Cuando el lote alcanza el tamaño definido, yield
                if len(batch) >= self.batch_size:
                    yield batch
                    batch = []
            
            # Yield del último lote si tiene datos
            if batch:
                yield batch
                
            logger.info(f"✅ Procesadas {row_number - 1} filas del archivo")
            
        except UnicodeDecodeError:
            # Intentar con latin-1 si UTF-8 falla
            try:
                content_str = file_content.decode('latin-1')
                csv_file = io.StringIO(content_str)
                csv_reader = csv.DictReader(csv_file)
                
                batch = []
                row_number = 1
                
                for row in csv_reader:
                    document = {
                        "client_id": client_id,
                        "file_id": file_id,
                        "row_number": row_number,
                        "data": row,
                        "created_at": datetime.utcnow()
                    }
                    
                    batch.append(document)
                    row_number += 1
                    
                    if len(batch) >= self.batch_size:
                        yield batch
                        batch = []
                
                if batch:
                    yield batch
                    
            except Exception as e:
                logger.error(f"❌ Error decodificando archivo: {e}")
                raise ValueError(f"No se pudo decodificar el archivo CSV: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando CSV: {e}")
            raise
    
    def validate_csv_headers(self, file_content: bytes) -> tuple[bool, str, List[str]]:
        """
        Validar que el archivo tenga headers válidos
        
        Returns:
            (is_valid, error_message, headers)
        """
        try:
            content_str = file_content.decode('utf-8-sig')
            csv_file = io.StringIO(content_str)
            csv_reader = csv.DictReader(csv_file)
            
            headers = csv_reader.fieldnames
            
            if not headers:
                return False, "El archivo CSV no tiene headers", []
            
            if len(headers) == 0:
                return False, "El archivo CSV está vacío", []
            
            # Verificar que no haya headers duplicados
            if len(headers) != len(set(headers)):
                return False, "El archivo tiene headers duplicados", headers
            
            return True, "", headers
            
        except Exception as e:
            return False, f"Error validando headers: {str(e)}", []
    
    def estimate_row_count(self, file_content: bytes) -> int:
        """
        Estimar el número de filas en el CSV
        """
        try:
            content_str = file_content.decode('utf-8-sig')
            # Contar saltos de línea menos 1 (header)
            row_count = content_str.count('\n')
            return max(0, row_count - 1)  # Restar header
        except:
            return 0


# Instancia global del procesador
csv_processor = CSVProcessor()
