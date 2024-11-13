# cache_writer.py
import ctypes
import json
import time
from typing import Optional
import sys
import os
from dataclasses import dataclass
from ctypes import c_int, c_char_p, c_void_p, c_size_t, CDLL

@dataclass
class CacheStats:
    total_size: int
    used_size: int
    total_entries: int
    hits: int
    misses: int

class CacheStats_C(ctypes.Structure):
    _fields_ = [
        ("total_size", c_size_t),
        ("used_size", c_size_t),
        ("total_entries", c_size_t),
        ("hits", c_size_t),
        ("misses", c_size_t)
    ]

class CacheWriter:
    def __init__(self):
        # Load the shared library
        self.lib = CDLL("/app/libcache.so")

        # Set up function signatures
        self.lib.cache_connect.restype = c_int
        self.lib.cache_connect.argtypes = []

        self.lib.cache_set.restype = c_int
        self.lib.cache_set.argtypes = [c_char_p, c_void_p, c_size_t]

        self.lib.cache_get.restype = c_int
        self.lib.cache_get.argtypes = [c_char_p, c_void_p, ctypes.POINTER(c_size_t)]

        self.lib.cache_delete.restype = c_int
        self.lib.cache_delete.argtypes = [c_char_p]

        self.lib.cache_get_stats.restype = c_int
        self.lib.cache_get_stats.argtypes = [ctypes.POINTER(CacheStats_C)]

        # Connect to cache
        result = self.lib.cache_connect()
        if result != 0:
            raise RuntimeError("Failed to connect to cache")
        print("Successfully connected to cache")

    def set(self, key: str, value: str) -> bool:
        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')
        result = self.lib.cache_set(
            key_bytes,
            ctypes.cast(value_bytes, c_void_p),
            len(value_bytes)
        )
        return result == 0

    def get(self, key: str) -> Optional[str]:
        key_bytes = key.encode('utf-8')
        value_size = c_size_t(1024)  # Initial buffer size
        value_buffer = ctypes.create_string_buffer(value_size.value)

        result = self.lib.cache_get(
            key_bytes,
            ctypes.cast(value_buffer, c_void_p),
            ctypes.byref(value_size)
        )

        if result == 0:
            return value_buffer.value[:value_size.value].decode('utf-8')
        return None

    def delete(self, key: str) -> bool:
        key_bytes = key.encode('utf-8')
        result = self.lib.cache_delete(key_bytes)
        return result == 0

    def get_stats(self) -> CacheStats:
        stats = CacheStats_C()
        result = self.lib.cache_get_stats(ctypes.byref(stats))
        if result == 0:
            return CacheStats(
                total_size=stats.total_size,
                used_size=stats.used_size,
                total_entries=stats.total_entries,
                hits=stats.hits,
                misses=stats.misses
            )
        raise RuntimeError("Failed to get cache stats")

def main():
    cache = CacheWriter()

    while True:
        print("\nCache Writer Service")
        print("1. Set value")
        print("2. Get value")
        print("3. Delete value")
        print("4. Show stats")
        print("5. Exit")

        choice = input("Enter choice (1-5): ")

        if choice == "1":
            key = input("Enter key: ")
            value = input("Enter value: ")
            if cache.set(key, value):
                print("Value set successfully")
            else:
                print("Failed to set value")

        elif choice == "2":
            key = input("Enter key: ")
            value = cache.get(key)
            if value is not None:
                print(f"Value: {value}")
            else:
                print("Key not found")

        elif choice == "3":
            key = input("Enter key: ")
            if cache.delete(key):
                print("Value deleted successfully")
            else:
                print("Failed to delete value")

        elif choice == "4":
            try:
                stats = cache.get_stats()
                print("\nCache Statistics:")
                print(f"Total Size: {stats.total_size}")
                print(f"Used Size: {stats.used_size}")
                print(f"Total Entries: {stats.total_entries}")
                print(f"Cache Hits: {stats.hits}")
                print(f"Cache Misses: {stats.misses}")
            except RuntimeError as e:
                print(f"Error getting stats: {e}")

        elif choice == "5":
            print("Exiting...")
            break

        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()