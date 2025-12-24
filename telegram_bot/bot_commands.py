"""
Comandos del bot de Telegram

Define todos los comandos disponibles para los usuarios.
"""

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BotCommands:
    """
    Comandos disponibles para usuarios del bot
    
    Cada método corresponde a un comando:
    - /start → cmd_start
    - /subscribe → cmd_subscribe
    - etc.
    """
    
    def __init__(self, subscriber_manager, signal_generator):
        """
        Inicializa los comandos
        
        Args:
            subscriber_manager: Instancia de SubscriberManager
            signal_generator: Instancia de SignalGenerator
        """
        self.subscribers = subscriber_manager
        self.signals = signal_generator
        logger.info("✅ Bot Commands inicializado")
    
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /start - Mensaje de bienvenida
        
        Muestra:
        - Bienvenida al bot
        - Descripción del servicio
        - Instrucciones para suscribirse
        """
        user = update.effective_user
        
        message = f"""
👋 <b>¡Hola {user.first_name}!</b>

🤖 Bienvenido al <b>Bot de Señales de Trading</b>

📊 Recibe señales de trading profesionales basadas en:
   • Análisis técnico con IA
   • Múltiples indicadores
   • Alta confianza (70%+)

🎯 <b>Características:</b>
   ✓ Señales de BUY/SELL en tiempo real
   ✓ Stop Loss y Take Profit calculados
   ✓ Notificaciones instantáneas
   ✓ 100% GRATIS

📝 <b>Usa /subscribe para comenzar</b>
📚 <b>Usa /help para más información</b>
"""
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
        
        logger.info(f"👤 /start de {user.username or user.id}")
    
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /subscribe - Suscribirse al servicio
        
        Agrega al usuario a la base de datos y habilita notificaciones
        """
        user = update.effective_user
        
        # Agregar suscriptor
        subscriber, is_new = self.subscribers.add_subscriber(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        if is_new:
            message = f"""
✅ <b>¡Suscripción Exitosa!</b>

Hola {user.first_name}, ahora recibirás:

📈 Señales de trading en tiempo real
🎯 Análisis con alta confianza
💰 Stop Loss y Take Profit
⚡ Notificaciones instantáneas

<b>Comandos útiles:</b>
/status - Ver tu estado
/stats - Estadísticas del servicio
/unsubscribe - Cancelar suscripción
/help - Ayuda

🔔 <i>Recibirás la próxima señal automáticamente</i>
"""
            logger.info(f"✅ Nuevo suscriptor: {user.username or user.id}")
        else:
            message = f"""
ℹ️ <b>Ya estás suscrito</b>

{user.first_name}, ya estabas en nuestra lista.

📊 Señales recibidas: {subscriber['total_signals_received']}
📅 Miembro desde: {subscriber['joined_date'][:10]}

🔔 Seguirás recibiendo todas las señales
"""
            logger.info(f"♻️  Usuario ya suscrito: {user.username or user.id}")
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def cmd_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /unsubscribe - Cancelar suscripción
        
        Elimina al usuario de la base de datos
        """
        user = update.effective_user
        
        # Intentar eliminar
        removed = self.subscribers.remove_subscriber(user.id)
        
        if removed:
            message = """
😢 <b>Suscripción Cancelada</b>

Has sido eliminado de nuestra lista.

Ya no recibirás señales de trading.

<i>Puedes volver cuando quieras con /subscribe</i>
"""
            logger.info(f"👋 Usuario desuscrito: {user.username or user.id}")
        else:
            message = """
ℹ️ <b>No estabas suscrito</b>

No encontramos tu suscripción activa.

Usa /subscribe si quieres recibir señales.
"""
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /status - Ver estado de la suscripción
        
        Muestra:
        - Estado de suscripción
        - Señales recibidas
        - Fecha de registro
        """
        user = update.effective_user
        
        subscriber = self.subscribers.get_subscriber(user.id)
        
        if not subscriber:
            message = """
❌ <b>No estás suscrito</b>

Usa /subscribe para comenzar a recibir señales.
"""
        else:
            # Calcular días desde registro
            joined = datetime.fromisoformat(subscriber['joined_date'])
            days = (datetime.now() - joined).days
            
            # Estado de notificaciones
            notif_status = "✅ Activas" if subscriber['preferences']['notifications_enabled'] else "🔕 Desactivadas"
            
            message = f"""
👤 <b>TU ESTADO</b>

<b>Usuario:</b> {subscriber['username']}
<b>Estado:</b> {'✅ Activo' if subscriber['is_active'] else '⏸️  Inactivo'}
<b>Notificaciones:</b> {notif_status}

📊 <b>Estadísticas:</b>
   • Señales hoy: {subscriber['signals_received_today']}
   • Señales totales: {subscriber['total_signals_received']}
   • Miembro desde: {days} días

📅 <b>Registro:</b> {joined.strftime('%d/%m/%Y')}
"""
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /stats - Estadísticas del servicio
        
        Muestra:
        - Suscriptores totales
        - Señales enviadas
        - Performance reciente
        """
        # Estadísticas de suscriptores
        sub_stats = self.subscribers.get_stats()
        
        # Estadísticas de performance (últimos 7 días)
        perf_stats = self.signals.get_performance_stats(days=7)
        
        message = f"""
📊 <b>ESTADÍSTICAS DEL SERVICIO</b>

👥 <b>Suscriptores:</b>
   • Total: {sub_stats['total_subscribers']}
   • Activos: {sub_stats['active_subscribers']}
   • Señales enviadas hoy: {sub_stats['signals_today']}
   • Señales totales: {sub_stats['total_signals_sent']}
"""
        
        # Agregar performance si hay datos
        if perf_stats:
            message += f"""
📈 <b>Performance (últimos 7 días):</b>
   • Señales generadas: {perf_stats['total_signals']}
   • Operaciones ganadoras: {perf_stats['winners']} ✅
   • Operaciones perdedoras: {perf_stats['losers']} ❌
   • Win Rate: {perf_stats['win_rate']:.1%}
   • Ganancia promedio: {perf_stats['avg_win']:+.2f}%
   • Pérdida promedio: {perf_stats['avg_loss']:+.2f}%
"""
            
            if perf_stats['profit_factor'] > 0:
                message += f"   • Profit Factor: {perf_stats['profit_factor']:.2f}\n"
        
        message += """
⚠️ <i>Resultados pasados no garantizan ganancias futuras</i>
"""
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /help - Ayuda y lista de comandos
        
        Muestra todos los comandos disponibles
        """
        message = """
📚 <b>COMANDOS DISPONIBLES</b>

<b>Suscripción:</b>
/start - Iniciar el bot
/subscribe - Suscribirte al servicio
/unsubscribe - Cancelar suscripción

<b>Información:</b>
/status - Ver tu estado
/stats - Estadísticas del servicio
/help - Ver esta ayuda

<b>Sobre las señales:</b>
📊 Recibirás señales automáticamente cuando el sistema detecte oportunidades con alta confianza (70%+)

🎯 Cada señal incluye:
   • Tipo (BUY/SELL)
   • Precio de entrada
   • Stop Loss
   • Take Profit
   • Nivel de confianza

⚠️ <b>IMPORTANTE:</b>
Este bot solo envía SEÑALES, no ejecuta operaciones automáticamente. Tú decides si operar o no.

💡 <b>Recomendaciones:</b>
• Usa solo 2-3% de tu capital por operación
• Siempre coloca stop loss
• No operes con dinero que no puedas perder

❓ ¿Preguntas? Contacta al administrador
"""
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /broadcast - Enviar mensaje masivo (SOLO ADMIN)
        
        Uso: /broadcast Tu mensaje aquí
        """
        from config.config import Config
        
        user = update.effective_user
        
        # Verificar que sea admin
        if str(user.id) != str(Config.TELEGRAM_ADMIN_ID):
            await update.message.reply_text("❌ Comando solo para administradores")
            return
        
        # Obtener mensaje
        if not context.args:
            await update.message.reply_text(
                "Uso: /broadcast Tu mensaje aquí"
            )
            return
        
        broadcast_msg = ' '.join(context.args)
        
        # Confirmar
        await update.message.reply_text(
            f"📢 Enviando broadcast a todos los usuarios...\n\n{broadcast_msg}"
        )
        
        # TODO: Implementar envío masivo
        # Esto requiere acceso al SignalDistributor
        
        logger.info(f"📢 Broadcast solicitado por admin: {broadcast_msg}")
    
    
    async def cmd_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /users - Ver lista de usuarios (SOLO ADMIN)
        """
        from config.config import Config
        
        user = update.effective_user
        
        # Verificar que sea admin
        if str(user.id) != str(Config.TELEGRAM_ADMIN_ID):
            await update.message.reply_text("❌ Comando solo para administradores")
            return
        
        stats = self.subscribers.get_stats()
        recent = self.subscribers.get_recent_subscribers(days=7)
        
        message = f"""
👥 <b>GESTIÓN DE USUARIOS</b>

Total: {stats['total_subscribers']}
Activos: {stats['active_subscribers']}

<b>Nuevos (últimos 7 días):</b> {len(recent)}

<b>Usuario más activo:</b>
"""
        
        if stats['most_active_user']:
            message += f"{stats['most_active_user']['username']} - {stats['most_active_user']['signals']} señales\n"
        
        await update.message.reply_text(
            message.strip(),
            parse_mode='HTML'
        )
    
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para mensajes de texto que no son comandos
        
        Responde con ayuda básica
        """
        message = """
❓ No entiendo ese mensaje.

Usa /help para ver los comandos disponibles.
"""
        
        await update.message.reply_text(message.strip())
