"""
Gestor de archivos JSON

Maneja lectura/escritura segura de archivos JSON con:
- Validación de errores
- Creación automática de archivos
- Respaldo de datos
- Pretty printing
"""

import json
from pathlib import Path
from typing import Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONManager:
    """
    Gestor centralizado de archivos JSON
    
    Maneja toda la persistencia de datos en formato JSON:
    - subscribers.json
    - active_signals.json
    - performance.json
    """
    
    @staticmethod
    def load(filepath: Path, default: Any = None) -> Any:
        """
        Carga datos desde un archivo JSON
        
        Args:
            filepath: Path o string del archivo
            default: Valor a retornar si el archivo no existe
        
        Returns:
            Datos cargados o default si no existe
        
        Ejemplo:
            >>> from utils import JSONManager
            >>> data = JSONManager.load('data/subscribers.json', {})
            >>> print(f"Cargados {len(data)} suscriptores")
        """
        filepath = Path(filepath)
        
        # Si no existe, retornar default
        if not filepath.exists():
            logger.debug(f"📂 Archivo no existe, usando default: {filepath}")
            return default if default is not None else {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"✅ Cargado: {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON en {filepath}: {e}")
            logger.warning(f"⚠️  Retornando default debido a JSON inválido")
            return default if default is not None else {}
            
        except Exception as e:
            logger.error(f"❌ Error leyendo {filepath}: {e}")
            return default if default is not None else {}
    
    
    @staticmethod
    def save(filepath: Path, data: Any, backup: bool = True):
        """
        Guarda datos en un archivo JSON
        
        Args:
            filepath: Path o string del archivo
            data: Datos a guardar (dict, list, etc.)
            backup: Si True, crea backup antes de sobrescribir
        
        Características:
            - Crea el directorio si no existe
            - Backup automático (.bak)
            - Pretty print (indent=2)
            - Encoding UTF-8
        
        Ejemplo:
            >>> data = {'user1': {'signals': 10}}
            >>> JSONManager.save('data/stats.json', data)
        """
        filepath = Path(filepath)
        
        # Crear directorio si no existe
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Hacer backup del archivo existente
        if backup and filepath.exists():
            try:
                backup_path = filepath.with_suffix('.bak')
                filepath.rename(backup_path)
                logger.debug(f"💾 Backup creado: {backup_path}")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo crear backup: {e}")
        
        # Guardar datos
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"✅ Guardado: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando {filepath}: {e}")
            
            # Restaurar backup si falla
            if backup:
                backup_path = filepath.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.rename(filepath)
                    logger.warning("⚠️  Backup restaurado debido a error")
            
            raise
    
    
    @staticmethod
    def append(filepath: Path, item: Any, max_items: Optional[int] = None):
        """
        Añade un elemento a una lista en JSON
        
        Args:
            filepath: Archivo JSON que contiene una lista
            item: Elemento a añadir
            max_items: Límite de elementos (opcional)
                      Si se supera, elimina los más antiguos
        
        Ejemplo:
            >>> signal = {'type': 'BUY', 'price': 95500}
            >>> JSONManager.append('data/history.json', signal, max_items=1000)
        """
        # Cargar lista existente
        data = JSONManager.load(filepath, [])
        
        if not isinstance(data, list):
            logger.error(f"❌ {filepath} no contiene una lista")
            return
        
        # Añadir nuevo elemento
        data.append(item)
        
        # Limitar tamaño si es necesario
        if max_items and len(data) > max_items:
            data = data[-max_items:]  # Mantener los últimos N
            logger.debug(f"🔄 Lista limitada a {max_items} elementos")
        
        # Guardar
        JSONManager.save(filepath, data)
    
    
    @staticmethod
    def update(filepath: Path, key: str, value: Any):
        """
        Actualiza un valor específico en un JSON dict
        
        Args:
            filepath: Archivo JSON
            key: Clave a actualizar
            value: Nuevo valor
        
        Ejemplo:
            >>> JSONManager.update('data/config.json', 'last_update', datetime.now())
        """
        data = JSONManager.load(filepath, {})
        
        if not isinstance(data, dict):
            logger.error(f"❌ {filepath} no contiene un diccionario")
            return
        
        data[key] = value
        JSONManager.save(filepath, data)
    
    
    @staticmethod
    def delete_key(filepath: Path, key: str) -> bool:
        """
        Elimina una clave de un JSON dict
        
        Args:
            filepath: Archivo JSON
            key: Clave a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        data = JSONManager.load(filepath, {})
        
        if not isinstance(data, dict):
            logger.error(f"❌ {filepath} no contiene un diccionario")
            return False
        
        if key in data:
            del data[key]
            JSONManager.save(filepath, data)
            logger.debug(f"🗑️  Clave '{key}' eliminada de {filepath}")
            return True
        
        return False
    
    
    @staticmethod
    def exists(filepath: Path) -> bool:
        """
        Verifica si un archivo JSON existe
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si existe
        """
        return Path(filepath).exists()
    
    
    @staticmethod
    def get_size(filepath: Path) -> int:
        """
        Obtiene el tamaño de un archivo JSON en bytes
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            Tamaño en bytes o 0 si no existe
        """
        filepath = Path(filepath)
        if filepath.exists():
            return filepath.stat().st_size
        return 0
    
    
    @staticmethod
    def backup_with_timestamp(filepath: Path):
        """
        Crea backup con timestamp en el nombre
        
        Args:
            filepath: Archivo a respaldar
        
        Ejemplo:
            >>> JSONManager.backup_with_timestamp('data/subscribers.json')
            # Crea: data/subscribers_2025-12-24_001000.json
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"⚠️  No se puede respaldar, no existe: {filepath}")
            return
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        backup_path = filepath.parent / backup_name
        
        try:
            import shutil
            shutil.copy2(filepath, backup_path)
            logger.info(f"💾 Backup creado: {backup_path}")
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
    
    
    @staticmethod
    def pretty_print(filepath: Path):
        """
        Imprime contenido de un JSON formateado
        
        Args:
            filepath: Archivo JSON a mostrar
        """
        data = JSONManager.load(filepath)
        
        if data:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Archivo vacío o no existe: {filepath}")
