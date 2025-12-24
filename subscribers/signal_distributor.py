"""
Distribuidor de señales de trading por Telegram

Envía señales a todos los usuarios suscritos de forma automática.
Formatea los mensajes de manera profesional y maneja errores.
"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class SignalDistributor:
    """
    Distribuye señales de trading a todos los suscriptores
    
    Funciones:
    - Envía señales a todos los usuarios activos
    - Formatea mensajes profesionales
    - Maneja errores de envío (usuarios bloqueados, etc.)
    - Registra estadísticas de envío
    """
    
    def __init__(self, bot_token: str, subscriber_manager):
        """
        Inicializa el distribuidor de señales
        
        Args:
            bot_token: Token del bot de Telegram
            subscriber_manager: Instancia de SubscriberManager
        """
        self.bot = Bot(token=bot_token)
        self.subscribers = subscriber_manager
        
        logger.info("✅ Signal Distributor inicializado")
    
    
    async def distribute_signal(self, signal: Dict) -> int:
        """
        Distribuye una señal a todos los suscriptores activos
        
        Args:
            signal: Dict con datos de la señal
                {
                    'symbol': 'BTCUSDT',
                    'type': 'BUY' o 'SELL',
                    'price': 95500.00,
                    'confidence': 0.85,
                    'stop_loss': 95200.00,
                    'take_profit': 96000.00,
                    'atr': 150.00
                }
        
        Returns:
            Número de usuarios que recibieron la señal exitosamente
        """
        # Obtener todos los suscriptores activos
        subs = self.subscribers.get_all_active()
        
        if not subs:
            logger.warning("⚠️  No hay suscriptores activos")
            return 0
        
        # Formatear mensaje
        message = self._format_signal_message(signal)
        
        # Crear tareas de envío para todos los usuarios
        tasks = [
            self._send_to_user(sub['telegram_id'], message) 
            for sub in subs
        ]
        
        # Enviar en paralelo
        logger.info(f"📡 Enviando señal a {len(subs)} usuarios...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Contar exitosos
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        logger.info(
            f"✅ Señal distribuida: {successful}/{len(subs)} exitosos, "
            f"{failed} fallidos"
        )
        
        return successful
    
    
    async def _send_to_user(self, telegram_id: str, message: str) -> bool:
        """
        Envía mensaje a un usuario específico
        
        Args:
            telegram_id: ID de Telegram del usuario
            message: Mensaje a enviar
            
        Returns:
            True si se envió exitosamente, False si falló
        """
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='HTML'
            )
            
            # Registrar envío exitoso
            self.subscribers.record_signal_sent(telegram_id)
            
            return True
            
        except TelegramError as e:
            # Errores comunes de Telegram
            if "blocked" in str(e).lower():
                logger.warning(f"⚠️  Usuario {telegram_id} bloqueó el bot")
                
            elif "not found" in str(e).lower():
                logger.warning(f"⚠️  Usuario {telegram_id} no encontrado")
                
            else:
                logger.error(f"❌ Error enviando a {telegram_id}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando a {telegram_id}: {e}")
            return False
    
    
    def _format_signal_message(self, signal: Dict) -> str:
        """
        Formatea mensaje de señal profesional para Telegram
        
        Args:
            signal: Dict con datos de la señal
            
        Returns:
            String formateado en HTML para Telegram
        """
        # Determinar emoji y dirección
        if signal['type'] == 'BUY':
            emoji = "🟢"
            direction = "LONG"
        else:
            emoji = "🔴"
            direction = "SHORT"
        
        # Calcular distancias
        entry = signal['price']
        stop = signal['stop_loss']
        target = signal['take_profit']
        
        risk = abs(entry - stop)
        reward = abs(target - entry)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Formatear mensaje
        message = f"""
{emoji} <b>SEÑAL DE TRADING</b> {emoji}

📊 <b>Par:</b> {signal['symbol']}
🎯 <b>Tipo:</b> {signal['type']} ({direction})
💰 <b>Entrada:</b> ${signal['price']:,.2f}
📈 <b>Confianza:</b> {signal['confidence']:.0%}

<b>🛡️ Stop Loss:</b> ${signal['stop_loss']:,.2f}
<b>🎯 Take Profit:</b> ${signal['take_profit']:,.2f}
<b>📊 Risk/Reward:</b> 1:{risk_reward:.2f}

💡 <i>Usa 2-3% de tu capital por operación</i>
⚡ <i>Apalancamiento sugerido: 3x</i>

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        
        return message.strip()
    
    
    async def broadcast(self, message: str, parse_mode: str = 'HTML') -> int:
        """
        Envía mensaje masivo a todos los suscriptores
        """
        subs = self.subscribers.get_all_active()
        
        if not subs:
            logger.warning("⚠️  No hay suscriptores activos")
            return 0
        
        logger.info(f"📢 Enviando broadcast a {len(subs)} usuarios...")
        
        tasks = []
        for sub in subs:
            tasks.append(
                self._send_broadcast_to_user(
                    sub['telegram_id'], 
                    message, 
                    parse_mode
                )
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        
        logger.info(f"✅ Broadcast enviado a {successful}/{len(subs)} usuarios")
        
        return successful
    
    
    async def _send_broadcast_to_user(self, telegram_id: str, 
                                      message: str, parse_mode: str) -> bool:
        """Envía broadcast a un usuario"""
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
            
        except Exception as e:
            logger.error(f"Error enviando broadcast a {telegram_id}: {e}")
            return False
    
    
    async def send_signal_update(self, signal_id: str, status: str, 
                                  pnl_percent: float) -> int:
        """
        Envía actualización de una señal (cuando se cierra)
        """
        subs = self.subscribers.get_all_active()
        
        if not subs:
            return 0
        
        message = self._format_update_message(signal_id, status, pnl_percent)
        
        tasks = [
            self._send_to_user(sub['telegram_id'], message) 
            for sub in subs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        
        logger.info(
            f"📤 Actualización de señal enviada a {successful}/{len(subs)} usuarios"
        )
        
        return successful
    
    
    def _format_update_message(self, signal_id: str, status: str, 
                               pnl_percent: float) -> str:
        """Formatea mensaje de actualización de señal"""
        
        if status == 'TAKE_PROFIT':
            emoji = "✅"
            title = "OBJETIVO ALCANZADO"
            color = "🟢"
        else:
            emoji = "❌"
            title = "STOP LOSS ACTIVADO"
            color = "🔴"
        
        pnl_text = f"{pnl_percent:+.2f}%"
        
        message = f"""
{emoji} <b>{title}</b> {emoji}

{color} <b>Resultado:</b> {pnl_text}

<i>Señal ID: {signal_id}</i>

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        
        return message.strip()
    
    
    async def send_market_alert(self, alert_type: str, symbol: str, 
                                 details: str) -> int:
        """
        Envía alerta de mercado importante
        """
        subs = self.subscribers.get_all_active()
        
        if not subs:
            return 0
        
        emoji_map = {
            'VOLATILITY': '⚠️',
            'VOLUME': '🔊',
            'PRICE_MOVEMENT': '📈'
        }
        
        emoji = emoji_map.get(alert_type, '⚡')
        
        message = f"""
{emoji} <b>ALERTA DE MERCADO</b> {emoji}

<b>Tipo:</b> {alert_type}
<b>Símbolo:</b> {symbol}

{details}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        
        return await self.broadcast(message)
    
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión del bot
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot conectado: @{bot_info.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando bot: {e}")
            return False
    
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del distribuidor
        """
        subscriber_stats = self.subscribers.get_stats()
        
        return {
            'total_subscribers': subscriber_stats['total_subscribers'],
            'active_subscribers': subscriber_stats['active_subscribers'],
            'bot_username': None
        }
