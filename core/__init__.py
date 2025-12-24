"""
Módulo Core del sistema de trading

Este módulo contiene los componentes principales:
- BinanceClient: Conexión y obtención de datos de Binance
- AIPredictor: Sistema de predicción con IA
- SignalGenerator: Generación y monitoreo de señales

Uso:
    from core import BinanceClient, AIPredictor, SignalGenerator
    
    client = BinanceClient()
    predictor = AIPredictor(weights)
    signal_gen = SignalGenerator(client, predictor)
"""

from .binance_client import BinanceClient
from .ai_predictor import AIPredictor
from .signal_generator import SignalGenerator

# Exportar clases públicas
__all__ = [
    'BinanceClient',
    'AIPredictor',
    'SignalGenerator'
]

# Versión del módulo
__version__ = '1.0.0'

# Metadata
__author__ = 'Trading Bot Team'
__description__ = 'Módulo core para análisis y generación de señales de trading'
