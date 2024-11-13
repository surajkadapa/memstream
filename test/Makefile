CC=gcc
CFLAGS=-Wall -pthread -I..
SRCS=test.c ../cache.c
OBJS=$(SRCS:.c=.o)
TARGET=cache_test

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

test.o: test.c ../cache.h
	$(CC) $(CFLAGS) -c $<

../cache.o: ../cache.c ../cache.h ../cache_internal.h
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET) ../cache.o

.PHONY: all clean