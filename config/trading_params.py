"""
Parámetros de trading y estrategia

⚠️ IMPORTANTE: Este bot NO ejecuta operaciones automáticamente
Solo ANALIZA el mercado y ENVÍA SEÑALES a los usuarios por Telegram

Los usuarios reciben:
- Señales de BUY/SELL
- Precio de entrada sugerido
- Stop Loss recomendado
- Take Profit recomendado
- Confianza del análisis

Cada usuario decide si operar o no en su propia cuenta
"""


class TradingParams:
    """
    Parámetros configurables del sistema de SEÑALES
    
    Este bot es un SERVICIO DE ALERTAS, no ejecuta trades
    """
    
    # ========================================================================
    # SÍMBOLOS - Pares de criptomonedas a ANALIZAR
    # ========================================================================
    
    SYMBOLS = [
        'BTCUSDT',   # Bitcoin
        'ETHUSDT',   # Ethereum
        'SOLUSDT',   # Solana
        'BNBUSDT',   # Binance Coin
        # Puedes agregar más:
        # 'ADAUSDT',   # Cardano
        # 'XRPUSDT',   # Ripple
        # 'DOGEUSDT',  # Dogecoin
        # 'AVAXUSDT',  # Avalanche
        # 'MATICUSDT', # Polygon
        # 'LINKUSDT',  # Chainlink
    ]
    
    
    # ========================================================================
    # TIMEFRAMES - Intervalos de tiempo para ANÁLISIS
    # ========================================================================
    
    # Timeframe principal para análisis de scalping
    # Opciones: '1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d'
    TIMEFRAME = '1m'  # 1 minuto (scalping rápido)
    
    # Intervalo de análisis en segundos
    # Cada cuántos segundos el bot ANALIZA el mercado y envía señales
    ANALYSIS_INTERVAL = 10  # Analiza cada 10 segundos
    
    
    # ========================================================================
    # APALANCAMIENTO - SUGERENCIA para los usuarios
    # ========================================================================
    
    # Apalancamiento RECOMENDADO en las señales que envías
    # Este valor solo se MUESTRA al usuario como sugerencia
    # ⚠️ NO ejecuta nada, solo informa
    LEVERAGE = 3  # Sugiere 3x leverage (moderado)
    
    
    # ========================================================================
    # INDICADORES TÉCNICOS - Para ANÁLISIS (no ejecución)
    # ========================================================================
    
    # EMAs para detectar tendencia
    EMA_FAST = 9    # EMA rápida (corto plazo)
    EMA_SLOW = 21   # EMA lenta (largo plazo)
    
    # RSI para momentum
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70  # Sobrecomprado
    RSI_OVERSOLD = 30    # Sobrevendido
    
    # Bollinger Bands para volatilidad
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2
    
    # ATR para calcular stops RECOMENDADOS
    ATR_PERIOD = 14
    
    
    # ========================================================================
    # STOPS RECOMENDADOS - Se calculan y ENVÍAN al usuario
    # ========================================================================
    
    # Multiplicadores de ATR para stops dinámicos SUGERIDOS
    # Estos valores se usan para CALCULAR los stops que aparecen en la señal
    STOP_LOSS_MULTIPLIER = 2.0   # Stop Loss sugerido = Entrada ± (2 × ATR)
    TAKE_PROFIT_MULTIPLIER = 3.0 # Take Profit sugerido = Entrada ± (3 × ATR)
    
    # Ejemplo de señal que recibe el usuario:
    # 🟢 SEÑAL BUY BTCUSDT
    # Entrada: $95,500
    # Stop Loss: $95,200 ← Calculado con estos multiplicadores
    # Take Profit: $96,000 ← Calculado con estos multiplicadores
    # El USUARIO decide si copiar estos valores o no
    
    
    # ========================================================================
    # FILTROS DE SEÑALES - Control de calidad de ALERTAS
    # ========================================================================
    
    # Confianza mínima para ENVIAR una señal
    MIN_CONFIDENCE = 0.50  # Solo envía señales con 70%+ confianza
    
    # Volumen mínimo requerido para validar señal
    MIN_VOLUME_RATIO = 1.5  # Volumen debe ser 1.5x el promedio
    
    # Volatilidad mínima para considerar el mercado
    MIN_VOLATILITY = 0.02  # 2% de volatilidad mínima
    
    # Cooldown entre señales del mismo símbolo
    # Evita SPAM de señales repetidas
    SIGNAL_COOLDOWN_MINUTES = 5  # 5 minutos entre alertas del mismo par
    
    
    # ========================================================================
    # PESOS DE INDICADORES - Sistema de scoring para SEÑALES
    # ========================================================================
    
    # Estos pesos determinan qué tan importante es cada indicador
    # para GENERAR LA SEÑAL (no para ejecutar)
    # DEBEN SUMAR 1.0 (100%)
    WEIGHTS = {
        'ema_trend': 0.25,      # 25% - Tendencia de EMAs
        'rsi_momentum': 0.20,   # 20% - Momentum del RSI
        'bollinger': 0.15,      # 15% - Bandas de Bollinger
        'vwap': 0.15,           # 15% - VWAP
        'volume': 0.15,         # 15% - Confirmación de volumen
        'price_action': 0.10    # 10% - Acción del precio
    }
    
    
    # ========================================================================
    # RECOMENDACIONES - Se MUESTRAN al usuario (no se ejecutan)
    # ========================================================================
    
    # Estas son sugerencias que aparecen en las señales
    # para educar a los usuarios sobre gestión de riesgo
    
    RECOMMENDED_RISK_PER_TRADE = 0.02  # "Usa 2% de tu capital por operación"
    RECOMMENDED_MAX_DAILY_LOSS = 0.05  # "Detente si pierdes 5% en el día"
    RECOMMENDED_MAX_OPEN_TRADES = 3    # "No tengas más de 3 posiciones abiertas"
    
    # Estos valores solo se INFORMAN, cada usuario decide qué hacer
    
    
    # ========================================================================
    # LÍMITES DEL SISTEMA DE SEÑALES
    # ========================================================================
    
    # Máximo de señales activas que el BOT monitorea simultáneamente
    # (Para saber cuándo cerrar señales y enviar actualización)
    MAX_ACTIVE_SIGNALS = 10
    
    # Máximo de señales por símbolo
    MAX_SIGNALS_PER_SYMBOL = 2
    
    # Tiempo máximo que una señal se monitorea (horas)
    # Después de este tiempo, se cierra automáticamente en el sistema
    MAX_SIGNAL_LIFETIME_HOURS = 24
    
    
    # ========================================================================
    # VALIDACIÓN DE PARÁMETROS
    # ========================================================================
    
    @classmethod
    def validate(cls):
        """
        Valida que los parámetros sean coherentes
        
        Returns:
            bool: True si todo está OK
            
        Raises:
            ValueError: Si hay parámetros incorrectos
        """
        # Validar que los pesos sumen 1.0
        total_weight = sum(cls.WEIGHTS.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(
                f"❌ ERROR: Los pesos deben sumar 1.0, actualmente suman {total_weight}\n"
                f"Revisa WEIGHTS en trading_params.py"
            )
        
        # Validar confianza mínima
        if not 0.0 <= cls.MIN_CONFIDENCE <= 1.0:
            raise ValueError(
                f"❌ MIN_CONFIDENCE debe estar entre 0.0 y 1.0, valor actual: {cls.MIN_CONFIDENCE}"
            )
        
        # Validar timeframe
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        if cls.TIMEFRAME not in valid_timeframes:
            raise ValueError(
                f"❌ TIMEFRAME inválido: {cls.TIMEFRAME}\n"
                f"Valores válidos: {', '.join(valid_timeframes)}"
            )
        
        # Validar símbolos
        if not cls.SYMBOLS:
            raise ValueError("❌ Debes configurar al menos 1 símbolo en SYMBOLS")
        
        return True
    
    
    @classmethod
    def print_info(cls):
        """Imprime resumen de la configuración"""
        print("\n" + "="*70)
        print("⚙️  PARÁMETROS DEL SERVICIO DE SEÑALES")
        print("="*70)
        print(f"📊 Símbolos analizados: {', '.join(cls.SYMBOLS)}")
        print(f"⏱️  Timeframe: {cls.TIMEFRAME}")
        print(f"🔄 Análisis cada: {cls.ANALYSIS_INTERVAL}s")
        print(f"⚡ Leverage sugerido: {cls.LEVERAGE}x")
        print(f"📈 Confianza mínima: {cls.MIN_CONFIDENCE:.0%}")
        print(f"🎯 Risk/Reward sugerido: 1:{cls.TAKE_PROFIT_MULTIPLIER/cls.STOP_LOSS_MULTIPLIER:.1f}")
        print(f"\n⚠️  Este bot NO ejecuta trades, solo envía señales")
        print("="*70 + "\n")
