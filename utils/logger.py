"""
Sistema de logging profesional

Configura logging con:
- Salida a archivo (logs/trading_bot.log)
- Salida a consola (con colores)
- Rotación automática de logs
- Formato profesional con timestamps
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config.config import Config


def setup_logger(name: str = None, level: str = None) -> logging.Logger:
    """
    Configura y retorna un logger profesional
    
    Args:
        name: Nombre del logger (None = root logger)
        level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
               Si None, usa Config.LOG_LEVEL
    
    Returns:
        Logger configurado
    
    Características:
        - Archivo rotativo (max 10MB, 5 backups)
        - Consola con colores
        - Formato: [2025-12-24 00:10:00] INFO - Mensaje
    
    Ejemplo:
        >>> from utils import setup_logger
        >>> logger = setup_logger()
        >>> logger.info("Sistema iniciado")
        >>> logger.error("Error crítico")
    """
    # Determinar nombre del logger
    if name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
    
    # Determinar nivel
    if level is None:
        level = Config.LOG_LEVEL
    
    # Configurar nivel
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger
    
    # Crear formateador
    formatter = logging.Formatter(
        Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )
    
    # =========================================================================
    # HANDLER 1: ARCHIVO (con rotación)
    # =========================================================================
    try:
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,               # 5 archivos de backup
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Guardar todo en archivo
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️  No se pudo crear log en archivo: {e}")
    
    
    # =========================================================================
    # HANDLER 2: CONSOLA (con colores)
    # =========================================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Solo INFO+ en consola
    
    # Formateador con colores para consola
    console_formatter = ColoredFormatter(
        Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


class ColoredFormatter(logging.Formatter):
    """
    Formateador personalizado con colores ANSI para la consola
    
    Colores:
        DEBUG: Gris
        INFO: Blanco
        WARNING: Amarillo
        ERROR: Rojo
        CRITICAL: Rojo brillante + negrita
    """
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[90m',      # Gris
        'INFO': '\033[97m',       # Blanco brillante
        'WARNING': '\033[93m',    # Amarillo
        'ERROR': '\033[91m',      # Rojo
        'CRITICAL': '\033[1;91m'  # Rojo brillante + negrita
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Aplica color según el nivel del log"""
        # Obtener color según nivel
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Formatear mensaje original
        message = super().format(record)
        
        # Aplicar color
        colored_message = f"{color}{message}{self.RESET}"
        
        return colored_message


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger ya configurado por nombre
    
    Args:
        name: Nombre del módulo (__name__)
    
    Returns:
        Logger configurado
    
    Ejemplo:
        >>> # En cualquier archivo .py
        >>> from utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensaje desde mi módulo")
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exception: Exception, 
                  context: str = ""):
    """
    Registra una excepción con traceback completo
    
    Args:
        logger: Logger a usar
        exception: Excepción capturada
        context: Contexto adicional (opcional)
    
    Ejemplo:
        >>> try:
        >>>     # código que puede fallar
        >>>     1 / 0
        >>> except Exception as e:
        >>>     log_exception(logger, e, "División por cero")
    """
    import traceback
    
    error_msg = f"{'[' + context + '] ' if context else ''}{str(exception)}"
    logger.error(error_msg)
    logger.debug(f"Traceback:\n{traceback.format_exc()}")


def configure_third_party_loggers():
    """
    Silencia loggers de librerías de terceros (reduce ruido)
    
    Configura:
        - urllib3: WARNING
        - telegram: WARNING
        - binance: WARNING
    
    Llama esta función si hay demasiados logs de librerías externas
    """
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext').setLevel(logging.WARNING)
    logging.getLogger('binance').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


# Configuración inicial al importar el módulo
def _setup_root_logger():
    """Configura el logger root al importar utils"""
    setup_logger()
    configure_third_party_loggers()

# Auto-configurar cuando se importa
_setup_root_logger()
