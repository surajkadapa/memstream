from flask import Flask, jsonify, request
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

class CacheReadService:
    def __init__(self):
        self.logger = sender.FluentSender('cache', host='localhost', port=24224)
        self.node_id = "Read_Service"
        self.service_name = "CacheReadService"
        self.send_registration()
        self.init_cache()
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
            time.sleep(5)

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
            
            self.lib.cache_get.restype = c_int
            self.lib.cache_get.argtypes = [c_char_p, c_void_p, ctypes.POINTER(c_size_t)]
            
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

    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        start_time = time.time()
        try:
            key_bytes = key.encode('utf-8')
            value_size = c_size_t(1024)  # Initial buffer size
            value_buffer = ctypes.create_string_buffer(value_size.value)
            
            result = self.lib.cache_get(
                key_bytes,
                ctypes.cast(value_buffer, c_void_p),
                ctypes.byref(value_size)
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if result == 0:
                value = value_buffer.value[:value_size.value].decode('utf-8')
                self.log_info(
                    f"Retrieved value for key: {key}",
                    operation="GET",
                    key=key,
                    value_size=value_size.value
                )
                
                # Log warning if operation took too long
                if response_time > 100:  # 100ms threshold
                    self.log_warn(
                        f"Slow GET operation for key: {key}",
                        response_time,
                        100.0
                    )
                
                return value
            else:
                self.log_error(
                    f"Failed to get value for key: {key}",
                    "GET_ERROR",
                    "Cache get operation returned error"
                )
                return None
                
        except Exception as e:
            self.log_error(
                f"Exception during GET operation for key: {key}",
                "GET_EXCEPTION",
                str(e)
            )
            return None

    def cleanup(self):
        """Cleanup before exit"""
        try:
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
            time.sleep(3)

        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
        finally:
            try:
                self.logger.close()
            except:
                pass

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    cache = app.config['cache']
    value = cache.get(key)
    
    if value is not None:
        return jsonify({
            'key': key,
            'value': value
        })
    return jsonify({'error': f'Key not found: {key}'}), 404

@app.route('/exists/<key>', methods=['GET'])
def check_exists(key):
    cache = app.config['cache']
    value = cache.get(key)
    
    return jsonify({
        'key': key,
        'exists': value is not None
    })

def cleanup_handler(signum, frame):
    print("\nReceived shutdown signal...")
    app.config['cache'].cleanup()
    print("Service stopped.")
    sys.exit(0)

if __name__ == '__main__':
    try:
        cache = CacheReadService()
        app.config['cache'] = cache
        
        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)
        
        print("Starting Cache Read Service on port 4003")
        app.run(host='0.0.0.0', port=4003)
    finally:
        cache.cleanup()
        print("Service stopped.")