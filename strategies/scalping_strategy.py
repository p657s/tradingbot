"""
Estrategia de scalping profesional

Esta estrategia está diseñada para:
- Identificar oportunidades de scalping en timeframes cortos (1m, 5m)
- Usar múltiples indicadores para confirmación
- Generar señales con alta probabilidad de éxito
- Calcular stops dinámicos basados en volatilidad (ATR)

NO ejecuta operaciones, solo genera señales que se envían a usuarios
"""

import pandas as pd
from datetime import datetime, timedelta
from config.trading_params import TradingParams
from .indicators import TechnicalIndicators
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ScalpingStrategy:
    """
    Estrategia de scalping con múltiples confirmaciones
    
    Analiza el mercado usando:
    - Tendencia (EMAs)
    - Momentum (RSI)
    - Volatilidad (Bollinger Bands)
    - Volumen (confirmación)
    - Precio (VWAP y price action)
    
    Retorna señales BUY/SELL con confianza y stops calculados
    """
    
    def __init__(self):
        """Inicializa la estrategia de scalping"""
        self.params = TradingParams()
        self.indicators = TechnicalIndicators()
        self.last_signals = {}  # Para cooldown
        
        logger.info("✅ Estrategia de Scalping inicializada")
        logger.info(f"   Confianza mínima: {self.params.MIN_CONFIDENCE:.0%}")
        logger.info(f"   Volumen mínimo: {self.params.MIN_VOLUME_RATIO}x")
        logger.info(f"   Cooldown: {self.params.SIGNAL_COOLDOWN_MINUTES} min")
    
    
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Optional[Dict]]:
        """
        Analiza el mercado y genera señal de trading
        
        Args:
            df: DataFrame con datos OHLCV (ya debe tener indicadores calculados)
            
        Returns:
            Tupla (signal_type, confidence, stops)
            - signal_type: 'BUY', 'SELL' o 'HOLD'
            - confidence: 0.0 a 1.0 (0% a 100%)
            - stops: Dict con stop_loss, take_profit, entry_price, atr
                    o None si es HOLD
        
        Ejemplo:
            >>> strategy = ScalpingStrategy()
            >>> signal, confidence, stops = strategy.analyze(df)
            >>> if signal != 'HOLD':
            >>>     print(f"{signal} con {confidence:.0%} confianza")
            >>>     print(f"Entry: ${stops['entry_price']}")
            >>>     print(f"Stop: ${stops['stop_loss']}")
        """
        # Validar datos
        if df is None or len(df) < 50:
            logger.warning("⚠️  Datos insuficientes para análisis (mínimo 50 velas)")
            return 'HOLD', 0.0, None
        
        # Asegurar que los indicadores estén calculados
        if not self.indicators.validate_data_quality(df):
            logger.warning("⚠️  Calculando indicadores faltantes...")
            df = self.indicators.calculate_all(df)
            
            if df is None:
                return 'HOLD', 0.0, None
        
        # Generar señal basada en scoring
        signal_type, confidence = self._generate_signal(df)
        
        # Si es HOLD, no calcular stops
        if signal_type == 'HOLD':
            return signal_type, confidence, None
        
        # Calcular stops dinámicos
        stops = self._calculate_stops(df, signal_type)
        
        return signal_type, confidence, stops
    
    
    def _generate_signal(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        Genera señal basada en sistema de scoring
        
        Analiza 6 aspectos del mercado:
        1. Tendencia EMA (25%)
        2. RSI Momentum (20%)
        3. Bollinger Bands (15%)
        4. VWAP (15%)
        5. Volumen (15%)
        6. Price Action (10%)
        
        Args:
            df: DataFrame con indicadores
            
        Returns:
            Tupla (signal_type, confidence)
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        buy_score = 0.0
        sell_score = 0.0
        
        weights = self.params.WEIGHTS
        
        
        # ===================================================================
        # 1. TENDENCIA EMA (25%)
        # ===================================================================
        ema_fast = latest['ema_fast']
        ema_slow = latest['ema_slow']
        prev_fast = prev['ema_fast']
        prev_slow = prev['ema_slow']
        
        # Tendencia alcista
        if ema_fast > ema_slow:
            buy_score += weights['ema_trend']
            
            # Bonus: Golden cross reciente (cruce alcista)
            if prev_fast <= prev_slow:
                buy_score += 0.05
                logger.debug("  🔔 Golden cross detectado")
        
        # Tendencia bajista
        elif ema_fast < ema_slow:
            sell_score += weights['ema_trend']
            
            # Bonus: Death cross reciente (cruce bajista)
            if prev_fast >= prev_slow:
                sell_score += 0.05
                logger.debug("  🔔 Death cross detectado")
        
        
        # ===================================================================
        # 2. RSI MOMENTUM (20%)
        # ===================================================================
        rsi = latest['rsi']
        
        if rsi < self.params.RSI_OVERSOLD:
            # Sobrevendido - probable rebote
            buy_score += weights['rsi_momentum']
            logger.debug(f"  📉 RSI sobrevendido: {rsi:.1f}")
            
        elif rsi > self.params.RSI_OVERBOUGHT:
            # Sobrecomprado - probable caída
            sell_score += weights['rsi_momentum']
            logger.debug(f"  📈 RSI sobrecomprado: {rsi:.1f}")
            
        elif 40 < rsi < 60:
            # RSI neutral - no sumar puntos
            pass
            
        elif rsi < 50:
            # Ligeramente bajista
            buy_score += weights['rsi_momentum'] * 0.5
            
        else:
            # Ligeramente alcista
            sell_score += weights['rsi_momentum'] * 0.5
        
        
        # ===================================================================
        # 3. BOLLINGER BANDS (15%)
        # ===================================================================
        close = latest['close']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_width = latest['bb_width']
        
        # Solo considerar si hay volatilidad suficiente
        if bb_width > self.params.MIN_VOLATILITY:
            
            # Precio en banda inferior (probable rebote)
            if close <= bb_lower:
                buy_score += weights['bollinger']
                logger.debug(f"  📊 Precio tocando banda inferior")
            
            # Precio en banda superior (probable retroceso)
            elif close >= bb_upper:
                sell_score += weights['bollinger']
                logger.debug(f"  📊 Precio tocando banda superior")
        
        else:
            logger.debug(f"  ⚠️  Volatilidad baja ({bb_width:.4f}), Bollinger ignorado")
        
        
        # ===================================================================
        # 4. VWAP (15%)
        # ===================================================================
        vwap = latest['vwap']
        prev_close = prev['close']
        prev_vwap = prev['vwap']
        
        # Cruce alcista (precio cruza por encima de VWAP)
        if close > vwap and prev_close <= prev_vwap:
            buy_score += weights['vwap']
            logger.debug("  🔄 Cruce alcista de VWAP")
        
        # Cruce bajista (precio cruza por debajo de VWAP)
        elif close < vwap and prev_close >= prev_vwap:
            sell_score += weights['vwap']
            logger.debug("  🔄 Cruce bajista de VWAP")
        
        # Precio muy por encima de VWAP
        elif close > vwap * 1.001:
            buy_score += weights['vwap'] * 0.5
        
        # Precio muy por debajo de VWAP
        elif close < vwap * 0.999:
            sell_score += weights['vwap'] * 0.5
        
        
        # ===================================================================
        # 5. VOLUMEN (15%)
        # ===================================================================
        volume_ratio = latest['volume_ratio']
        
        # Alto volumen confirma la dirección actual
        if volume_ratio > self.params.MIN_VOLUME_RATIO:
            logger.debug(f"  🔊 Alto volumen detectado ({volume_ratio:.1f}x)")
            
            # Confirma la dirección que ya está ganando
            if buy_score > sell_score:
                buy_score += weights['volume']
            elif sell_score > buy_score:
                sell_score += weights['volume']
        
        
        # ===================================================================
        # 6. PRICE ACTION (10%)
        # ===================================================================
        price_change = latest['price_change']
        
        # Momentum alcista fuerte (+0.2% o más)
        if price_change > 0.002:
            buy_score += weights['price_action']
            logger.debug(f"  ⚡ Momentum alcista: {price_change*100:+.2f}%")
        
        # Momentum bajista fuerte (-0.2% o más)
        elif price_change < -0.002:
            sell_score += weights['price_action']
            logger.debug(f"  ⚡ Momentum bajista: {price_change*100:+.2f}%")
        
        
        # ===================================================================
        # DECISIÓN FINAL
        # ===================================================================
        confidence = max(buy_score, sell_score)
        
        # Verificar confianza mínima
        if confidence < self.params.MIN_CONFIDENCE:
            logger.debug(
                f"  ❌ Confianza insuficiente: {confidence:.0%} "
                f"(mínimo: {self.params.MIN_CONFIDENCE:.0%})"
            )
            return 'HOLD', confidence
        
        # Decidir señal
        if buy_score > sell_score:
            logger.info(
                f"  ✅ SEÑAL BUY - Confianza: {buy_score:.0%} "
                f"(Buy: {buy_score:.2f}, Sell: {sell_score:.2f})"
            )
            return 'BUY', buy_score
            
        elif sell_score > buy_score:
            logger.info(
                f"  ✅ SEÑAL SELL - Confianza: {sell_score:.0%} "
                f"(Sell: {sell_score:.2f}, Buy: {buy_score:.2f})"
            )
            return 'SELL', sell_score
            
        else:
            # Empate
            return 'HOLD', confidence
    
    
    def _calculate_stops(self, df: pd.DataFrame, signal_type: str) -> Dict:
        """
        Calcula stop loss y take profit dinámicos basados en ATR
        
        Args:
            df: DataFrame con indicadores (debe tener ATR)
            signal_type: 'BUY' o 'SELL'
            
        Returns:
            Dict con:
                - entry_price: Precio de entrada sugerido
                - stop_loss: Precio de stop loss
                - take_profit: Precio de take profit
                - atr: ATR usado para cálculo
                - risk_reward: Ratio riesgo/recompensa
        
        Lógica:
            - Stop Loss = Entrada ± (2 × ATR)
            - Take Profit = Entrada ± (3 × ATR)
            - Esto da un ratio Risk/Reward de 1:1.5
        """
        latest = df.iloc[-1]
        entry_price = float(latest['close'])
        atr = float(latest['atr'])
        
        # Usar ATR para stops dinámicos (se ajustan a la volatilidad)
        stop_distance = atr * self.params.STOP_LOSS_MULTIPLIER
        profit_distance = atr * self.params.TAKE_PROFIT_MULTIPLIER
        
        if signal_type == 'BUY':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + profit_distance
            
        else:  # SELL
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - profit_distance
        
        # Calcular ratio riesgo/recompensa
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        stops = {
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'atr': round(atr, 2),
            'risk_reward': round(risk_reward, 2)
        }
        
        logger.debug(
            f"  📍 Stops calculados: "
            f"Entry ${stops['entry_price']}, "
            f"SL ${stops['stop_loss']}, "
            f"TP ${stops['take_profit']} "
            f"(R:R 1:{stops['risk_reward']})"
        )
        
        return stops
    
    
    def calculate_position_size(self, capital: float, entry_price: float, 
                                stop_loss: float, risk_percent: float = 0.02) -> float:
        """
        Calcula el tamaño de posición recomendado basado en riesgo
        
        Esta función es INFORMATIVA para los usuarios
        El bot NO ejecuta trades
        
        Args:
            capital: Capital disponible del usuario
            entry_price: Precio de entrada
            stop_loss: Precio de stop loss
            risk_percent: Porcentaje de riesgo (default 2%)
            
        Returns:
            Cantidad de unidades recomendadas
            
        Ejemplo:
            >>> strategy = ScalpingStrategy()
            >>> size = strategy.calculate_position_size(
            >>>     capital=10000,
            >>>     entry_price=95500,
            >>>     stop_loss=95200,
            >>>     risk_percent=0.02
            >>> )
            >>> print(f"Tamaño recomendado: {size} unidades")
        """
        # Cantidad de dinero a arriesgar
        risk_amount = capital * risk_percent
        
        # Distancia del stop (cuánto se pierde si salta el stop)
        price_difference = abs(entry_price - stop_loss)
        
        if price_difference == 0:
            logger.warning("⚠️  Stop loss = precio de entrada, no se puede calcular")
            return 0
        
        # Cantidad de unidades = Riesgo / Distancia del stop
        quantity = risk_amount / price_difference
        
        # Redondear a 3 decimales
        quantity = round(quantity, 3)
        
        logger.debug(
            f"  💰 Position size: {quantity} unidades "
            f"(Capital: ${capital}, Riesgo: {risk_percent:.0%})"
        )
        
        return quantity
    
    
    def validate_signal(self, symbol: str, signal_type: str, 
                        cooldown_minutes: Optional[int] = None) -> bool:
        """
        Valida si se debe emitir la señal (evita duplicados)
        
        Implementa cooldown: no envía la misma señal del mismo símbolo
        si ya se envió hace menos de X minutos
        
        Args:
            symbol: Símbolo del par (ej: 'BTCUSDT')
            signal_type: 'BUY' o 'SELL'
            cooldown_minutes: Minutos de cooldown (usa config si None)
            
        Returns:
            True si la señal es válida (puede enviarse)
            False si está en cooldown
        """
        if cooldown_minutes is None:
            cooldown_minutes = self.params.SIGNAL_COOLDOWN_MINUTES
        
        # Clave única para este símbolo y tipo
        key = f"{symbol}_{signal_type}"
        
        # Si nunca se ha enviado, es válida
        if key not in self.last_signals:
            self.last_signals[key] = datetime.now()
            return True
        
        # Calcular tiempo desde última señal
        last_time = self.last_signals[key]
        time_diff = datetime.now() - last_time
        
        # Si ya pasó el cooldown, es válida
        if time_diff.total_seconds() > (cooldown_minutes * 60):
            self.last_signals[key] = datetime.now()
            return True
        
        # Está en cooldown
        remaining = cooldown_minutes - (time_diff.total_seconds() / 60)
        logger.info(
            f"  ⏸️  Señal {key} en cooldown "
            f"({remaining:.1f} min restantes)"
        )
        return False
    
    
    def get_stats(self) -> Dict:
        """
        Retorna estadísticas de la estrategia
        
        Returns:
            Dict con información de configuración
        """
        return {
            'name': 'Scalping Strategy',
            'timeframe': self.params.TIMEFRAME,
            'min_confidence': self.params.MIN_CONFIDENCE,
            'min_volume_ratio': self.params.MIN_VOLUME_RATIO,
            'cooldown_minutes': self.params.SIGNAL_COOLDOWN_MINUTES,
            'stop_loss_multiplier': self.params.STOP_LOSS_MULTIPLIER,
            'take_profit_multiplier': self.params.TAKE_PROFIT_MULTIPLIER,
            'indicators': {
                'ema_fast': self.params.EMA_FAST,
                'ema_slow': self.params.EMA_SLOW,
                'rsi_period': self.params.RSI_PERIOD,
                'bollinger_period': self.params.BOLLINGER_PERIOD,
                'atr_period': self.params.ATR_PERIOD
            },
            'weights': self.params.WEIGHTS
        }
