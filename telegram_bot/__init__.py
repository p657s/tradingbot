"""
Módulo de Telegram Bot

Este módulo maneja toda la interacción con usuarios vía Telegram:
- TelegramBot: Clase principal del bot
- BotCommands: Comandos disponibles para usuarios

El bot permite:
- Suscribirse/desuscribirse
- Ver estado y estadísticas
- Recibir señales automáticamente

Uso:
    from telegram import TelegramBot
    
    bot = TelegramBot(bot_token, subscriber_manager, signal_generator)
    await bot.start()
"""

from .bot import TelegramBot
from .bot_commands import BotCommands

# Exportar clases públicas
__all__ = [
    'TelegramBot',
    'BotCommands'
]

# Versión del módulo
__version__ = '1.0.0'

# Metadata
__author__ = 'Trading Bot Team'
__description__ = 'Bot de Telegram para distribución de señales'
