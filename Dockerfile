# Dockerfile
FROM ubuntu:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    sudo \
    ruby \
    ruby-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Fluentd directly using gem
RUN gem install fluentd --no-doc
RUN gem install fluent-plugin-kafka --no-doc

# Create directories for Fluentd
RUN mkdir -p /etc/fluent
RUN mkdir -p /var/log/fluent

# Copy required files
WORKDIR /app
COPY libcache.so /app/
COPY cache_writer.py /app/
COPY fluent.conf /etc/fluent/fluent.conf
COPY start.sh /app/

# Install Python dependencies
RUN pip3 install dataclasses typing fluent-logger --break-system-packages

# Make start script executable
RUN chmod +x /app/start.sh

# Start both services
CMD ["/app/start.sh"]