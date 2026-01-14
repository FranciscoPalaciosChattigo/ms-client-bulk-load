import httpx
import logging
from typing import List, Dict, Any
from app.config.settings import get_settings
from app.mapper.data_mapper import DataMapper
from app.utils.constants import LogMessages

logger = logging.getLogger(__name__)


class MongoClient:
    """Cliente HTTP para ig-db-mongo service"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.IG_DB_MONGO_URL
        self.timeout = 60.0  # Mayor timeout para archivos grandes
        self.mapper = DataMapper()

    async def bulk_import(
            self,
            cliente: str,
            numero_cliente: str,
            all_documents: List[Dict[str, Any]]
    ) -> bool:
        """
        Guardar todos los documentos de una vez en ig-db-mongo

        Args:
            cliente: Parte del nombre de colección
            numero_cliente: ID del cliente/archivo
            all_documents: Lista completa de documentos a guardar

        Returns:
            True si fue exitoso, False en caso de error
        """
        url = f"{self.base_url}/api/rest/v1/google-sheet/bulk-import"

        # Usar mapper para construir payload
        payload = self.mapper.map_to_bulk_import_request(
            cliente=cliente,
            numero_cliente=numero_cliente,
            documents=all_documents
        )

        try:
            logger.info(f"📤 Enviando {len(all_documents)} documentos a ig-db-mongo...")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Bulk import exitoso: {result}")
                    return True
                else:
                    logger.error(f"❌ Error en bulk import: {response.status_code} - {response.text}")
                    return False

        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout en bulk import")
            return False
        except Exception as e:
            logger.error(f"❌ Error en bulk import: {e}")
            return False


# Instancia global
mongo_client = MongoClient()