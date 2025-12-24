"""
Gestor de suscriptores del bot de trading

Maneja la base de datos de usuarios suscritos en formato JSON.
Registra actividad, señales recibidas y preferencias.
"""

from datetime import datetime
from config.config import Config
from utils.json_manager import JSONManager
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class SubscriberManager:
    """
    Gestiona la base de datos de suscriptores
    
    Funciones:
    - Agregar/eliminar suscriptores
    - Consultar estado de suscripción
    - Registrar actividad
    - Estadísticas del servicio
    
    Los datos se guardan en: data/subscribers.json
    """
    
    def __init__(self):
        """Inicializa el gestor de suscriptores"""
        # Cargar base de datos de suscriptores
        self.subscribers = JSONManager.load(Config.SUBSCRIBERS_FILE, {})
        
        total = len(self.subscribers)
        active = len(self.get_all_active())
        
        logger.info(f"✅ SubscriberManager inicializado")
        logger.info(f"   Total suscriptores: {total}")
        logger.info(f"   Activos: {active}")
    
    
    def add_subscriber(self, telegram_id: int, username: Optional[str] = None, 
                      first_name: Optional[str] = None) -> tuple[Dict, bool]:
        """
        Añade un nuevo suscriptor o actualiza uno existente
        
        Args:
            telegram_id: ID de Telegram del usuario
            username: Username de Telegram (opcional)
            first_name: Nombre del usuario (opcional)
            
        Returns:
            Tupla (subscriber_data, is_new)
            - subscriber_data: Dict con datos del suscriptor
            - is_new: True si es nuevo, False si ya existía
            
        Ejemplo:
            >>> manager = SubscriberManager()
            >>> subscriber, is_new = manager.add_subscriber(
            >>>     telegram_id=123456789,
            >>>     username="@juan",
            >>>     first_name="Juan"
            >>> )
            >>> if is_new:
            >>>     print("¡Nuevo suscriptor!")
        """
        telegram_id = str(telegram_id)  # Convertir a string para JSON
        
        # Si ya existe, actualizar última actividad
        if telegram_id in self.subscribers:
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self.subscribers[telegram_id]['username'] = username or self.subscribers[telegram_id]['username']
            self.subscribers[telegram_id]['first_name'] = first_name or self.subscribers[telegram_id]['first_name']
            self._save()
            
            logger.info(f"♻️  Suscriptor actualizado: {username or telegram_id}")
            return self.subscribers[telegram_id], False
        
        # Crear nuevo suscriptor
        subscriber = {
            'telegram_id': telegram_id,
            'username': username or 'Usuario',
            'first_name': first_name or 'Usuario',
            'joined_date': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'is_active': True,
            'signals_received_today': 0,
            'total_signals_received': 0,
            'preferences': {
                'notifications_enabled': True,
                'language': 'es',
                'timezone': 'UTC-5'
            }
        }
        
        self.subscribers[telegram_id] = subscriber
        self._save()
        
        logger.info(f"✅ Nuevo suscriptor: {username or telegram_id} (ID: {telegram_id})")
        return subscriber, True
    
    
    def remove_subscriber(self, telegram_id: int) -> bool:
        """
        Elimina un suscriptor de la base de datos
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            True si se eliminó, False si no existía
            
        Ejemplo:
            >>> manager.remove_subscriber(123456789)
            True
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            username = self.subscribers[telegram_id]['username']
            del self.subscribers[telegram_id]
            self._save()
            
            logger.info(f"🗑️  Suscriptor eliminado: {username} (ID: {telegram_id})")
            return True
        
        logger.warning(f"⚠️  Usuario {telegram_id} no encontrado para eliminar")
        return False
    
    
    def is_subscribed(self, telegram_id: int) -> bool:
        """
        Verifica si un usuario está suscrito
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            True si está suscrito
        """
        return str(telegram_id) in self.subscribers
    
    
    def get_subscriber(self, telegram_id: int) -> Optional[Dict]:
        """
        Obtiene datos de un suscriptor específico
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            Dict con datos del suscriptor o None si no existe
        """
        return self.subscribers.get(str(telegram_id))
    
    
    def get_all_active(self) -> List[Dict]:
        """
        Obtiene todos los suscriptores activos con notificaciones habilitadas
        
        Returns:
            Lista de suscriptores activos
            
        Ejemplo:
            >>> active = manager.get_all_active()
            >>> print(f"{len(active)} usuarios activos")
        """
        active = [
            subscriber for subscriber in self.subscribers.values()
            if subscriber['is_active'] 
            and subscriber['preferences']['notifications_enabled']
        ]
        
        return active
    
    
    def get_all_subscribers(self) -> List[Dict]:
        """
        Obtiene TODOS los suscriptores (activos e inactivos)
        
        Returns:
            Lista de todos los suscriptores
        """
        return list(self.subscribers.values())
    
    
    def deactivate_subscriber(self, telegram_id: int) -> bool:
        """
        Desactiva un suscriptor (no lo elimina, solo lo marca como inactivo)
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            True si se desactivó
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            self.subscribers[telegram_id]['is_active'] = False
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self._save()
            
            logger.info(f"⏸️  Suscriptor desactivado: {telegram_id}")
            return True
        
        return False
    
    
    def activate_subscriber(self, telegram_id: int) -> bool:
        """
        Reactiva un suscriptor desactivado
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            True si se reactivó
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            self.subscribers[telegram_id]['is_active'] = True
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self._save()
            
            logger.info(f"▶️  Suscriptor reactivado: {telegram_id}")
            return True
        
        return False
    
    
    def record_signal_sent(self, telegram_id: int):
        """
        Registra que se envió una señal a un usuario
        
        Actualiza contadores:
        - signals_received_today
        - total_signals_received
        - last_activity
        
        Args:
            telegram_id: ID de Telegram del usuario
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            self.subscribers[telegram_id]['signals_received_today'] += 1
            self.subscribers[telegram_id]['total_signals_received'] += 1
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self._save()
    
    
    def reset_daily_counters(self):
        """
        Resetea contadores diarios (llamar cada 24 horas)
        
        Resetea signals_received_today a 0 para todos los usuarios
        """
        count = 0
        for telegram_id in self.subscribers:
            self.subscribers[telegram_id]['signals_received_today'] = 0
            count += 1
        
        self._save()
        logger.info(f"🔄 Contadores diarios reseteados para {count} usuarios")
    
    
    def update_preferences(self, telegram_id: int, preferences: Dict) -> bool:
        """
        Actualiza preferencias de un suscriptor
        
        Args:
            telegram_id: ID de Telegram del usuario
            preferences: Dict con preferencias a actualizar
                {
                    'notifications_enabled': True/False,
                    'language': 'es'/'en',
                    'timezone': 'UTC-5'
                }
        
        Returns:
            True si se actualizó
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            self.subscribers[telegram_id]['preferences'].update(preferences)
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self._save()
            
            logger.info(f"⚙️  Preferencias actualizadas: {telegram_id}")
            return True
        
        return False
    
    
    def toggle_notifications(self, telegram_id: int) -> Optional[bool]:
        """
        Activa/desactiva notificaciones de un usuario
        
        Args:
            telegram_id: ID de Telegram del usuario
            
        Returns:
            Nuevo estado de notificaciones (True/False) o None si no existe
        """
        telegram_id = str(telegram_id)
        
        if telegram_id in self.subscribers:
            current = self.subscribers[telegram_id]['preferences']['notifications_enabled']
            new_state = not current
            
            self.subscribers[telegram_id]['preferences']['notifications_enabled'] = new_state
            self.subscribers[telegram_id]['last_activity'] = datetime.now().isoformat()
            self._save()
            
            status = "activadas" if new_state else "desactivadas"
            logger.info(f"🔔 Notificaciones {status}: {telegram_id}")
            
            return new_state
        
        return None
    
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del servicio de suscripciones
        
        Returns:
            Dict con estadísticas completas
            
        Ejemplo:
            >>> stats = manager.get_stats()
            >>> print(f"Total: {stats['total_subscribers']}")
            >>> print(f"Activos: {stats['active_subscribers']}")
        """
        all_subs = self.get_all_subscribers()
        active_subs = self.get_all_active()
        
        # Calcular señales totales enviadas
        total_signals = sum(
            sub['total_signals_received'] 
            for sub in all_subs
        )
        
        # Calcular señales de hoy
        today_signals = sum(
            sub['signals_received_today'] 
            for sub in all_subs
        )
        
        # Encontrar usuario más activo
        if all_subs:
            most_active = max(
                all_subs, 
                key=lambda x: x['total_signals_received']
            )
            most_active_info = {
                'username': most_active['username'],
                'signals': most_active['total_signals_received']
            }
        else:
            most_active_info = None
        
        return {
            'total_subscribers': len(all_subs),
            'active_subscribers': len(active_subs),
            'inactive_subscribers': len(all_subs) - len(active_subs),
            'total_signals_sent': total_signals,
            'signals_today': today_signals,
            'most_active_user': most_active_info
        }
    
    
    def get_recent_subscribers(self, days: int = 7) -> List[Dict]:
        """
        Obtiene suscriptores que se unieron recientemente
        
        Args:
            days: Número de días hacia atrás
            
        Returns:
            Lista de suscriptores recientes
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        recent = [
            sub for sub in self.subscribers.values()
            if datetime.fromisoformat(sub['joined_date']) > cutoff
        ]
        
        # Ordenar por fecha de unión (más recientes primero)
        recent.sort(
            key=lambda x: x['joined_date'], 
            reverse=True
        )
        
        return recent
    
    
    def get_inactive_subscribers(self, days: int = 30) -> List[Dict]:
        """
        Obtiene usuarios que no han tenido actividad reciente
        
        Args:
            days: Días de inactividad
            
        Returns:
            Lista de usuarios inactivos
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        inactive = [
            sub for sub in self.subscribers.values()
            if datetime.fromisoformat(sub['last_activity']) < cutoff
        ]
        
        return inactive
    
    
    def export_to_csv(self, filepath: str):
        """
        Exporta base de datos a CSV
        
        Args:
            filepath: Ruta del archivo CSV
        """
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not self.subscribers:
                logger.warning("No hay suscriptores para exportar")
                return
            
            # Obtener keys del primer suscriptor
            first_sub = list(self.subscribers.values())[0]
            fieldnames = [
                'telegram_id', 'username', 'first_name', 
                'joined_date', 'last_activity', 'is_active',
                'signals_received_today', 'total_signals_received',
                'notifications_enabled'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for sub in self.subscribers.values():
                row = {
                    'telegram_id': sub['telegram_id'],
                    'username': sub['username'],
                    'first_name': sub['first_name'],
                    'joined_date': sub['joined_date'],
                    'last_activity': sub['last_activity'],
                    'is_active': sub['is_active'],
                    'signals_received_today': sub['signals_received_today'],
                    'total_signals_received': sub['total_signals_received'],
                    'notifications_enabled': sub['preferences']['notifications_enabled']
                }
                writer.writerow(row)
        
        logger.info(f"📄 Base de datos exportada a: {filepath}")
    
    
    def _save(self):
        """
        Guarda cambios en el archivo JSON
        
        Uso interno, se llama automáticamente después de cada cambio
        """
        JSONManager.save(Config.SUBSCRIBERS_FILE, self.subscribers)
    
    
    def print_stats(self):
        """Imprime estadísticas formateadas"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DE SUSCRIPTORES")
        print("="*70)
        print(f"Total suscriptores: {stats['total_subscribers']}")
        print(f"  ✅ Activos: {stats['active_subscribers']}")
        print(f"  ⏸️  Inactivos: {stats['inactive_subscribers']}")
        print(f"\nSeñales enviadas:")
        print(f"  Hoy: {stats['signals_today']}")
        print(f"  Total: {stats['total_signals_sent']}")
        
        if stats['most_active_user']:
            print(f"\nUsuario más activo:")
            print(f"  {stats['most_active_user']['username']}")
            print(f"  {stats['most_active_user']['signals']} señales recibidas")
        
        print("="*70 + "\n")
