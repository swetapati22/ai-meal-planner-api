"""
File-based caching service for meal plans
Stores meal plan JSON files locally with a mapper for quick lookup
"""
from typing import Optional, Dict, Any
import json
import os
import hashlib
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """File-based caching service with mapper for meal plans"""
    
    def __init__(self):
        self.cache_dir = "meals_store"
        self.mapper_file = os.path.join(self.cache_dir, "mapper.json")
        self.enabled = settings.enable_cache
        
        #Create cache directory if it doesn't exist:
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            #Initialize mapper if it doesn't exist:
            if not os.path.exists(self.mapper_file):
                self._save_mapper({})
    
    def _make_cache_key(
        self,
        dietary_restrictions: list,
        preferences: list,
        duration_days: int,
        special_requirements: list
    ) -> str:
        """
        Create a deterministic cache key from query parameters.
        All parameters must match exactly for a cache hit.
        """
        #Sort lists to ensure consistent keys:
        restrictions_sorted = sorted(dietary_restrictions or [])
        preferences_sorted = sorted(preferences or [])
        special_sorted = sorted(special_requirements or [])
        
        #Create a unique string representation:
        key_string = json.dumps({
            "dietary_restrictions": restrictions_sorted,
            "preferences": preferences_sorted,
            "duration_days": duration_days,
            "special_requirements": special_sorted
        }, sort_keys=True)
        
        #Create hash for shorter filename:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return key_hash
    
    def _load_mapper(self) -> Dict[str, Any]:
        """Load the mapper from file"""
        try:
            if os.path.exists(self.mapper_file):
                with open(self.mapper_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"[CACHE] Failed to load mapper: {str(e)}")
            return {}
    
    def _save_mapper(self, mapper: Dict[str, Any]) -> None:
        """Save the mapper to file"""
        try:
            with open(self.mapper_file, 'w') as f:
                json.dump(mapper, f, indent=2)
        except Exception as e:
            logger.error(f"[CACHE] Failed to save mapper: {str(e)}")
    
    def get_meal_plan(
        self,
        dietary_restrictions: list,
        preferences: list,
        duration_days: int,
        special_requirements: list
    ) -> Optional[Dict[str, Any]]:
        """
        Get meal plan from cache if exact match exists.
        Returns the meal plan JSON or None if not found.
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._make_cache_key(
                dietary_restrictions,
                preferences,
                duration_days,
                special_requirements
            )
            
            mapper = self._load_mapper()
            
            #Check if cache key exists in mapper:
            if cache_key in mapper:
                filename = mapper[cache_key].get("filename")
                if filename:
                    filepath = os.path.join(self.cache_dir, filename)
                    if os.path.exists(filepath):
                        logger.info(f"[CACHE] Cache hit for key: {cache_key[:8]}...")
                        with open(filepath, 'r') as f:
                            return json.load(f)
                    else:
                        #File missing, remove from mapper:
                        logger.warning(f"[CACHE] Cached file missing: {filename}, removing from mapper")
                        del mapper[cache_key]
                        self._save_mapper(mapper)
            
            logger.info(f"[CACHE] Cache miss for key: {cache_key[:8]}...")
            return None
            
        except Exception as e:
            logger.error(f"[CACHE] Error getting meal plan from cache: {str(e)}")
            return None
    
    def save_meal_plan(
        self,
        dietary_restrictions: list,
        preferences: list,
        duration_days: int,
        special_requirements: list,
        meal_plan_data: Dict[str, Any]
    ) -> None:
        """
        Save meal plan to cache with mapper entry.
        """
        if not self.enabled:
            return
        
        try:
            cache_key = self._make_cache_key(
                dietary_restrictions,
                preferences,
                duration_days,
                special_requirements
            )
            
            #Create filename with timestamp for uniqueness:
            import time
            timestamp = int(time.time())
            filename = f"meal_plan_{cache_key}_{timestamp}.json"
            filepath = os.path.join(self.cache_dir, filename)
            
            #Save meal plan JSON:
            with open(filepath, 'w') as f:
                json.dump(meal_plan_data, f, indent=2)
            
            #Update mapper:
            mapper = self._load_mapper()
            mapper[cache_key] = {
                "filename": filename,
                "dietary_restrictions": sorted(dietary_restrictions or []),
                "preferences": sorted(preferences or []),
                "duration_days": duration_days,
                "special_requirements": sorted(special_requirements or []),
                "cached_at": timestamp
            }
            self._save_mapper(mapper)
            
            logger.info(f"[CACHE] Saved meal plan to cache: {filename}")
            
        except Exception as e:
            logger.error(f"[CACHE] Error saving meal plan to cache: {str(e)}")
    
    def clear(self) -> None:
        """Clear all cached meal plans and mapper"""
        try:
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.cache_dir, filename)
                        os.remove(filepath)
            self._save_mapper({})
            logger.info("[CACHE] Cleared all cached meal plans")
        except Exception as e:
            logger.error(f"[CACHE] Error clearing cache: {str(e)}")
