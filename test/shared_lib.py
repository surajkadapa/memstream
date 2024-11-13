#!/usr/bin/env python3

from ctypes import *
import os
import time

class CacheStats(Structure):
    _fields_ = [
        ("total_size", c_size_t),
        ("used_size", c_size_t),
        ("total_entries", c_size_t),
        ("hits", c_size_t),
        ("misses", c_size_t)
    ]

class CacheTest:
    def __init__(self):
        # Load the shared library
        try:
            # Try to load from current directory
            self.lib = CDLL("./libcache.so")
        except OSError:
            # Try to load from parent directory
            self.lib = CDLL("../libcache.so")

        # Set up function signatures
        self.setup_functions()

    def setup_functions(self):
        # cache_init
        self.lib.cache_init.argtypes = [c_size_t]
        self.lib.cache_init.restype = c_int

        # cache_destroy
        self.lib.cache_destroy.argtypes = []
        self.lib.cache_destroy.restype = None

        # cache_set
        self.lib.cache_set.argtypes = [c_char_p, c_void_p, c_size_t]
        self.lib.cache_set.restype = c_int

        # cache_get
        self.lib.cache_get.argtypes = [c_char_p, c_void_p, POINTER(c_size_t)]
        self.lib.cache_get.restype = c_int

        # cache_delete
        self.lib.cache_delete.argtypes = [c_char_p]
        self.lib.cache_delete.restype = c_int

        # cache_get_stats
        self.lib.cache_get_stats.argtypes = [POINTER(CacheStats)]
        self.lib.cache_get_stats.restype = c_int

    def run_tests(self):
        print("Starting cache tests...")

        # Initialize cache
        print("\nTest 1: Initialize Cache")
        result = self.lib.cache_init(1024 * 1024)  # 1MB cache
        print(f"Cache initialization: {'Success' if result == 0 else 'Failed'}")

        # Test basic set/get
        print("\nTest 2: Basic Set/Get")
        test_key = b"test_key"
        test_value = b"Hello, Cache!"
        
        result = self.lib.cache_set(test_key, test_value, len(test_value))
        print(f"Set operation: {'Success' if result == 0 else 'Failed'}")

        buffer = create_string_buffer(256)
        buffer_size = c_size_t(256)
        
        result = self.lib.cache_get(test_key, buffer, byref(buffer_size))
        if result == 0:
            print(f"Get operation: Success")
            print(f"Retrieved value: {buffer.value.decode()}")
        else:
            print("Get operation: Failed")

        # Test stats
        print("\nTest 3: Cache Statistics")
        stats = CacheStats()
        result = self.lib.cache_get_stats(byref(stats))
        if result == 0:
            print("Cache Stats:")
            print(f"Total Entries: {stats.total_entries}")
            print(f"Used Size: {stats.used_size} bytes")
            print(f"Hits: {stats.hits}")
            print(f"Misses: {stats.misses}")

        # Test update
        print("\nTest 4: Update Existing Key")
        new_value = b"Updated Value!"
        result = self.lib.cache_set(test_key, new_value, len(new_value))
        print(f"Update operation: {'Success' if result == 0 else 'Failed'}")

        buffer = create_string_buffer(256)
        buffer_size = c_size_t(256)
        result = self.lib.cache_get(test_key, buffer, byref(buffer_size))
        if result == 0:
            print(f"Retrieved updated value: {buffer.value.decode()}")

        # Test delete
        print("\nTest 5: Delete Key")
        result = self.lib.cache_delete(test_key)
        print(f"Delete operation: {'Success' if result == 0 else 'Failed'}")

        # Verify deletion
        buffer = create_string_buffer(256)
        buffer_size = c_size_t(256)
        result = self.lib.cache_get(test_key, buffer, byref(buffer_size))
        print(f"Key exists after deletion: {'Yes' if result == 0 else 'No'}")

        # Cleanup
        print("\nTest 6: Cleanup")
        self.lib.cache_destroy()
        print("Cache destroyed")

if __name__ == "__main__":
    test = CacheTest()
    test.run_tests()