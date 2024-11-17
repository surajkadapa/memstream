import os
from elasticsearch import Elasticsearch, helpers
from kafka import KafkaConsumer
import json
from datetime import datetime
import sys
import traceback
import time
from urllib3.exceptions import ProtocolError
from elasticsearch.exceptions import ConnectionError as ESConnectionError

# Configuration
ELASTICSEARCH_HOST = 'http://localhost:9200'
KAFKA_BOOTSTRAP_SERVERS = '192.168.122.76:9092'  # Replace with your Kafka VM IP
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def get_elasticsearch_client():
    """Create Elasticsearch client with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            es = Elasticsearch(
                [ELASTICSEARCH_HOST],
                retry_on_timeout=True,
                max_retries=3,
                request_timeout=30
            )
            # Test connection
            es.info()
            print("Successfully connected to Elasticsearch")
            return es
        except Exception as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed to connect to Elasticsearch: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise

def process_message_with_retry(es, msg, max_retries=3):
    """Process message with retry logic"""
    try:
        topic = msg.topic
        data = msg.value
        
        print(f"\n=== Received Message ===")
        print(f"Topic: {topic}")
        print(f"Partition: {msg.partition}")
        print(f"Offset: {msg.offset}")
        print(f"Value: {json.dumps(data, indent=2)}")
        print("========================")
        
        # Add metadata
        data['kafka_topic'] = topic
        data['indexed_at'] = datetime.now().isoformat()
        
        # Index document
        response = es.index(index='cache-logs', document=data)
        print(f"Indexed in Elasticsearch: {response['result']}")
        return True
            
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        traceback.print_exc()
        return False

def main():
    print(f"Starting Kafka to Elasticsearch service")
    print(f"Elasticsearch: {ELASTICSEARCH_HOST}")
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    
    # Initialize Elasticsearch
    try:
        es = get_elasticsearch_client()
    except Exception as e:
        print(f"Failed to initialize Elasticsearch: {str(e)}")
        return

    print("\nInitializing Kafka Consumer...")
    # Initialize Kafka consumer
    topics = ['cache.log.info', 'cache.log.warn', 'cache.log.error', 
              'cache.registration', 'cache.heartbeat']
    
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',  # Start from beginning
        enable_auto_commit=True,
        group_id='elastic-consumer-group'
    )

    print(f"Subscribed to topics: {consumer.subscription()}")
    print(f"Partition assignment: {consumer.assignment()}")
    
    print("Starting to consume messages...")
    
    try:
        for message in consumer:
            success = process_message_with_retry(es, message)
            if not success:
                print("Failed to process message, reconnecting to Elasticsearch...")
                es = get_elasticsearch_client()
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
    finally:
        consumer.close()
        print("Consumer closed")

if __name__ == "__main__":
    main()