
from .subscriber_manager import SubscriberManager
from .signal_distributor import SignalDistributor

# Exportar clases públicas
__all__ = [
    'SubscriberManager',
    'SignalDistributor'
]

# Versión del módulo
__version__ = '1.0.0'

# Metadata
__author__ = 'Trading Bot Team'
__description__ = 'Sistema de gestión de suscriptores y distribución de señales'