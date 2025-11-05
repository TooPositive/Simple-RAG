"""
Persistent cache utility for repository analysis data.

Provides disk-based caching to avoid re-analyzing the repository
on every query, significantly improving performance for follow-up questions.
"""

import pickle
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class PersistentCache:
    """Persistent cache for repository analysis data."""

    def __init__(self, cache_dir: str = ".agent_cache", ttl_hours: int = 24):
        """
        Initialize persistent cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, repo_path: str) -> str:
        """
        Generate cache key based on repository path and modification time.

        Uses directory modification time to auto-invalidate cache
        when files change.

        Args:
            repo_path: Path to repository

        Returns:
            str: Cache key (hash)
        """
        repo_path = Path(repo_path).resolve()

        # Get latest modification time of Python files
        try:
            py_files = list(repo_path.rglob("*.py"))
            if py_files:
                latest_mtime = max(f.stat().st_mtime for f in py_files[:100])  # Sample first 100
            else:
                latest_mtime = repo_path.stat().st_mtime
        except Exception:
            latest_mtime = repo_path.stat().st_mtime

        # Create cache key from path + mtime
        key_string = f"{repo_path}:{latest_mtime}"
        cache_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"repo_cache_{cache_hash}.pkl"

    def get(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached repository data.

        Args:
            repo_path: Path to repository

        Returns:
            Optional[Dict]: Cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(repo_path)
        cache_file = self.cache_dir / cache_key

        if not cache_file.exists():
            return None

        try:
            # Check if cache is expired
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age > self.ttl:
                print(f"  🗑️  Cache expired ({cache_age.total_seconds() / 3600:.1f}h old), invalidating...")
                cache_file.unlink()
                return None

            # Load cache
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)

            print(f"  ✅ Loaded repository data from cache (age: {cache_age.total_seconds() / 60:.1f}m)")
            return cached_data

        except Exception as e:
            print(f"  ⚠️  Failed to load cache: {e}")
            # Delete corrupted cache file
            if cache_file.exists():
                cache_file.unlink()
            return None

    def set(self, repo_path: str, data: Dict[str, Any]) -> bool:
        """
        Save repository data to cache.

        Args:
            repo_path: Path to repository
            data: Data to cache

        Returns:
            bool: True if successful
        """
        cache_key = self._get_cache_key(repo_path)
        cache_file = self.cache_dir / cache_key

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"  💾 Saved repository data to cache")
            return True
        except Exception as e:
            print(f"  ⚠️  Failed to save cache: {e}")
            return False

    def clear(self, repo_path: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            repo_path: Specific repository to clear, or None to clear all
        """
        if repo_path:
            cache_key = self._get_cache_key(repo_path)
            cache_file = self.cache_dir / cache_key
            if cache_file.exists():
                cache_file.unlink()
                print(f"  🗑️  Cleared cache for {repo_path}")
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("repo_cache_*.pkl"):
                cache_file.unlink()
            print(f"  🗑️  Cleared all cache files")


# Global cache instance
_cache_instance = None


def get_cache() -> PersistentCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PersistentCache()
    return _cache_instance
