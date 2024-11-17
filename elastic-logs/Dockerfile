FROM python:3.9-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY kafka_to_elastic.py .

CMD ["python", "kafka_to_elastic.py"]