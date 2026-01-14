from pydantic import BaseModel, Field
from typing import Optional


class UploadRequest(BaseModel):
    """Request para upload de archivo"""
    cliente: str = Field(..., description="Nombre del cliente")
    numero_cliente: str = Field(..., description="ID/número del cliente o archivo")


class UploadResponse(BaseModel):
    """Response del proceso de carga"""
    success: bool
    message: str
    cliente: str
    numero_cliente: str
    collection_name: str
    filename: str
    total_rows: int
    processing_time_seconds: float