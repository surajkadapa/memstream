#!/bin/bash
# start.sh

# Start Fluentd in the background
# fluentd -c /etc/fluent/fluent.conf &

# Wait for Fluentd to start
sleep 2

# Start the Python service
python3 /app/reader.py