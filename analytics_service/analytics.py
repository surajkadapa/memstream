from flask import Flask, jsonify
import ctypes
import json
import time
import uuid
import sys
import os
import signal
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from ctypes import c_int, c_char_p, c_void_p, c_size_t, CDLL
from fluent import sender
import threading

app = Flask(__name__)
shutdown_flag = threading.Event()

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

class CacheStatsService:
    def __init__(self):
        fluent_host = os.getenv('FLUENT_HOST', 'localhost')
        fluent_port = int(os.getenv('FLUENT_PORT', '24224'))
        print(f"Connecting to fluentd at {fluent_host}:{fluent_port}")
        
        self.logger = sender.FluentSender(
            'cache',
            host=fluent_host,
            port=fluent_port,
            nanosecond_precision=True
        )
        self.node_id = "Stats_Service"
        self.service_name = "CacheStatsService"
        self.send_registration()
        self.init_cache()
        self.running = True
        self.shutdown_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop)
        self.heartbeat_thread.daemon = False
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
        if not self.logger.emit('registration', registration_msg):
            print(f"Failed to send registration: {self.logger.last_error}")

    def send_heartbeat(self):
        """Send single heartbeat message"""
        heartbeat_msg = {
            "node_id": self.node_id,
            "message_type": "HEARTBEAT",
            "status": "UP",
            "timestamp": datetime.now().isoformat()
        }
        if not self.logger.emit('heartbeat', heartbeat_msg):
            print(f"Failed to send heartbeat: {self.logger.last_error}")

    def heartbeat_loop(self):
        """Continuous heartbeat sender"""
        while self.running and not self.shutdown_event.is_set():
            self.send_heartbeat()
            self.shutdown_event.wait(timeout=5)

    def log_info(self, message: str, **kwargs):
        """Send INFO level log message"""
        try:
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
            if not self.logger.emit('log.info', log_msg):
                print(f"Failed to send info log: {self.logger.last_error}")
        except Exception as e:
            print(f"Error sending info log: {str(e)}")

    def log_error(self, message: str, error_code: str, error_message: str):
        """Send ERROR level log message"""
        try:
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
            if not self.logger.emit('log.error', log_msg):
                print(f"Failed to send error log: {self.logger.last_error}")
        except Exception as e:
            print(f"Error sending error log: {str(e)}")

    def init_cache(self):
        """Initialize cache connection"""
        try:
            self.lib = CDLL("/app/libcache.so")
            
            # Set up function signatures
            self.lib.cache_connect.restype = c_int
            self.lib.cache_connect.argtypes = []
            
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
        if hasattr(self, 'running') and self.running:
            print("Starting cleanup process...")
            self.running = False
            self.shutdown_event.set()
            
            try:
                # Stop heartbeat thread first
                if hasattr(self, 'heartbeat_thread') and self.heartbeat_thread.is_alive():
                    print("Stopping heartbeat thread...")
                    self.heartbeat_thread.join(timeout=5)

                messages = [
                    ('log.warn', {
                        "log_id": str(uuid.uuid4()),
                        "node_id": self.node_id,
                        "log_level": "WARN",
                        "message_type": "LOG",
                        "message": "node going off",
                        "service_name": self.service_name,
                        "response_time_ms": "0",
                        "threshold_limit_ms": "0",
                        "timestamp": datetime.now().isoformat()
                    }),
                    ('registration', {
                        "message_type": "REGISTRATION",
                        "node_id": self.node_id,
                        "service_name": self.service_name,
                        "status": "DOWN",
                        "timestamp": datetime.now().isoformat()
                    }),
                    ('heartbeat', {
                        "node_id": self.node_id,
                        "message_type": "HEARTBEAT",
                        "status": "DOWN",
                        "timestamp": datetime.now().isoformat()
                    })
                ]

                for tag, msg in messages:
                    print(f"Sending {tag} message...")
                    success = self.logger.emit(tag, msg)
                    if not success:
                        print(f"Failed to send {tag}: {self.logger.last_error}")
                    time.sleep(0.5)

                print("Waiting for final messages to be processed...")
                time.sleep(2)

            except Exception as e:
                print(f"Error during cleanup: {str(e)}")
            finally:
                try:
                    if hasattr(self, 'logger'):
                        print("Closing logger...")
                        self.logger.close()
                        print("Logger closed")
                except Exception as e:
                    print(f"Error closing logger: {str(e)}")
                print("Cleanup completed")

@app.route('/stats', methods=['GET'])
def get_stats():
    cache = app.config['cache']
    stats = cache.get_stats()
    
    if stats:
        return jsonify({
            'total_size': stats.total_size,
            'used_size': stats.used_size,
            'total_entries': stats.total_entries,
            'hits': stats.hits,
            'misses': stats.misses,
            'hit_ratio': f"{(stats.hits/(stats.hits + stats.misses) if stats.hits + stats.misses > 0 else 0):.2%}"
        })
    return jsonify({'error': 'Failed to get cache statistics'}), 500

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}")
    shutdown_flag.set()

def flask_thread():
    app.run(host='0.0.0.0', port=4002, use_reloader=False)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        cache = CacheStatsService()
        app.config['cache'] = cache

        server_thread = threading.Thread(target=flask_thread)
        server_thread.daemon = True
        server_thread.start()
        
        print("Service started, waiting for requests...")
        
        while not shutdown_flag.is_set():
            time.sleep(0.1)
            
        print("Shutdown flag received, starting cleanup...")
        if 'cache' in app.config:
            app.config['cache'].cleanup()
            
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        if 'cache' in app.config:
            app.config['cache'].cleanup()
        print("Service stopped")