"""
Módulo de utilidades

Herramientas auxiliares para el sistema:
- Logger: Sistema de logging profesional
- JSONManager: Gestión de archivos JSON

Uso:
    from utils import setup_logger, JSONManager
    
    # Configurar logging
    logger = setup_logger()
    
    # Manejar archivos JSON
    data = JSONManager.load('data.json', default={})
    JSONManager.save('data.json', data)
"""

from .logger import setup_logger
from .json_manager import JSONManager

# Exportar funciones públicas
__all__ = [
    'setup_logger',
    'JSONManager'
]

# Versión del módulo
__version__ = '1.0.0'

# Metadata
__author__ = 'Trading Bot Team'
__description__ = 'Utilidades y herramientas auxiliares'
