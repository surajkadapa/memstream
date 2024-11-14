# cache_writer.py
import ctypes
import json
import time
import uuid
import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from ctypes import c_int, c_char_p, c_void_p, c_size_t, CDLL
from fluent import sender
import threading

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
        # Initialize Fluentd logger
        self.logger = sender.FluentSender('cache', host='localhost', port=24224)
        self.node_id = str(uuid.uuid4())[:8]  # Using shorter ID for readability
        self.service_name = "CacheWriterService"
        
        # Send registration message
        self.send_registration()
        
        # Initialize cache connection
        self.init_cache()
        
        # Start heartbeat thread
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def send_registration(self):
        """Send service registration message"""
        registration_msg = {
            "message_type": "REGISTRATION",
            "node_id": self.node_id,
            "service_name": self.service_name,
            "status": "UP",
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('registration', registration_msg)

    def send_heartbeat(self):
        """Send single heartbeat message"""
        heartbeat_msg = {
            "node_id": self.node_id,
            "message_type": "HEARTBEAT",
            "status": "UP",
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('heartbeat', heartbeat_msg)

    def heartbeat_loop(self):
        """Continuous heartbeat sender"""
        while self.running:
            self.send_heartbeat()
            time.sleep(5)  # Send heartbeat every 5 seconds

    def log_info(self, message: str, **kwargs):
        """Send INFO level log message"""
        log_msg = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "INFO",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat()
        }
        log_msg.update(kwargs)
        self.logger.emit('log.info', log_msg)

    def log_warn(self, message: str, response_time_ms: float, threshold_limit_ms: float):
        """Send WARN level log message"""
        log_msg = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "WARN",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "response_time_ms": response_time_ms,
            "threshold_limit_ms": threshold_limit_ms,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('log.warn', log_msg)

    def log_error(self, message: str, error_code: str, error_message: str):
        """Send ERROR level log message"""
        log_msg = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "ERROR",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "error_details": {
                "error_code": error_code,
                "error_message": error_message
            },
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('log.error', log_msg)

    def init_cache(self):
        """Initialize cache connection"""
        try:
            self.lib = CDLL("/app/libcache.so")
            
            # Set up function signatures
            self.lib.cache_connect.restype = c_int
            self.lib.cache_connect.argtypes = []
            
            self.lib.cache_set.restype = c_int
            self.lib.cache_set.argtypes = [c_char_p, c_void_p, c_size_t]
            
            self.lib.cache_delete.restype = c_int
            self.lib.cache_delete.argtypes = [c_char_p]
            
            self.lib.cache_get_stats.restype = c_int
            self.lib.cache_get_stats.argtypes = [ctypes.POINTER(CacheStats_C)]
            
            # Connect to cache
            result = self.lib.cache_connect()
            if result != 0:
                self.log_error(
                    "Cache connection failed", 
                    "CONN_ERROR", 
                    "Failed to establish connection with cache"
                )
                raise RuntimeError("Failed to connect to cache")
            
            self.log_info("Cache connection established successfully")
            
        except Exception as e:
            self.log_error(
                "Cache initialization failed",
                "INIT_ERROR",
                str(e)
            )
            raise

    def set(self, key: str, value: str) -> bool:
        """Set value in cache"""
        start_time = time.time()
        try:
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            result = self.lib.cache_set(
                key_bytes,
                ctypes.cast(value_bytes, c_void_p),
                len(value_bytes)
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if result == 0:
                self.log_info(
                    f"Set value for key: {key}",
                    operation="SET",
                    key=key,
                    value_size=len(value_bytes)
                )
                
                # Log warning if operation took too long
                if response_time > 100:  # 100ms threshold
                    self.log_warn(
                        f"Slow SET operation for key: {key}",
                        response_time,
                        100.0
                    )
                
                return True
            else:
                self.log_error(
                    f"Failed to set value for key: {key}",
                    "SET_ERROR",
                    "Cache set operation returned error"
                )
                return False
                
        except Exception as e:
            self.log_error(
                f"Exception during SET operation for key: {key}",
                "SET_EXCEPTION",
                str(e)
            )
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        start_time = time.time()
        try:
            key_bytes = key.encode('utf-8')
            result = self.lib.cache_delete(key_bytes)
            
            response_time = (time.time() - start_time) * 1000
            
            if result == 0:
                self.log_info(
                    f"Deleted key: {key}",
                    operation="DELETE",
                    key=key
                )
                
                if response_time > 100:
                    self.log_warn(
                        f"Slow DELETE operation for key: {key}",
                        response_time,
                        100.0
                    )
                
                return True
            else:
                self.log_error(
                    f"Failed to delete key: {key}",
                    "DELETE_ERROR",
                    "Cache delete operation returned error"
                )
                return False
                
        except Exception as e:
            self.log_error(
                f"Exception during DELETE operation for key: {key}",
                "DELETE_EXCEPTION",
                str(e)
            )
            return False

    def get_stats(self) -> Optional[CacheStats]:
        """Get cache statistics"""
        try:
            stats = CacheStats_C()
            result = self.lib.cache_get_stats(ctypes.byref(stats))
            
            if result == 0:
                cache_stats = CacheStats(
                    total_size=stats.total_size,
                    used_size=stats.used_size,
                    total_entries=stats.total_entries,
                    hits=stats.hits,
                    misses=stats.misses
                )
                
                self.log_info(
                    "Retrieved cache statistics",
                    operation="STATS",
                    total_entries=stats.total_entries,
                    hit_ratio=f"{(stats.hits/(stats.hits + stats.misses) if stats.hits + stats.misses > 0 else 0):.2%}"
                )
                
                return cache_stats
            else:
                self.log_error(
                    "Failed to get cache statistics",
                    "STATS_ERROR",
                    "Cache stats operation returned error"
                )
                return None
                
        except Exception as e:
            self.log_error(
                "Exception while getting cache statistics",
                "STATS_EXCEPTION",
                str(e)
            )
            return None

    def cleanup(self):
        """Cleanup before exit"""
        self.running = False
        if self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join()

        # Send WARN log for node going down
        warn_msg = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "WARN",
            "message_type": "LOG",
            "message": "node going off",
            "service_name": self.service_name,
            "response_time_ms": "0",
            "threshold_limit_ms": "0",
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('log.warn', warn_msg)

        # Send registry update with DOWN status
        registry_msg = {
            "message_type": "REGISTRATION",
            "node_id": self.node_id,
            "service_name": self.service_name,
            "status": "DOWN",
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('registration', registry_msg)

        # Final heartbeat with DOWN status
        heartbeat_msg = {
            "node_id": self.node_id,
            "message_type": "HEARTBEAT",
            "status": "DOWN",
            "timestamp": datetime.now().isoformat()
        }
        self.logger.emit('heartbeat', heartbeat_msg)

        # Give time for logs to be sent
        time.sleep(1)


def main():
    cache = CacheWriter()
    
    try:
        while True:
            print("\nCache Writer Service")
            print("1. Set value")
            print("2. Delete value")
            print("3. Show stats")
            print("4. Exit")
            
            choice = input("Enter choice (1-4): ")
            
            if choice == "1":
                key = input("Enter key: ")
                value = input("Enter value: ")
                if cache.set(key, value):
                    print("Value set successfully")
                else:
                    print("Failed to set value")
                    
            elif choice == "2":
                key = input("Enter key: ")
                if cache.delete(key):
                    print("Value deleted successfully")
                else:
                    print("Failed to delete value")
                    
            elif choice == "3":
                stats = cache.get_stats()
                if stats:
                    print("\nCache Statistics:")
                    print(f"Total Size: {stats.total_size}")
                    print(f"Used Size: {stats.used_size}")
                    print(f"Total Entries: {stats.total_entries}")
                    print(f"Cache Hits: {stats.hits}")
                    print(f"Cache Misses: {stats.misses}")
                
            elif choice == "4":
                print("Exiting...")
                break
                
            else:
                print("Invalid choice")
    finally:
        cache.cleanup()
        print("Service stopped.")

if __name__ == "__main__":
    main()