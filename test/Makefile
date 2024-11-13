CC=gcc
CFLAGS=-Wall -I..
LDFLAGS=-Wl,-rpath,.. -L.. -lcache -pthread

test: test.c
	$(CC) $(CFLAGS) -o test test.c $(LDFLAGS)

clean:
	rm -f test

.PHONY: clean