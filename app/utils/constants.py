"""
Constantes del microservicio
"""


class LogMessages:
    """Mensajes de log estandarizados"""
    LOG_INI = "INIT"
    LOG_OK = "OK"
    LOG_EX = "EXCEPTION"


class FileFormats:
    """Formatos de archivo soportados"""
    CSV = ['.csv']
    EXCEL = ['.xlsx', '.xls']
    ALL_SUPPORTED = CSV + EXCEL


class HttpStatus:
    """Códigos de estado HTTP"""
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


class ErrorMessages:
    """Mensajes de error"""
    FILE_NO_NAME = "Archivo sin nombre"
    FILE_NOT_SUPPORTED = "Formato no soportado. Use CSV o Excel (.xlsx, .xls)"
    FILE_TOO_LARGE = "Archivo excede el tamaño máximo ({max_size}MB)"
    MONGODB_SAVE_ERROR = "Error guardando datos en MongoDB"
    VALIDATION_ERROR = "Error de validación"
    INTERNAL_ERROR = "Error interno"