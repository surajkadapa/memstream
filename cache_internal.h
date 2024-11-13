#ifndef CACHE_INTERNAL_H
#define CACHE_INTERNAL_H

#include <pthread.h>
#include <time.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "cache.h"

#define MAX_KEY_LENGTH 256
#define MAX_ENTRIES 10000
#define SHM_KEY 0x1234  // Fixed key for shared memory

typedef struct {
    char key[MAX_KEY_LENGTH];
    size_t value_size;
    time_t last_access;
    time_t created_at;
    uint32_t access_count;
    int is_valid;
    size_t data_offset;  // Offset to value in data region
} entry_t;

typedef struct {
    pthread_rwlock_t lock;
    size_t max_memory;
    size_t used_memory;
    cache_stats_t stats;
    entry_t entries[MAX_ENTRIES];
    char data[];  // Flexible array member for values
} cache_t;

#endif