# alert_system.py
from kafka import KafkaConsumer
import json
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import threading
from collections import defaultdict
import time

# Initialize colorama for colored output
init()

class AlertSystem:
    def __init__(self, kafka_bootstrap_servers):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.last_heartbeats = defaultdict(datetime.now)
        self.heartbeat_threshold = timedelta(seconds=10)  # Alert if no heartbeat for 10s

    def start(self):
        consumer = KafkaConsumer(
            'cache.log.error',
            'cache.log.warn',
            'cache.heartbeat',
            bootstrap_servers=[self.kafka_bootstrap_servers],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='alert-consumer-group'
        )

        # Start heartbeat monitoring in a separate thread
        threading.Thread(target=self.monitor_heartbeats, daemon=True).start()

        for message in consumer:
            self.process_message(message)

    def process_message(self, message):
        topic = message.topic
        data = message.value

        if topic == 'cache.heartbeat':
            self.handle_heartbeat(data)
        elif topic == 'cache.log.error':
            self.handle_error(data)
        elif topic == 'cache.log.warn':
            self.handle_warning(data)

    def handle_heartbeat(self, data):
        node_id = data['node_id']
        self.last_heartbeats[node_id] = datetime.now()
        if data['status'] == 'DOWN':
            self.print_alert(f"Node {node_id} is shutting down!", "SHUTDOWN")

    def handle_error(self, data):
        self.print_alert(
            f"Error in {data['service_name']} (Node {data['node_id']}): "
            f"{data['error_details']['error_message']}", 
            "ERROR"
        )

    def handle_warning(self, data):
        self.print_alert(
            f"Warning in {data['service_name']} (Node {data['node_id']}): "
            f"{data['message']}", 
            "WARNING"
        )

    def monitor_heartbeats(self):
        while True:
            now = datetime.now()
            for node_id, last_heartbeat in self.last_heartbeats.items():
                if now - last_heartbeat > self.heartbeat_threshold:
                    self.print_alert(
                        f"No heartbeat from Node {node_id} for {self.heartbeat_threshold.seconds} seconds!",
                        "HEARTBEAT MISSING"
                    )
            time.sleep(5)

    def print_alert(self, message, alert_type):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = {
            "ERROR": Fore.RED,
            "WARNING": Fore.YELLOW,
            "HEARTBEAT MISSING": Fore.MAGENTA,
            "SHUTDOWN": Fore.CYAN
        }.get(alert_type, Fore.WHITE)

        print(f"{color}[{timestamp}] {alert_type}: {message}{Style.RESET_ALL}")

def main():
    kafka_bootstrap_servers = "100.102.21.101:9092"
    alert_system = AlertSystem(kafka_bootstrap_servers)
    
    print(f"{Fore.GREEN}Starting Alert System...{Style.RESET_ALL}")
    print(f"Monitoring Kafka at {kafka_bootstrap_servers}")
    print("Watching for:")
    print("- Errors (RED)")
    print("- Warnings (YELLOW)")
    print("- Missing Heartbeats (MAGENTA)")
    print("- Node Shutdowns (CYAN)")
    print("-" * 50)
    
    alert_system.start()

if __name__ == "__main__":
    main()