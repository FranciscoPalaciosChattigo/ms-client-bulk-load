"""
Mapper para transformaciones de datos
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataMapper:
    """Mapper para transformar datos entre capas"""

    @staticmethod
    def clean_row_data(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpiar datos de una fila
        Convierte None a string vacío

        Args:
            row: Diccionario con datos de una fila

        Returns:
            Diccionario con datos limpios
        """
        return {k: (v if v is not None else "") for k, v in row.items()}

    @staticmethod
    def map_to_bulk_import_request(
            cliente: str,
            numero_cliente: str,
            documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Mapear datos al formato de BulkImportRequest

        Args:
            cliente: Nombre del cliente
            numero_cliente: ID/número del cliente
            documents: Lista de documentos

        Returns:
            Payload formateado para ig-db-mongo
        """
        return {
            "cliente": cliente,
            "numeroCliente": numero_cliente,
            "data": documents
        }

    @staticmethod
    def build_collection_name(client_id: str, business_name: str) -> str:
        """
        Construir nombre de colección según formato requerido
        Formato: clientId/businessName-DB
        """
        return f"{client_id}/{business_name}-DB"

    @staticmethod
    def map_to_bulk_import_request(
            client_id: str,
            business_name: str,
            documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Mapear datos al formato de BulkImportRequest
        """
        return {
            "clientId": client_id,
            "businessName": business_name,
            "data": documents
        }