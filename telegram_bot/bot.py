"""
Clase principal del bot de Telegram

Maneja la inicialización, configuración y ejecución del bot.
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.config import Config
from .bot_commands import BotCommands
import logging

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Bot principal de Telegram para interacción con usuarios
    
    Responsabilidades:
    - Inicializar Application de python-telegram-bot
    - Registrar handlers de comandos
    - Gestionar inicio/detención del bot
    - Coordinar con SubscriberManager y SignalGenerator
    """
    
    def __init__(self, bot_token: str, subscriber_manager, signal_generator, binance_client):
        """
        Inicializa el bot de Telegram
        
        Args:
            bot_token: Token del bot de Telegram
            subscriber_manager: Instancia de SubscriberManager
            signal_generator: Instancia de SignalGenerator
            binance_client: Instancia de BinanceClient ← AGREGADO
        """
        self.token = bot_token
        self.subscribers = subscriber_manager
        self.signals = signal_generator
        self.binance_client = binance_client  # ← LÍNEA NUEVA
        self.app = None
        self.commands = None
        
        logger.info("🤖 Inicializando Telegram Bot...")
    
    
    async def start(self):
        """
        Inicia el bot de Telegram
        
        Configura:
        - Application builder
        - Handlers de comandos
        - Polling para recibir mensajes
        """
        try:
            # Crear application
            self.app = Application.builder().token(self.token).build()
            
            # Inicializar comandos
            self.commands = BotCommands(self.subscribers, self.signals)
            
            # Guardar binance_client en bot_data para que los comandos puedan acceder ← LÍNEA NUEVA
            self.app.bot_data['binance_client'] = self.binance_client
            
            # Registrar handlers de comandos
            self._register_handlers()
            
            # Inicializar y empezar polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=['message', 'callback_query'],
                drop_pending_updates=True
            )
            
            # Obtener info del bot
            bot_info = await self.app.bot.get_me()
            logger.info(f"✅ Bot iniciado: @{bot_info.username}")
            logger.info(f"   ID: {bot_info.id}")
            logger.info(f"   Nombre: {bot_info.first_name}")
            
            # Notificar al admin si está configurado
            if Config.TELEGRAM_ADMIN_ID:
                await self._notify_admin_startup(bot_info.username)
            
        except Exception as e:
            logger.error(f"❌ Error iniciando bot: {e}")
            raise
    
    
    async def stop(self):
        """Detiene el bot de forma ordenada"""
        if self.app:
            logger.info("⏹️  Deteniendo bot...")
            
            # Notificar admin
            if Config.TELEGRAM_ADMIN_ID:
                await self._notify_admin_shutdown()
            
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            
            logger.info("✅ Bot detenido correctamente")
    
    
    def _register_handlers(self):
        """
        Registra todos los handlers de comandos
        
        Comandos disponibles:
        - /start: Bienvenida
        - /subscribe: Suscribirse
        - /unsubscribe: Cancelar suscripción
        - /status: Ver tu estado
        - /stats: Estadísticas del servicio
        - /help: Ayuda
        - /precio: Consultar precio ← NUEVO
        - /markets: Ver resumen de mercados ← NUEVO
        """
        # Comandos básicos
        self.app.add_handler(
            CommandHandler("start", self.commands.cmd_start)
        )
        self.app.add_handler(
            CommandHandler("subscribe", self.commands.cmd_subscribe)
        )
        self.app.add_handler(
            CommandHandler("unsubscribe", self.commands.cmd_unsubscribe)
        )
        self.app.add_handler(
            CommandHandler("status", self.commands.cmd_status)
        )
        self.app.add_handler(
            CommandHandler("stats", self.commands.cmd_stats)
        )
        self.app.add_handler(
            CommandHandler("help", self.commands.cmd_help)
        )
        
        # ← COMANDOS NUEVOS DE PRECIOS
        self.app.add_handler(
            CommandHandler("precio", self.commands.cmd_precio)
        )
        self.app.add_handler(
            CommandHandler("price", self.commands.cmd_precio)
        )
        self.app.add_handler(
            CommandHandler("markets", self.commands.cmd_markets)
        )
        self.app.add_handler(
            CommandHandler("mercados", self.commands.cmd_markets)
        )
        
        # Comandos administrativos (si se implementan)
        if Config.TELEGRAM_ADMIN_ID:
            self.app.add_handler(
                CommandHandler("broadcast", self.commands.cmd_broadcast)
            )
            self.app.add_handler(
                CommandHandler("users", self.commands.cmd_users)
            )
        
        # Handler para mensajes no reconocidos
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.commands.handle_text_message
            )
        )
        
        logger.info("✅ Handlers registrados")
    
    
    async def _notify_admin_startup(self, bot_username: str):
        """Notifica al admin que el bot inició"""
        try:
            stats = self.subscribers.get_stats()
            message = f"""
🚀 <b>BOT INICIADO</b>

<b>Bot:</b> @{bot_username}
<b>Suscriptores activos:</b> {stats['active_subscribers']}
<b>Total suscriptores:</b> {stats['total_subscribers']}

✅ Sistema operativo
"""
            await self.app.bot.send_message(
                chat_id=Config.TELEGRAM_ADMIN_ID,
                text=message.strip(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al admin: {e}")
    
    
    async def _notify_admin_shutdown(self):
        """Notifica al admin que el bot se detendrá"""
        try:
            message = "⏹️ <b>Bot detenido</b>\n\nSistema apagado correctamente."
            await self.app.bot.send_message(
                chat_id=Config.TELEGRAM_ADMIN_ID,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al admin: {e}")
    
    
    async def send_message_to_admin(self, message: str):
        """
        Envía mensaje al administrador
        
        Args:
            message: Mensaje a enviar
        """
        if not Config.TELEGRAM_ADMIN_ID:
            return
        
        try:
            await self.app.bot.send_message(
                chat_id=Config.TELEGRAM_ADMIN_ID,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error enviando mensaje a admin: {e}")
    
    
    def get_bot_info(self) -> dict:
        """
        Obtiene información del bot
        
        Returns:
            Dict con info del bot
        """
        return {
            'token': f"{self.token[:10]}...{self.token[-5:]}",
            'is_running': self.app is not None,
            'subscribers': self.subscribers.get_stats()
        }
