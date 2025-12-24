
import asyncio
import sys
from typing import Dict
from utils import setup_logger
from config.config import Config
from config.trading_params import TradingParams
from core.binance_client import BinanceClient
from strategies.scalping_strategy import ScalpingStrategy
from subscribers.subscriber_manager import SubscriberManager
from subscribers.signal_distributor import SignalDistributor
from core.signal_generator import SignalGenerator
from telegram_bot.bot import TelegramBot


# Configurar logger
logger = setup_logger()


class TradingSignalService:
    """
    Sistema principal de señales de trading
    
    Componentes:
    - BinanceClient: Conexión con Binance para datos
    - ScalpingStrategy: Estrategia de análisis
    - SignalGenerator: Genera y monitorea señales
    - SubscriberManager: Gestiona usuarios
    - SignalDistributor: Envía señales por Telegram
    - TelegramBot: Bot de Telegram para comandos
    """
    
    def __init__(self):
        """Inicializa todos los componentes del sistema"""
        logger.info("="*70)
        logger.info("🚀 SISTEMA DE SEÑALES DE TRADING")
        logger.info("="*70)
        
        # 1. Validar configuración
        try:
            Config.validate()
            logger.info("✅ Configuración validada")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        
        # 2. Cargar parámetros
        self.params = TradingParams()
        try:
            self.params.validate()
            logger.info("✅ Parámetros de trading validados")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        
        # 3. Inicializar componentes EN ORDEN CORRECTO
        logger.info("\n📦 Inicializando componentes...")
        
        # PRIMERO: Binance Client
        logger.info("  🔗 Binance Client...")
        self.binance = BinanceClient()
        
        # Estrategia de scalping
        logger.info("  🎯 Scalping Strategy...")
        self.strategy = ScalpingStrategy()
        
        # Gestor de suscriptores
        logger.info("  👥 Subscriber Manager...")
        self.subscribers = SubscriberManager()
        
        # Distribuidor de señales
        logger.info("  📡 Signal Distributor...")
        self.distributor = SignalDistributor(
            Config.TELEGRAM_BOT_TOKEN,
            self.subscribers
        )
        
        # Generador de señales
        logger.info("  ⚡ Signal Generator...")
        self.signal_gen = SignalGenerator(self.binance, self.strategy)
        
        # ÚLTIMO: Bot de Telegram (necesita binance)
        logger.info("  🤖 Bot de Telegram...")
        self.telegram = TelegramBot(
            Config.TELEGRAM_BOT_TOKEN,
            self.subscribers,
            self.signal_gen,
            self.binance  # ← Ahora sí existe
        )
        
        logger.info("✅ Todos los componentes inicializados")
        logger.info("="*70)
    
    
    async def run(self):
        """
        Loop principal del sistema
        
        Workflow:
        1. Iniciar bot de Telegram
        2. Notificar admin
        3. Loop infinito:
           a. Analizar cada símbolo
           b. Generar señales si hay oportunidad
           c. Distribuir señales a usuarios
           d. Monitorear señales activas
           e. Esperar intervalo
        """
        try:
            # 1. Iniciar bot de Telegram
            logger.info("🤖 Iniciando bot de Telegram...")
            await self.telegram.start()
            
            # 2. Notificar admin que el sistema inició
            if Config.TELEGRAM_ADMIN_ID:
                await self._notify_admin_startup()
            
            # 3. Mostrar info inicial
            self._print_startup_info()
            
            # 4. Loop principal
            logger.info("\n🔄 Iniciando análisis de mercados...")
            logger.info("="*70)
            
            iteration = 0
            
            while True:
                try:
                    iteration += 1
                    logger.debug(f"\n--- Iteración #{iteration} ---")
                    
                    # Analizar cada símbolo configurado
                    for symbol in self.params.SYMBOLS:
                        signal = await self.signal_gen.analyze_symbol(symbol)
                        
                        # Si hay señal, distribuir a usuarios
                        if signal:
                            logger.info(f"📤 Distribuyendo señal de {symbol}...")
                            sent = await self.distributor.distribute_signal(signal)
                            logger.info(f"✅ Señal enviada a {sent} usuarios")
                    
                    # Monitorear señales activas
                    closed_signals = await self.signal_gen.monitor_active_signals()
                    
                    # Si hay señales cerradas, notificar resultados
                    for signal in closed_signals:
                        await self._notify_signal_closed(signal)
                    
                    # Esperar antes de la siguiente iteración
                    logger.debug(
                        f"⏳ Esperando {self.params.ANALYSIS_INTERVAL}s "
                        f"hasta próximo análisis..."
                    )
                    await asyncio.sleep(self.params.ANALYSIS_INTERVAL)
                    
                except KeyboardInterrupt:
                    raise  # Propagar para cerrar limpiamente
                    
                except Exception as e:
                    logger.error(f"❌ Error en loop principal: {e}", exc_info=True)
                    logger.warning("⚠️  Esperando 30s antes de reintentar...")
                    await asyncio.sleep(30)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Señal de interrupción recibida...")
            await self._shutdown()
        
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}", exc_info=True)
            await self._shutdown()
            sys.exit(1)
    
    
    async def _notify_admin_startup(self):
        """Notifica al admin que el sistema inició"""
        stats = self.subscribers.get_stats()
        
        message = f"""
🚀 <b>SISTEMA INICIADO</b>

✅ Todos los componentes operativos

<b>Suscriptores:</b> {stats['active_subscribers']} activos

<b>Símbolos monitoreados:</b>
{', '.join(self.params.SYMBOLS)}

<b>Configuración:</b>
• Timeframe: {self.params.TIMEFRAME}
• Confianza mínima: {self.params.MIN_CONFIDENCE:.0%}
• Análisis cada: {self.params.ANALYSIS_INTERVAL}s

🔔 Listo para generar señales
"""
        
        try:
            await self.distributor.bot.send_message(
                chat_id=Config.TELEGRAM_ADMIN_ID,
                text=message.strip(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al admin: {e}")
    
    
    async def _notify_signal_closed(self, signal: Dict):
        """Notifica a usuarios cuando una señal se cierra"""
        await self.distributor.send_signal_update(
            signal['signal_id'],
            signal['status'],
            signal['pnl_percent']
        )
    
    
    def _print_startup_info(self):
        """Imprime información inicial del sistema"""
        stats = self.subscribers.get_stats()
        perf = self.signal_gen.get_performance_stats(7)
        
        print("\n" + "="*70)
        print("📊 ESTADO DEL SISTEMA")
        print("="*70)
        print(f"Suscriptores activos: {stats['active_subscribers']}")
        print(f"Símbolos: {', '.join(self.params.SYMBOLS)}")
        print(f"Timeframe: {self.params.TIMEFRAME}")
        print(f"Intervalo de análisis: {self.params.ANALYSIS_INTERVAL}s")
        
        if perf:
            print(f"\nPerformance (últimos 7 días):")
            print(f"  Win Rate: {perf['win_rate']:.1%}")
            print(f"  Total señales: {perf['total_signals']}")
            print(f"  P&L total: {perf['total_pnl']:+.2f}%")
        
        print("="*70)
    
    
    async def _shutdown(self):
        """Cierra el sistema de forma ordenada"""
        logger.info("\n🛑 Cerrando sistema...")
        
        # Notificar admin
        if Config.TELEGRAM_ADMIN_ID:
            try:
                await self.distributor.bot.send_message(
                    chat_id=Config.TELEGRAM_ADMIN_ID,
                    text="⏹️ <b>Sistema detenido</b>",
                    parse_mode='HTML'
                )
            except:
                pass
        
        # Detener bot
        await self.telegram.stop()
        
        logger.info("✅ Sistema cerrado correctamente")


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    """
    Ejecuta el sistema
    
    Uso:
        python main.py
    """
    service = TradingSignalService()
    
    try:
        # Ejecutar con asyncio
        asyncio.run(service.run())
        
    except KeyboardInterrupt:
        logger.info("\n👋 Sistema detenido por el usuario")
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
