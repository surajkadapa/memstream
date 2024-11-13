CC=gcc
CFLAGS=-Wall -fPIC
LDFLAGS=-shared -pthread

all: libcache.so cache_manager

# Shared library
libcache.so: cache.o
	$(CC) $(LDFLAGS) -o $@ $^

# Cache manager executable
cache_manager: cache_manager.o libcache.so
	$(CC) -o $@ cache_manager.o -L. -lcache -pthread -Wl,-rpath,.

cache.o: cache.c cache.h cache_internal.h
	$(CC) $(CFLAGS) -c $<

cache_manager.o: cache_manager.c cache.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f *.o libcache.so cache_manager

.PHONY: all clean