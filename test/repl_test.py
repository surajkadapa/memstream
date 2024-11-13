#!/usr/bin/env python3
# cache_repl.py

from ctypes import *
import sys
import time

class CacheInterface:
    def __init__(self):
        try:
            # Load the shared library
            self.lib = CDLL("../libcache.so")
            self.setup_functions()

            # Connect to existing cache
            if self.lib.cache_connect() != 0:
                print("Failed to connect to cache. Is cache manager running?")
                sys.exit(1)
            print("Successfully connected to cache")

        except Exception as e:
            print(f"Failed to initialize cache interface: {str(e)}")
            sys.exit(1)

    def setup_functions(self):
        # cache_set
        self.lib.cache_set.argtypes = [c_char_p, c_void_p, c_size_t]
        self.lib.cache_set.restype = c_int

        # cache_get
        self.lib.cache_get.argtypes = [c_char_p, c_void_p, POINTER(c_size_t)]
        self.lib.cache_get.restype = c_int

        # cache_delete
        self.lib.cache_delete.argtypes = [c_char_p]
        self.lib.cache_delete.restype = c_int

    def set(self, key: str, value: str) -> bool:
        try:
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            result = self.lib.cache_set(key_bytes, value_bytes, len(value_bytes))
            if result == 0:
                print(f"Successfully set key '{key}' with value '{value}'")
                return True
            else:
                print(f"Failed to set key '{key}'")
                return False
        except Exception as e:
            print(f"Error setting key: {str(e)}")
            return False

    def get(self, key: str, max_size: int = 1024) -> str:
        try:
            key_bytes = key.encode('utf-8')
            buffer = create_string_buffer(max_size)
            size = c_size_t(max_size)

            result = self.lib.cache_get(key_bytes, buffer, byref(size))
            if result == 0:
                value = buffer.value.decode('utf-8')
                print(f"Value for key '{key}': '{value}'")
                return value
            else:
                print(f"Key '{key}' not found")
                return None
        except Exception as e:
            print(f"Error getting key: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        try:
            key_bytes = key.encode('utf-8')
            result = self.lib.cache_delete(key_bytes)
            if result == 0:
                print(f"Successfully deleted key '{key}'")
                return True
            else:
                print(f"Failed to delete key '{key}' (key might not exist)")
                return False
        except Exception as e:
            print(f"Error deleting key: {str(e)}")
            return False

def print_help():
    print("\nAvailable commands:")
    print("  set <key> <value>  - Store a key-value pair")
    print("  get <key>         - Retrieve value for a key")
    print("  del <key>         - Delete a key-value pair")
    print("  help             - Show this help message")
    print("  exit             - Exit the program")

def main():
    cache = CacheInterface()
    print("\nWelcome to Cache REPL!")
    print_help()

    while True:
        try:
            command = input("\n> ").strip()

            if not command:
                continue

            parts = command.split()
            cmd = parts[0].lower()

            if cmd == "exit":
                print("Goodbye!")
                break

            elif cmd == "help":
                print_help()

            elif cmd == "set":
                if len(parts) < 3:
                    print("Usage: set <key> <value>")
                    continue
                key = parts[1]
                value = " ".join(parts[2:])  # Allow spaces in value
                cache.set(key, value)

            elif cmd == "get":
                if len(parts) != 2:
                    print("Usage: get <key>")
                    continue
                cache.get(parts[1])

            elif cmd == "del":
                if len(parts) != 2:
                    print("Usage: del <key>")
                    continue
                cache.delete(parts[1])

            else:
                print(f"Unknown command: {cmd}")
                print_help()

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()