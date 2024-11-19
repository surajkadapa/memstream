CC = gcc
CFLAGS = -Wall -O2 -fPIC
LDFLAGS = -lpthread

ANALYTICS_DIR = analytics_service
READ_DIR = read_service
WRITE_DIR = writer_service

LIB = libcache.so
MANAGER = cache_manager
OBJECTS = cache.o

.PHONY: all build clean run stop

all: build

build: $(LIB) $(MANAGER)
	cp $(LIB) $(ANALYTICS_DIR)/
	cp $(LIB) $(READ_DIR)/
	cp $(LIB) $(WRITE_DIR)/
	docker-compose build --no-cache

$(LIB): $(OBJECTS)
	$(CC) -shared -o $@ $^ $(LDFLAGS)

$(MANAGER): cache_manager.c cache.c
	$(CC) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $<

run:
	docker-compose up --force-recreate --remove-orphans

run-detached:
	docker-compose up -d --force-recreate --remove-orphans

logs:
	docker-compose logs -f

stop:
	docker-compose down

clean:
	rm -f $(LIB) $(MANAGER) $(OBJECTS)
	rm -f $(ANALYTICS_DIR)/$(LIB)
	rm -f $(READ_DIR)/$(LIB)
	rm -f $(WRITE_DIR)/$(LIB)
	docker-compose down --rmi all
	docker system prune -f

debug: CFLAGS += -g
debug: clean build

writer-logs:
	docker-compose logs -f writer

reader-logs:
	docker-compose logs -f reader

analytics-logs:
	docker-compose logs -f analytics

status:
	docker-compose ps

rebuild-writer:
	docker-compose build --no-cache writer

rebuild-reader:
	docker-compose build --no-cache reader

rebuild-analytics:
	docker-compose build --no-cache analytics

help:
	@echo "available targets:"
	@echo "  make build          - Build cache library and Docker images"
	@echo "  make run           - Run services with logs"
	@echo "  make run-detached  - Run services in background"
	@echo "  make stop          - Stop all services"
	@echo "  make clean         - Clean all built files and Docker images"
	@echo "  make debug         - Build with debug symbols"
	@echo "  make logs          - View all logs"
	@echo "  make writer-logs   - View writer service logs"
	@echo "  make reader-logs   - View reader service logs"
	@echo "  make analytics-logs- View analytics service logs"
	@echo "  make status        - Check service status"
	@echo "  make rebuild-writer- Rebuild writer service"
	@echo "  make rebuild-reader- Rebuild reader service"
	@echo "  make rebuild-analytics - Rebuild analytics service"