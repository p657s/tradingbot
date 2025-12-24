"""
Predictor de IA para análisis de mercado

Este módulo implementa el sistema de "IA" que analiza datos reales
y predice movimientos del mercado con porcentaje de confianza.

NO es magia, es análisis técnico automatizado con machine learning básico.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AIPredictor:
    """
    Sistema de predicción con IA para trading
    
    Analiza múltiples indicadores técnicos y genera:
    - Predicción: BUY, SELL o HOLD
    - Confianza: 0% a 100%
    - Razones: Por qué tomó esa decisión
    """
    
    def __init__(self, weights: Dict[str, float]):
        """
        Inicializa el predictor de IA
        
        Args:
            weights: Pesos de cada indicador (deben sumar 1.0)
        """
        self.weights = weights
        self.prediction_history = []
        
        # Validar pesos
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Los pesos deben sumar 1.0, actualmente: {total}")
        
        logger.info("✅ AI Predictor inicializado")
    
    
    def predict(self, df: pd.DataFrame, symbol: str) -> Tuple[str, float, Dict]:
        """
        Predice la dirección del mercado basándose en indicadores
        
        Args:
            df: DataFrame con indicadores calculados
            symbol: Símbolo analizado (ej: 'BTCUSDT')
            
        Returns:
            Tupla (prediction, confidence, analysis)
            - prediction: 'BUY', 'SELL' o 'HOLD'
            - confidence: 0.0 a 1.0 (0% a 100%)
            - analysis: Dict con detalles del análisis
        """
        if df is None or len(df) < 2:
            return 'HOLD', 0.0, {'error': 'Datos insuficientes'}
        
        # Obtener última vela y anterior
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Inicializar scores
        buy_score = 0.0
        sell_score = 0.0
        
        # Diccionario para guardar análisis detallado
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': float(latest['close']),
            'indicators': {},
            'signals': []
        }
        
        # ===================================================================
        # ANÁLISIS 1: TENDENCIA EMA (25%)
        # ===================================================================
        ema_signal, ema_strength = self._analyze_ema_trend(latest, prev)
        
        if ema_signal == 'BUY':
            buy_score += self.weights['ema_trend'] * ema_strength
            analysis['signals'].append(f"✅ Tendencia alcista (EMA)")
        elif ema_signal == 'SELL':
            sell_score += self.weights['ema_trend'] * ema_strength
            analysis['signals'].append(f"❌ Tendencia bajista (EMA)")
        
        analysis['indicators']['ema'] = {
            'signal': ema_signal,
            'strength': ema_strength,
            'fast': float(latest['ema_fast']),
            'slow': float(latest['ema_slow'])
        }
        
        
        # ===================================================================
        # ANÁLISIS 2: RSI MOMENTUM (20%)
        # ===================================================================
        rsi_signal, rsi_strength = self._analyze_rsi(latest['rsi'])
        
        if rsi_signal == 'BUY':
            buy_score += self.weights['rsi_momentum'] * rsi_strength
            analysis['signals'].append(f"✅ RSI sobrevendido ({latest['rsi']:.1f})")
        elif rsi_signal == 'SELL':
            sell_score += self.weights['rsi_momentum'] * rsi_strength
            analysis['signals'].append(f"❌ RSI sobrecomprado ({latest['rsi']:.1f})")
        
        analysis['indicators']['rsi'] = {
            'signal': rsi_signal,
            'strength': rsi_strength,
            'value': float(latest['rsi'])
        }
        
        
        # ===================================================================
        # ANÁLISIS 3: BOLLINGER BANDS (15%)
        # ===================================================================
        bb_signal, bb_strength = self._analyze_bollinger(latest)
        
        if bb_signal == 'BUY':
            buy_score += self.weights['bollinger'] * bb_strength
            analysis['signals'].append(f"✅ Precio en banda inferior")
        elif bb_signal == 'SELL':
            sell_score += self.weights['bollinger'] * bb_strength
            analysis['signals'].append(f"❌ Precio en banda superior")
        
        analysis['indicators']['bollinger'] = {
            'signal': bb_signal,
            'strength': bb_strength,
            'width': float(latest['bb_width'])
        }
        
        
        # ===================================================================
        # ANÁLISIS 4: VWAP (15%)
        # ===================================================================
        vwap_signal, vwap_strength = self._analyze_vwap(latest, prev)
        
        if vwap_signal == 'BUY':
            buy_score += self.weights['vwap'] * vwap_strength
            analysis['signals'].append(f"✅ Cruce alcista de VWAP")
        elif vwap_signal == 'SELL':
            sell_score += self.weights['vwap'] * vwap_strength
            analysis['signals'].append(f"❌ Cruce bajista de VWAP")
        
        analysis['indicators']['vwap'] = {
            'signal': vwap_signal,
            'strength': vwap_strength,
            'value': float(latest['vwap'])
        }
        
        
        # ===================================================================
        # ANÁLISIS 5: VOLUMEN (15%)
        # ===================================================================
        volume_signal, volume_strength = self._analyze_volume(
            latest, buy_score, sell_score
        )
        
        if volume_signal == 'BUY':
            buy_score += self.weights['volume'] * volume_strength
            analysis['signals'].append(f"✅ Alto volumen confirma compra")
        elif volume_signal == 'SELL':
            sell_score += self.weights['volume'] * volume_strength
            analysis['signals'].append(f"❌ Alto volumen confirma venta")
        
        analysis['indicators']['volume'] = {
            'signal': volume_signal,
            'strength': volume_strength,
            'ratio': float(latest['volume_ratio'])
        }
        
        
        # ===================================================================
        # ANÁLISIS 6: PRICE ACTION (10%)
        # ===================================================================
        price_action_signal, price_action_strength = self._analyze_price_action(latest)
        
        if price_action_signal == 'BUY':
            buy_score += self.weights['price_action'] * price_action_strength
            analysis['signals'].append(f"✅ Momentum de precio positivo")
        elif price_action_signal == 'SELL':
            sell_score += self.weights['price_action'] * price_action_strength
            analysis['signals'].append(f"❌ Momentum de precio negativo")
        
        analysis['indicators']['price_action'] = {
            'signal': price_action_signal,
            'strength': price_action_strength,
            'change': float(latest['price_change'])
        }
        
        
        # ===================================================================
        # DECISIÓN FINAL
        # ===================================================================
        confidence = max(buy_score, sell_score)
        
        if buy_score > sell_score:
            prediction = 'BUY'
            analysis['prediction'] = 'BUY'
            analysis['confidence'] = buy_score
        elif sell_score > buy_score:
            prediction = 'SELL'
            analysis['prediction'] = 'SELL'
            analysis['confidence'] = sell_score
        else:
            prediction = 'HOLD'
            analysis['prediction'] = 'HOLD'
            analysis['confidence'] = confidence
        
        analysis['buy_score'] = buy_score
        analysis['sell_score'] = sell_score
        
        # Guardar en historial
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'prediction': prediction,
            'confidence': confidence
        })
        
        logger.debug(
            f"IA Prediction: {prediction} {symbol} "
            f"(Confidence: {confidence:.0%}, Buy: {buy_score:.2f}, Sell: {sell_score:.2f})"
        )
        
        return prediction, confidence, analysis
    
    
    # =======================================================================
    # MÉTODOS DE ANÁLISIS INDIVIDUAL
    # =======================================================================
    
    def _analyze_ema_trend(self, latest: pd.Series, prev: pd.Series) -> Tuple[str, float]:
        """
        Analiza tendencia usando EMAs
        
        Returns:
            Tupla (signal, strength)
        """
        ema_fast = latest['ema_fast']
        ema_slow = latest['ema_slow']
        prev_fast = prev['ema_fast']
        prev_slow = prev['ema_slow']
        
        # Calcular separación entre EMAs
        separation = abs(ema_fast - ema_slow) / ema_slow
        
        # Tendencia alcista
        if ema_fast > ema_slow:
            # Golden cross reciente (cruce alcista)
            if prev_fast <= prev_slow:
                return 'BUY', 1.0  # Máxima fuerza
            # Tendencia establecida
            else:
                # Más separación = más fuerza
                strength = min(separation * 50, 1.0)
                return 'BUY', strength
        
        # Tendencia bajista
        elif ema_fast < ema_slow:
            # Death cross reciente (cruce bajista)
            if prev_fast >= prev_slow:
                return 'SELL', 1.0  # Máxima fuerza
            # Tendencia establecida
            else:
                strength = min(separation * 50, 1.0)
                return 'SELL', strength
        
        return 'HOLD', 0.0
    
    
    def _analyze_rsi(self, rsi: float) -> Tuple[str, float]:
        """
        Analiza RSI para detectar sobrecompra/sobreventa
        
        Returns:
            Tupla (signal, strength)
        """
        # Sobrevendido (probable rebote alcista)
        if rsi < 30:
            # Más sobrevendido = más fuerza
            strength = (30 - rsi) / 30
            return 'BUY', min(strength, 1.0)
        
        # Sobrecomprado (probable caída)
        elif rsi > 70:
            # Más sobrecomprado = más fuerza
            strength = (rsi - 70) / 30
            return 'SELL', min(strength, 1.0)
        
        # Zona neutral
        elif rsi < 50:
            # Ligeramente bajista
            strength = (50 - rsi) / 50 * 0.5
            return 'BUY', strength
        else:
            # Ligeramente alcista
            strength = (rsi - 50) / 50 * 0.5
            return 'SELL', strength
    
    
    def _analyze_bollinger(self, latest: pd.Series) -> Tuple[str, float]:
        """
        Analiza Bollinger Bands
        
        Returns:
            Tupla (signal, strength)
        """
        price = latest['close']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_middle = latest['bb_middle']
        bb_width = latest['bb_width']
        
        # Solo considerar si hay volatilidad suficiente
        if bb_width < 0.02:  # 2% mínimo
            return 'HOLD', 0.0
        
        # Precio tocando banda inferior (probable rebote)
        if price <= bb_lower:
            # Calcular qué tan lejos está de la media
            distance = abs(price - bb_middle) / bb_middle
            strength = min(distance * 20, 1.0)
            return 'BUY', strength
        
        # Precio tocando banda superior (probable retroceso)
        elif price >= bb_upper:
            distance = abs(price - bb_middle) / bb_middle
            strength = min(distance * 20, 1.0)
            return 'SELL', strength
        
        return 'HOLD', 0.0
    
    
    def _analyze_vwap(self, latest: pd.Series, prev: pd.Series) -> Tuple[str, float]:
        """
        Analiza VWAP (Volume Weighted Average Price)
        
        Returns:
            Tupla (signal, strength)
        """
        price = latest['close']
        vwap = latest['vwap']
        prev_price = prev['close']
        prev_vwap = prev['vwap']
        
        # Cruce alcista (precio cruza por encima de VWAP)
        if price > vwap and prev_price <= prev_vwap:
            return 'BUY', 1.0
        
        # Cruce bajista (precio cruza por debajo de VWAP)
        elif price < vwap and prev_price >= prev_vwap:
            return 'SELL', 1.0
        
        # Precio muy por encima de VWAP (alcista)
        elif price > vwap * 1.001:
            distance = (price - vwap) / vwap
            strength = min(distance * 100, 0.5)
            return 'BUY', strength
        
        # Precio muy por debajo de VWAP (bajista)
        elif price < vwap * 0.999:
            distance = (vwap - price) / vwap
            strength = min(distance * 100, 0.5)
            return 'SELL', strength
        
        return 'HOLD', 0.0
    
    
    def _analyze_volume(self, latest: pd.Series, buy_score: float, 
                       sell_score: float) -> Tuple[str, float]:
        """
        Analiza volumen para confirmar dirección
        
        Returns:
            Tupla (signal, strength)
        """
        volume_ratio = latest['volume_ratio']
        
        # Volumen alto confirma la dirección actual
        if volume_ratio > 1.5:
            strength = min((volume_ratio - 1) / 2, 1.0)
            
            # Confirma la dirección que ya está ganando
            if buy_score > sell_score:
                return 'BUY', strength
            elif sell_score > buy_score:
                return 'SELL', strength
        
        return 'HOLD', 0.0
    
    
    def _analyze_price_action(self, latest: pd.Series) -> Tuple[str, float]:
        """
        Analiza acción del precio (momentum)
        
        Returns:
            Tupla (signal, strength)
        """
        price_change = latest['price_change']
        
        # Momentum alcista fuerte
        if price_change > 0.002:  # +0.2%
            strength = min(price_change * 500, 1.0)
            return 'BUY', strength
        
        # Momentum bajista fuerte
        elif price_change < -0.002:  # -0.2%
            strength = min(abs(price_change) * 500, 1.0)
            return 'SELL', strength
        
        return 'HOLD', 0.0
    
    
    # =======================================================================
    # MÉTODOS AUXILIARES
    # =======================================================================
    
    def get_prediction_stats(self, minutes: int = 60) -> Optional[Dict]:
        """
        Obtiene estadísticas de predicciones recientes
        
        Args:
            minutes: Últimos X minutos a analizar
            
        Returns:
            Dict con estadísticas o None
        """
        if not self.prediction_history:
            return None
        
        cutoff = datetime.now() - pd.Timedelta(minutes=minutes)
        recent = [p for p in self.prediction_history if p['timestamp'] > cutoff]
        
        if not recent:
            return None
        
        total = len(recent)
        buy_count = sum(1 for p in recent if p['prediction'] == 'BUY')
        sell_count = sum(1 for p in recent if p['prediction'] == 'SELL')
        hold_count = sum(1 for p in recent if p['prediction'] == 'HOLD')
        
        avg_confidence = sum(p['confidence'] for p in recent) / total
        
        return {
            'total_predictions': total,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'hold_signals': hold_count,
            'avg_confidence': avg_confidence,
            'timeframe_minutes': minutes
        }
    
    
    def explain_prediction(self, analysis: Dict) -> str:
        """
        Genera explicación en lenguaje natural de la predicción
        
        Args:
            analysis: Dict de análisis generado por predict()
            
        Returns:
            String con explicación
        """
        explanation = f"Análisis de {analysis['symbol']}:\n\n"
        
        prediction = analysis['prediction']
        confidence = analysis['confidence']
        
        explanation += f"🎯 Predicción: {prediction}\n"
        explanation += f"📊 Confianza: {confidence:.0%}\n\n"
        explanation += "Señales detectadas:\n"
        
        for signal in analysis['signals']:
            explanation += f"  {signal}\n"
        
        return explanation
