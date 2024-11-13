FROM ubuntu

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gcc \
    make \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY cache.h /app/
COPY cache_internal.h /app/
COPY cache.c /app/

COPY cache_writer.py /app/

RUN gcc -shared -o libcache.so -fPIC cache.c -lpthread

RUN pip3 install dataclasses typing --break-system-packages

CMD ["python3", "cache_writer.py"]
