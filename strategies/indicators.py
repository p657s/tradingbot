"""
Indicadores técnicos para análisis de trading

Calcula todos los indicadores técnicos necesarios:
- EMAs (Exponential Moving Averages)
- RSI (Relative Strength Index)
- Bollinger Bands
- VWAP (Volume Weighted Average Price)
- ATR (Average True Range)
- Volume Analysis
- Price Action

Usa la librería 'ta' (Technical Analysis) para cálculos precisos
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from config.trading_params import TradingParams
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calcula indicadores técnicos sobre datos OHLCV
    
    Todos los cálculos se basan en datos REALES del mercado
    """
    
    def __init__(self):
        """Inicializa el calculador de indicadores"""
        self.params = TradingParams()
        logger.info("✅ Technical Indicators inicializado")
    
    
    def calculate_all(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Calcula TODOS los indicadores técnicos sobre un DataFrame
        
        Args:
            df: DataFrame con columnas: open, high, low, close, volume
            
        Returns:
            DataFrame con indicadores agregados o None si hay error
            
        Indicadores agregados:
            - ema_fast, ema_slow: EMAs para tendencia
            - rsi: Momentum
            - bb_upper, bb_middle, bb_lower, bb_width: Bollinger Bands
            - vwap: Volume Weighted Average Price
            - volume_ma, volume_ratio: Análisis de volumen
            - atr: Average True Range (para stops)
            - price_change, momentum: Price action
            
        Ejemplo:
            >>> indicators = TechnicalIndicators()
            >>> df_with_indicators = indicators.calculate_all(df)
            >>> print(df_with_indicators[['close', 'ema_fast', 'rsi']].tail())
        """
        if df is None or len(df) == 0:
            logger.error("❌ DataFrame vacío o None")
            return None
        
        try:
            # Verificar columnas requeridas
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_columns if col not in df.columns]
            
            if missing:
                logger.error(f"❌ Faltan columnas requeridas: {missing}")
                return None
            
            # Hacer copia para no modificar el original
            df = df.copy()
            
            # Calcular cada grupo de indicadores
            df = self._calculate_emas(df)
            df = self._calculate_rsi(df)
            df = self._calculate_bollinger_bands(df)
            df = self._calculate_vwap(df)
            df = self._calculate_volume_analysis(df)
            df = self._calculate_atr(df)
            df = self._calculate_price_action(df)
            
            logger.debug(f"✅ {len(df)} velas con indicadores calculados")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error calculando indicadores: {e}", exc_info=True)
            return None
    
    
    # =======================================================================
    # CÁLCULO DE INDICADORES INDIVIDUALES
    # =======================================================================
    
    def _calculate_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula EMAs (Exponential Moving Averages) para detectar tendencia
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con ema_fast y ema_slow agregadas
        """
        try:
            # EMA rápida (corto plazo)
            ema_fast_indicator = EMAIndicator(
                close=df['close'], 
                window=self.params.EMA_FAST,
                fillna=True
            )
            df['ema_fast'] = ema_fast_indicator.ema_indicator()
            
            # EMA lenta (largo plazo)
            ema_slow_indicator = EMAIndicator(
                close=df['close'], 
                window=self.params.EMA_SLOW,
                fillna=True
            )
            df['ema_slow'] = ema_slow_indicator.ema_indicator()
            
            logger.debug(
                f"  ✓ EMAs calculadas "
                f"(fast={self.params.EMA_FAST}, slow={self.params.EMA_SLOW})"
            )
            
        except Exception as e:
            logger.error(f"Error calculando EMAs: {e}")
        
        return df
    
    
    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula RSI (Relative Strength Index) para momentum
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con rsi agregado
            
        RSI:
            - < 30: Sobrevendido (posible rebote alcista)
            - > 70: Sobrecomprado (posible caída)
            - 30-70: Zona neutral
        """
        try:
            rsi_indicator = RSIIndicator(
                close=df['close'],
                window=self.params.RSI_PERIOD,
                fillna=True
            )
            df['rsi'] = rsi_indicator.rsi()
            
            logger.debug(f"  ✓ RSI calculado (period={self.params.RSI_PERIOD})")
            
        except Exception as e:
            logger.error(f"Error calculando RSI: {e}")
        
        return df
    
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula Bandas de Bollinger para volatilidad
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con bb_upper, bb_middle, bb_lower, bb_width
            
        Bollinger Bands:
            - bb_upper: Banda superior (resistencia)
            - bb_middle: Media móvil central
            - bb_lower: Banda inferior (soporte)
            - bb_width: Ancho de las bandas (volatilidad)
        """
        try:
            bollinger = BollingerBands(
                close=df['close'],
                window=self.params.BOLLINGER_PERIOD,
                window_dev=self.params.BOLLINGER_STD,
                fillna=True
            )
            
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_lower'] = bollinger.bollinger_lband()
            
            # Ancho de las bandas (indicador de volatilidad)
            # bb_width > 0.02 indica alta volatilidad
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            logger.debug(
                f"  ✓ Bollinger Bands calculadas "
                f"(period={self.params.BOLLINGER_PERIOD}, std={self.params.BOLLINGER_STD})"
            )
            
        except Exception as e:
            logger.error(f"Error calculando Bollinger Bands: {e}")
        
        return df
    
    
    def _calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula VWAP (Volume Weighted Average Price)
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con vwap agregado
            
        VWAP:
            - Precio promedio ponderado por volumen
            - Si precio > VWAP → Alcista
            - Si precio < VWAP → Bajista
            - Los institucionales lo usan como referencia
        """
        try:
            # VWAP = Suma(Precio típico × Volumen) / Suma(Volumen)
            # Precio típico = (High + Low + Close) / 3
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            
            df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
            
            logger.debug("  ✓ VWAP calculado")
            
        except Exception as e:
            logger.error(f"Error calculando VWAP: {e}")
        
        return df
    
    
    def _calculate_volume_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analiza el volumen de trading
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con volume_ma y volume_ratio
            
        Volume Analysis:
            - volume_ma: Promedio móvil del volumen (20 períodos)
            - volume_ratio: Volumen actual / Promedio
            - volume_ratio > 1.5 indica actividad inusual
        """
        try:
            # Promedio móvil del volumen (20 períodos)
            df['volume_ma'] = df['volume'].rolling(window=20, min_periods=1).mean()
            
            # Ratio: volumen actual vs promedio
            # > 1.5 = Alto volumen (confirma señales)
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # Reemplazar NaN e infinitos (SIN inplace=True)
            df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
            df['volume_ratio'] = df['volume_ratio'].replace([np.inf, -np.inf], 1.0)
            
            logger.debug("  ✓ Análisis de volumen calculado")
            
        except Exception as e:
            logger.error(f"Error calculando análisis de volumen: {e}")
        
        return df
    
    
    def _calculate_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula ATR (Average True Range) para volatilidad
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con atr y tr (True Range)
            
        ATR:
            - Mide la volatilidad del mercado
            - Se usa para calcular stops dinámicos
            - Stop Loss = Precio ± (2 × ATR)
            - Take Profit = Precio ± (3 × ATR)
        """
        try:
            # True Range: máximo de:
            # 1. High - Low
            # 2. |High - Close anterior|
            # 3. |Low - Close anterior|
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            
            # ATR = Promedio móvil del True Range
            atr_indicator = AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=self.params.ATR_PERIOD,
                fillna=True
            )
            df['atr'] = atr_indicator.average_true_range()
            
            logger.debug(f"  ✓ ATR calculado (period={self.params.ATR_PERIOD})")
            
        except Exception as e:
            logger.error(f"Error calculando ATR: {e}")
        
        return df
    
    
    def _calculate_price_action(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores de acción del precio
        
        Args:
            df: DataFrame con datos
            
        Returns:
            DataFrame con price_change y momentum
            
        Price Action:
            - price_change: Cambio porcentual vela a vela
            - momentum: Diferencia de precio en 4 velas
            - Detecta aceleración o desaceleración
        """
        try:
            # Cambio porcentual del precio (vela actual vs anterior)
            df['price_change'] = df['close'].pct_change()
            
            # Promedio móvil del cambio de precio
            df['price_change_ma'] = df['price_change'].rolling(window=5, min_periods=1).mean()
            
            # Momentum: diferencia de precio en 4 períodos
            # Positivo = alcista, Negativo = bajista
            df['momentum'] = df['close'] - df['close'].shift(4)
            
            # Reemplazar NaN (SIN inplace=True)
            df['price_change'] = df['price_change'].fillna(0)
            df['price_change_ma'] = df['price_change_ma'].fillna(0)
            df['momentum'] = df['momentum'].fillna(0)
            
            logger.debug("  ✓ Price action calculado")
            
        except Exception as e:
            logger.error(f"Error calculando price action: {e}")
        
        return df
    
    
    # =======================================================================
    # MÉTODOS AUXILIARES
    # =======================================================================
    
    def get_trend(self, df: pd.DataFrame) -> str:
        """
        Determina la tendencia actual del mercado
        
        Args:
            df: DataFrame con indicadores calculados
            
        Returns:
            'BULLISH', 'BEARISH' o 'NEUTRAL'
            
        Ejemplo:
            >>> trend = indicators.get_trend(df)
            >>> print(f"Tendencia: {trend}")
            Tendencia: BULLISH
        """
        if df is None or len(df) == 0 or 'ema_fast' not in df.columns:
            return 'NEUTRAL'
        
        latest = df.iloc[-1]
        
        # Comparar EMAs con margen del 1%
        if latest['ema_fast'] > latest['ema_slow'] * 1.01:
            return 'BULLISH'
        elif latest['ema_fast'] < latest['ema_slow'] * 0.99:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    
    def get_volatility(self, df: pd.DataFrame) -> float:
        """
        Calcula la volatilidad actual del mercado
        
        Args:
            df: DataFrame con indicadores
            
        Returns:
            Volatilidad como float (ancho de Bollinger Bands)
            
        Interpretación:
            - < 0.02: Baja volatilidad
            - 0.02 - 0.05: Volatilidad normal
            - > 0.05: Alta volatilidad
        """
        if df is None or len(df) == 0 or 'bb_width' not in df.columns:
            return 0.0
        
        latest = df.iloc[-1]
        return float(latest['bb_width'])
    
    
    def get_market_summary(self, df: pd.DataFrame, symbol: str) -> dict:
        """
        Genera resumen del mercado con todos los indicadores
        
        Args:
            df: DataFrame con indicadores
            symbol: Símbolo analizado
            
        Returns:
            Dict con resumen completo
        """
        if df is None or len(df) == 0:
            return {'error': 'No data'}
        
        latest = df.iloc[-1]
        trend = self.get_trend(df)
        volatility = self.get_volatility(df)
        
        return {
            'symbol': symbol,
            'price': float(latest['close']),
            'trend': trend,
            'volatility': volatility,
            'indicators': {
                'ema_fast': float(latest['ema_fast']),
                'ema_slow': float(latest['ema_slow']),
                'rsi': float(latest['rsi']),
                'bb_upper': float(latest['bb_upper']),
                'bb_lower': float(latest['bb_lower']),
                'vwap': float(latest['vwap']),
                'atr': float(latest['atr']),
                'volume_ratio': float(latest['volume_ratio'])
            }
        }
    
    
    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """
        Valida que los indicadores se calcularon correctamente
        
        Args:
            df: DataFrame con indicadores
            
        Returns:
            True si los datos son válidos
        """
        if df is None or len(df) == 0:
            return False
        
        required_indicators = [
            'ema_fast', 'ema_slow', 'rsi', 'bb_upper', 'bb_lower',
            'vwap', 'atr', 'volume_ratio'
        ]
        
        # Verificar que existan las columnas
        missing = [ind for ind in required_indicators if ind not in df.columns]
        if missing:
            logger.warning(f"⚠️  Indicadores faltantes: {missing}")
            return False
        
        # Verificar que no haya demasiados NaN
        latest = df.iloc[-1]
        nan_count = latest[required_indicators].isna().sum()
        
        if nan_count > 0:
            logger.warning(f"⚠️  {nan_count} indicadores con NaN en última vela")
            return False
        
        return True
