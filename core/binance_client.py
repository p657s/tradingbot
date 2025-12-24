"""
Cliente de Binance Futures

Maneja toda la comunicación con la API de Binance Futures
para obtener datos de mercado en TIEMPO REAL.

⚠️ IMPORTANTE: Este cliente solo LEE datos del mercado
NO ejecuta operaciones, NO toca cuentas de usuarios
"""

from binance.client import Client
from binance.exceptions import BinanceAPIException
from config.config import Config
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class BinanceClient:
    """
    Cliente para interactuar con Binance Futures API
    
    Funciones:
    - Obtener precios en tiempo real
    - Obtener datos históricos (klines/velas)
    - Obtener estadísticas de 24h
    - Verificar conectividad
    
    NO ejecuta trades, solo lectura de datos
    """
    
    def __init__(self):
        """
        Inicializa el cliente de Binance Futures
        
        Requiere:
            - Config.BINANCE_API_KEY
            - Config.BINANCE_API_SECRET
        """
        self.api_key = Config.BINANCE_API_KEY
        self.api_secret = Config.BINANCE_API_SECRET
        
        # Crear cliente de Binance
        self.client = Client(self.api_key, self.api_secret)
        
        logger.info("🔗 Inicializando Binance Futures Client...")
        self._verify_connection()
    
    
    def _verify_connection(self):
        """Verifica la conexión con Binance"""
        try:
            # Test de conectividad
            self.client.ping()
            logger.info("  ✅ Ping exitoso")
            
            # Test de tiempo del servidor
            server_time = self.client.get_server_time()
            logger.info(f"  ✅ Hora del servidor: {server_time['serverTime']}")
            
            # Test de exchange info
            exchange_info = self.client.futures_exchange_info()
            logger.info(f"  ✅ Exchange info obtenida: {len(exchange_info['symbols'])} símbolos disponibles")
            
            logger.info("✅ Conexión con Binance Futures establecida correctamente")
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error conectando con Binance: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            raise
    
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> Optional[List]:
        """Obtiene datos históricos de velas (klines)"""
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            logger.debug(f"📊 Obtenidas {len(klines)} velas de {symbol} ({interval})")
            return klines
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error obteniendo klines de {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return None
    
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Obtiene el precio actual"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            logger.debug(f"💰 Precio actual de {symbol}: ${price:.2f}")
            return price
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error obteniendo precio de {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return None
    
    
    def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """Obtiene estadísticas de 24 horas"""
        try:
            ticker = self.client.futures_ticker(symbol=symbol)
            
            stats = {
                'symbol': ticker['symbol'],
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'weighted_avg_price': float(ticker['weightedAvgPrice']),
                'last_price': float(ticker['lastPrice']),
                'high_price': float(ticker['highPrice']),
                'low_price': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume']),
                'open_time': ticker['openTime'],
                'close_time': ticker['closeTime'],
                'count': ticker['count']
            }
            
            return stats
            
        except BinanceAPIException as e:
            logger.error(f"❌ Error obteniendo ticker: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return None
    
    
    def test_connectivity(self) -> bool:
        """Prueba la conectividad"""
        try:
            self.client.ping()
            logger.info("✅ Test de conectividad exitoso")
            return True
        except Exception as e:
            logger.error(f"❌ Test fallido: {e}")
            return False
    
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """Obtiene información del exchange"""
        try:
            info = self.client.futures_exchange_info()
            
            if symbol:
                for s in info['symbols']:
                    if s['symbol'] == symbol:
                        return s
                return None
            
            return info
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo info: {e}")
            return None
