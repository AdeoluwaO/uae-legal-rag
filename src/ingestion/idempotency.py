import hashlib
import json
import os
from typing import Dict, Optional


class IngestionCache:
    """
    Tracks file hashes to enable idempotent ingestion.

    If a document's hash matches the cached hash, skip re-ingestion.
    """

    CACHE_FILE = ".ingest_cache.json"

    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[str, str] = {}
        self.load()

    def load(self):
        """Load cache from disk if it exists"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def save(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def is_cached(self, law_id: str, filepath: str) -> bool:
        """Check if document is already cached with same hash"""
        if law_id not in self.cache:
            return False

        try:
            current_hash = self.get_file_hash(filepath)
            cached_hash = self.cache[law_id]
            return current_hash == cached_hash
        except Exception as e:
            print(f"Warning: Could not verify cache for {law_id}: {e}")
            return False

    def update_cache(self, law_id: str, filepath: str):
        """Update cache with current file hash"""
        try:
            current_hash = self.get_file_hash(filepath)
            self.cache[law_id] = current_hash
        except Exception as e:
            print(f"Warning: Could not update cache for {law_id}: {e}")

    def clear(self):
        """Clear all cache entries"""
        self.cache = {}
        self.save()
