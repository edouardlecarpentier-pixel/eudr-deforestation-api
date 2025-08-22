import redis
import json
import hashlib
from typing import Optional, Any
import os
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Cache Redis connecté")
        except Exception as e:
            logger.warning(f"Redis non disponible: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, data: dict) -> str:
        """Génère une clé unique basée sur les données"""
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[dict]:
        """Récupère une valeur depuis le cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Erreur cache get: {e}")
        
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Stocke une valeur dans le cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            logger.debug(f"Valeur mise en cache: {key}")
        except Exception as e:
            logger.error(f"Erreur cache set: {e}")
    
    async def delete(self, key: str):
        """Supprime une valeur du cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Erreur cache delete: {e}")
    
    async def get_analysis_cache(self, coordinates: list, analysis_type: str) -> Optional[dict]:
        """Récupère une analyse depuis le cache"""
        key = self._generate_key(f"analysis_{analysis_type}", {
            "coordinates": coordinates
        })
        return await self.get(key)
    
    async def set_analysis_cache(self, coordinates: list, analysis_type: str, result: dict):
        """Met en cache une analyse"""
        key = self._generate_key(f"analysis_{analysis_type}", {
            "coordinates": coordinates
        })
        # Cache pour 1 heure
        await self.set(key, result, 3600)
    
    def get_cache_stats(self) -> dict:
        """Retourne les statistiques du cache"""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0)
            }
        except Exception as e:
            logger.error(f"Erreur stats cache: {e}")
            return {"status": "error", "error": str(e)}
