from pydantic import BaseModel, Field
from typing import Optional


class UploadRequest(BaseModel):
    """Request para upload de archivo"""
    client_id: str = Field(..., description="ID del cliente")
    business_name: str = Field(..., description="Nombre del negocio")


class UploadResponse(BaseModel):
    """Response del proceso de carga"""
    success: bool
    message: str
    client_id: str
    business_name: str
    collection_name: str
    filename: str
    total_rows: int
    processing_time_seconds: float