from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import InsertOne
from typing import List, Dict, Any
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)


class MongoService:
    """Servicio para operaciones con MongoDB"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None
    
    async def connect(self):
        """Conectar a MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(
                self.settings.MONGODB_URI,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[self.settings.MONGODB_DATABASE]
            
            # Verificar conexión
            await self.client.admin.command('ping')
            logger.info("✅ Conectado a MongoDB Atlas")
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Cerrar conexión a MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Conexión a MongoDB cerrada")
    
    def get_collection_name(self, client_id: str, file_id: str) -> str:
        """
        Generar nombre de colección basado en cliente y archivo
        Formato: client_{client_id}_file_{file_id}
        """
        return f"client_{client_id}_file_{file_id}"
    
    async def bulk_insert_documents(
        self, 
        collection_name: str, 
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Insertar múltiples documentos en una colección
        
        Args:
            collection_name: Nombre de la colección
            documents: Lista de documentos a insertar
            
        Returns:
            Número de documentos insertados
        """
        try:
            collection = self.db[collection_name]
            
            # Usar bulk_write para mejor rendimiento
            operations = [InsertOne(doc) for doc in documents]
            result = await collection.bulk_write(operations, ordered=False)
            
            logger.info(f"✅ Insertados {result.inserted_count} documentos en {collection_name}")
            return result.inserted_count
            
        except Exception as e:
            logger.error(f"❌ Error en bulk insert: {e}")
            raise
    
    async def create_indexes(self, collection_name: str):
        """
        Crear índices para optimizar consultas
        """
        try:
            collection = self.db[collection_name]
            
            # Índice en client_id y file_id
            await collection.create_index([("client_id", 1), ("file_id", 1)])
            
            # Índice en row_number para ordenamiento
            await collection.create_index([("row_number", 1)])
            
            # Índice en created_at para queries temporales
            await collection.create_index([("created_at", -1)])
            
            logger.info(f"✅ Índices creados en {collection_name}")
            
        except Exception as e:
            logger.error(f"⚠️ Error creando índices: {e}")
    
    async def get_document_count(self, collection_name: str) -> int:
        """Obtener el número de documentos en una colección"""
        try:
            collection = self.db[collection_name]
            count = await collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error obteniendo conteo: {e}")
            return 0
    
    async def collection_exists(self, collection_name: str) -> bool:
        """Verificar si una colección existe"""
        collections = await self.db.list_collection_names()
        return collection_name in collections


# Instancia global del servicio
mongo_service = MongoService()
