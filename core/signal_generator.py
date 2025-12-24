"""
Generador y monitor de señales de trading

Este módulo:
- Analiza símbolos con la estrategia
- Genera señales cuando hay oportunidad
- Monitorea señales activas
- Cierra señales cuando alcanzan objetivos
- Calcula resultados (P&L)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config.config import Config
from config.trading_params import TradingParams
from utils.json_manager import JSONManager
import logging

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Genera y monitorea señales de trading
    
    Workflow:
    1. Analizar símbolo → Generar señal
    2. Guardar en active_signals.json
    3. Monitorear hasta que alcance stop/target
    4. Guardar resultado en performance.json
    """
    
    def __init__(self, binance_client, strategy):
        """
        Inicializa el generador de señales
        
        Args:
            binance_client: Instancia de BinanceClient
            strategy: Instancia de ScalpingStrategy
        """
        self.binance = binance_client
        self.strategy = strategy
        self.params = TradingParams()
        
        # Cargar datos persistentes
        self.active_signals = JSONManager.load(Config.ACTIVE_SIGNALS_FILE, {})
        self.performance = JSONManager.load(Config.PERFORMANCE_FILE, [])
        
        logger.info("✅ Signal Generator inicializado")
        logger.info(f"   Señales activas: {len(self.active_signals)}")
        logger.info(f"   Historial: {len(self.performance)} señales")
    
    
    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Analiza un símbolo y genera señal si hay oportunidad
        
        Args:
            symbol: Símbolo a analizar (ej: 'BTCUSDT')
            
        Returns:
            Dict con datos de la señal o None si no hay señal
            
        Proceso:
        1. Obtener datos de Binance
        2. Calcular indicadores
        3. Analizar con estrategia
        4. Validar señal (cooldown)
        5. Guardar señal activa
        
        Ejemplo:
            >>> signal_gen = SignalGenerator(binance, strategy)
            >>> signal = await signal_gen.analyze_symbol('BTCUSDT')
            >>> if signal:
            >>>     print(f"Señal {signal['type']} generada")
        """
        try:
            logger.debug(f"🔍 Analizando {symbol}...")
            
            # 1. Obtener datos del mercado
            klines = self.binance.get_klines(
                symbol=symbol,
                interval=self.params.TIMEFRAME,
                limit=100
            )
            
            if not klines:
                logger.warning(f"⚠️  No se pudieron obtener datos de {symbol}")
                return None
            
            # 2. Convertir a DataFrame
            df = self._klines_to_dataframe(klines)
            
            # 3. Analizar con la estrategia
            signal_type, confidence, stops = self.strategy.analyze(df)
            
            # Si no hay señal, retornar None
            if signal_type == 'HOLD':
                logger.debug(f"   {symbol}: HOLD (confianza: {confidence:.0%})")
                return None
            
            # 4. Validar señal (cooldown para evitar duplicados)
            if not self.strategy.validate_signal(symbol, signal_type):
                logger.debug(f"   {symbol}: Señal en cooldown")
                return None
            
            # 5. Crear objeto de señal
            signal = self._create_signal(
                symbol, signal_type, confidence, stops
            )
            
            # 6. Guardar en señales activas
            self.active_signals[signal['signal_id']] = signal
            self._save_active_signals()
            
            logger.info(
                f"🎯 SEÑAL GENERADA: {signal_type} {symbol} @ "
                f"${signal['price']:.2f} ({confidence:.0%})"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error analizando {symbol}: {e}", exc_info=True)
            return None
    
    
    def _klines_to_dataframe(self, klines: List) -> pd.DataFrame:
        """
        Convierte datos de klines de Binance a DataFrame
        
        Args:
            klines: Lista de klines de Binance
            
        Returns:
            DataFrame con columnas OHLCV
        """
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convertir a numérico
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Convertir timestamp a datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    
    
    def _create_signal(self, symbol: str, signal_type: str, 
                      confidence: float, stops: Dict) -> Dict:
        """
        Crea el diccionario de señal con todos los datos
        
        Args:
            symbol: Símbolo del par
            signal_type: 'BUY' o 'SELL'
            confidence: Confianza (0.0 a 1.0)
            stops: Dict con stop_loss, take_profit, etc.
            
        Returns:
            Dict con toda la información de la señal
        """
        timestamp = datetime.now()
        
        signal = {
            'signal_id': f"{symbol}_{int(timestamp.timestamp())}",
            'symbol': symbol,
            'type': signal_type,
            'price': stops['entry_price'],
            'confidence': round(confidence, 3),
            'stop_loss': stops['stop_loss'],
            'take_profit': stops['take_profit'],
            'atr': stops['atr'],
            'risk_reward': stops.get('risk_reward', 0),
            'timestamp': timestamp.isoformat(),
            'status': 'ACTIVE',
            'created_at': timestamp.isoformat()
        }
        
        return signal
    
    
    async def monitor_active_signals(self) -> List[Dict]:
        """
        Monitorea todas las señales activas
        
        Verifica si alguna alcanzó:
        - Stop Loss (pérdida)
        - Take Profit (ganancia)
        
        Returns:
            Lista de señales cerradas en esta iteración
            
        Ejemplo:
            >>> closed = await signal_gen.monitor_active_signals()
            >>> for signal in closed:
            >>>     print(f"Señal cerrada: {signal['status']}")
        """
        if not self.active_signals:
            return []
        
        closed_signals = []
        
        logger.debug(f"👁️  Monitoreando {len(self.active_signals)} señales activas...")
        
        for signal_id, signal in list(self.active_signals.items()):
            try:
                # Obtener precio actual
                current_price = self.binance.get_current_price(signal['symbol'])
                
                if not current_price:
                    continue
                
                # Verificar si alcanzó stop loss o take profit
                status = self._check_signal_status(signal, current_price)
                
                if status in ['STOP_LOSS', 'TAKE_PROFIT']:
                    # Cerrar señal
                    closed_signal = self._close_signal(
                        signal, current_price, status
                    )
                    closed_signals.append(closed_signal)
                
                # Verificar si expiró por tiempo
                elif self._is_expired(signal):
                    closed_signal = self._close_signal(
                        signal, current_price, 'EXPIRED'
                    )
                    closed_signals.append(closed_signal)
                    
            except Exception as e:
                logger.error(f"❌ Error monitoreando señal {signal_id}: {e}")
        
        if closed_signals:
            logger.info(f"✅ {len(closed_signals)} señales cerradas")
        
        return closed_signals
    
    
    def _check_signal_status(self, signal: Dict, current_price: float) -> str:
        """
        Verifica el estado de una señal comparando con precio actual
        
        Args:
            signal: Dict de la señal
            current_price: Precio actual del mercado
            
        Returns:
            'STOP_LOSS', 'TAKE_PROFIT' o 'ACTIVE'
        """
        signal_type = signal['type']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        
        if signal_type == 'BUY':
            # Para señal BUY:
            # Stop loss si precio baja
            if current_price <= stop_loss:
                return 'STOP_LOSS'
            # Take profit si precio sube
            elif current_price >= take_profit:
                return 'TAKE_PROFIT'
        
        else:  # SELL
            # Para señal SELL:
            # Stop loss si precio sube
            if current_price >= stop_loss:
                return 'STOP_LOSS'
            # Take profit si precio baja
            elif current_price <= take_profit:
                return 'TAKE_PROFIT'
        
        return 'ACTIVE'
    
    
    def _is_expired(self, signal: Dict) -> bool:
        """
        Verifica si una señal expiró por tiempo
        
        Args:
            signal: Dict de la señal
            
        Returns:
            True si expiró
        """
        created = datetime.fromisoformat(signal['created_at'])
        now = datetime.now()
        hours_active = (now - created).total_seconds() / 3600
        
        return hours_active > self.params.MAX_SIGNAL_LIFETIME_HOURS
    
    
    def _close_signal(self, signal: Dict, close_price: float, 
                     status: str) -> Dict:
        """
        Cierra una señal y calcula resultados
        
        Args:
            signal: Dict de la señal
            close_price: Precio de cierre
            status: 'STOP_LOSS', 'TAKE_PROFIT' o 'EXPIRED'
            
        Returns:
            Señal cerrada con resultados
        """
        # Actualizar datos de cierre
        signal['close_price'] = close_price
        signal['close_time'] = datetime.now().isoformat()
        signal['status'] = status
        
        # Calcular P&L (Profit & Loss)
        entry_price = signal['price']
        
        if signal['type'] == 'BUY':
            # Para BUY: ganancia si sube
            pnl_percent = ((close_price - entry_price) / entry_price) * 100
        else:  # SELL
            # Para SELL: ganancia si baja
            pnl_percent = ((entry_price - close_price) / entry_price) * 100
        
        signal['pnl_percent'] = round(pnl_percent, 2)
        
        # Calcular duración
        created = datetime.fromisoformat(signal['created_at'])
        closed = datetime.fromisoformat(signal['close_time'])
        duration_minutes = (closed - created).total_seconds() / 60
        signal['duration_minutes'] = round(duration_minutes, 1)
        
        # Guardar en historial de performance
        self.performance.append(signal)
        self._save_performance()
        
        # Eliminar de señales activas
        del self.active_signals[signal['signal_id']]
        self._save_active_signals()
        
        # Log del resultado
        emoji = "✅" if status == 'TAKE_PROFIT' else "❌" if status == 'STOP_LOSS' else "⏱️"
        logger.info(
            f"{emoji} Señal cerrada: {signal['symbol']} - "
            f"{status} ({pnl_percent:+.2f}%) en {duration_minutes:.0f}min"
        )
        
        return signal
    
    
    def get_performance_stats(self, days: int = 7) -> Optional[Dict]:
        """
        Calcula estadísticas de performance
        
        Args:
            days: Número de días a analizar
            
        Returns:
            Dict con estadísticas o None si no hay datos
            
        Estadísticas incluidas:
        - Total de señales
        - Ganadoras vs perdedoras
        - Win rate
        - Ganancia/pérdida promedio
        - Profit factor
        """
        if not self.performance:
            return None
        
        # Filtrar por días
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            s for s in self.performance
            if datetime.fromisoformat(s['close_time']) > cutoff
        ]
        
        if not recent:
            return None
        
        # Calcular estadísticas
        total = len(recent)
        winners = [s for s in recent if s['pnl_percent'] > 0]
        losers = [s for s in recent if s['pnl_percent'] <= 0]
        
        win_count = len(winners)
        loss_count = len(losers)
        
        avg_win = sum(s['pnl_percent'] for s in winners) / win_count if win_count > 0 else 0
        avg_loss = sum(s['pnl_percent'] for s in losers) / loss_count if loss_count > 0 else 0
        
        # Profit factor = (ganancia total / pérdida total)
        total_wins = sum(s['pnl_percent'] for s in winners)
        total_losses = abs(sum(s['pnl_percent'] for s in losers))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        return {
            'total_signals': total,
            'winners': win_count,
            'losers': loss_count,
            'win_rate': win_count / total if total > 0 else 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': sum(s['pnl_percent'] for s in recent)
        }
    
    
    def _save_active_signals(self):
        """Guarda señales activas en JSON"""
        JSONManager.save(Config.ACTIVE_SIGNALS_FILE, self.active_signals)
    
    
    def _save_performance(self):
        """Guarda historial de performance en JSON"""
        JSONManager.save(Config.PERFORMANCE_FILE, self.performance)
    
    
    def get_active_signals_list(self) -> List[Dict]:
        """Retorna lista de señales activas"""
        return list(self.active_signals.values())
    
    
    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        """Obtiene una señal específica por ID"""
        return self.active_signals.get(signal_id)
