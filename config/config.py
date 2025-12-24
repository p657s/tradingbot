"""
Configuración general del sistema de trading
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """
    Configuración principal del bot de trading
    Centraliza todas las credenciales y rutas
    """
    
    # ========================================================================
    # CREDENCIALES - Obtenidas desde archivo .env
    # ========================================================================
    
    # Binance Futures API
    # Crear en: https://www.binance.com/en/my/settings/api-management
    # ⚠️ IMPORTANTE: Solo necesitas permiso de LECTURA (Enable Reading)
    # NO necesitas permisos de trading para este bot de señales
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    # Telegram Bot
    # Crear con @BotFather en Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # ID de Telegram del administrador (opcional)
    # Obtener con @userinfobot en Telegram
    TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
    
    
    # ========================================================================
    # BINANCE - URLs y configuración
    # ========================================================================
    
    # URL base de Binance Futures (USD-M Perpetual)
    BINANCE_FUTURES_BASE = 'https://fapi.binance.com'
    
    # WebSocket de Binance Futures (para streams en tiempo real)
    BINANCE_FUTURES_WS = 'wss://fstream.binance.com/ws'
    
    # Testnet para pruebas (descomenta para usar dinero virtual)
    # BINANCE_FUTURES_BASE = 'https://testnet.binancefuture.com'
    
    
    # ========================================================================
    # DIRECTORIOS - Estructura de archivos del proyecto
    # ========================================================================
    
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).parent.parent
    
    # Directorio para datos (JSON)
    DATA_DIR = BASE_DIR / 'data'
    
    # Directorio para logs
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Crear directorios si no existen
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    
    # ========================================================================
    # ARCHIVOS JSON - Base de datos en archivos
    # ========================================================================
    
    # Archivo de suscriptores
    # Contiene: telegram_id, username, fecha_suscripción, señales recibidas, etc.
    SUBSCRIBERS_FILE = DATA_DIR / 'subscribers.json'
    
    # Archivo de señales activas
    # Contiene: señales que están siendo monitoreadas (esperando stop/target)
    ACTIVE_SIGNALS_FILE = DATA_DIR / 'active_signals.json'
    
    # Archivo de historial de performance
    # Contiene: todas las señales cerradas con sus resultados (P&L)
    PERFORMANCE_FILE = DATA_DIR / 'performance.json'
    
    
    # ========================================================================
    # LOGGING - Configuración de registros
    # ========================================================================
    
    # Archivo de log principal
    LOG_FILE = LOGS_DIR / 'trading_bot.log'
    
    # Nivel de logging
    # Opciones: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    LOG_LEVEL = 'INFO'
    
    # Formato de los mensajes de log
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Formato de fecha en logs
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    
    # ========================================================================
    # VALIDACIÓN - Verifica que todo esté configurado
    # ========================================================================
    
    @classmethod
    def validate(cls):
        """
        Valida que todas las credenciales necesarias estén configuradas
        
        Raises:
            ValueError: Si falta alguna credencial requerida
            
        Returns:
            bool: True si todo está OK
        """
        # Lista de credenciales requeridas
        required_credentials = [
            ('BINANCE_API_KEY', cls.BINANCE_API_KEY),
            ('BINANCE_API_SECRET', cls.BINANCE_API_SECRET),
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
        ]
        
        # Verificar cuáles faltan
        missing = [name for name, value in required_credentials if not value or value == '']
        
        if missing:
            error_msg = (
                f"\n❌ ERROR: Faltan las siguientes credenciales en el archivo .env:\n"
                f"   {', '.join(missing)}\n\n"
                f"📝 Pasos para solucionar:\n"
                f"   1. Copia el archivo .env.example a .env\n"
                f"   2. Edita .env y completa tus credenciales\n"
                f"   3. Guarda el archivo y vuelve a ejecutar\n\n"
                f"💡 Ayuda:\n"
                f"   - Binance API: https://www.binance.com/en/my/settings/api-management\n"
                f"   - Telegram Bot: Habla con @BotFather en Telegram\n"
                f"   - Tu ID Telegram: Habla con @userinfobot en Telegram\n"
            )
            raise ValueError(error_msg)
        
        # Validar que no sean valores de ejemplo
        if 'tu_' in cls.BINANCE_API_KEY.lower():
            raise ValueError(
                "❌ Aún tienes valores de ejemplo en .env\n"
                "Reemplaza 'tu_binance_api_key_aqui' con tu API key real"
            )
        
        if 'tu_' in cls.TELEGRAM_BOT_TOKEN.lower():
            raise ValueError(
                "❌ Aún tienes valores de ejemplo en .env\n"
                "Reemplaza 'tu_telegram_bot_token_aqui' con tu token real"
            )
        
        return True
    
    
    # ========================================================================
    # INFORMACIÓN - Método para debug
    # ========================================================================
    
    @classmethod
    def print_info(cls):
        """Imprime información de configuración (sin mostrar credenciales)"""
        print("\n" + "="*70)
        print("⚙️  CONFIGURACIÓN DEL SISTEMA")
        print("="*70)
        print(f"📁 Directorio base: {cls.BASE_DIR}")
        print(f"📊 Directorio de datos: {cls.DATA_DIR}")
        print(f"📝 Directorio de logs: {cls.LOGS_DIR}")
        print(f"🔗 Binance API: {'✅ Configurada' if cls.BINANCE_API_KEY else '❌ No configurada'}")
        print(f"💬 Telegram Bot: {'✅ Configurado' if cls.TELEGRAM_BOT_TOKEN else '❌ No configurado'}")
        print(f"👤 Admin ID: {'✅ Configurado' if cls.TELEGRAM_ADMIN_ID else '⚠️  Opcional'}")
        print("="*70 + "\n")
