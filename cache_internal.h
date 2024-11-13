#ifndef CACHE_INTERNAL_H
#define CACHE_INTERNAL_H

#include <pthread.h>
#include <time.h>
#include "cache.h"

#define MAX_KEY_LENGTH 256
#define MAX_ENTRIES 10000
#define SHM_KEY 0x1234 

typedef struct {
    char key[MAX_KEY_LENGTH];
    size_t value_size;
    time_t last_access;
    time_t created_at;
    uint32_t access_count;
    int is_valid;
    size_t data_offset;  
} entry_t;

typedef struct {
    pthread_rwlock_t lock;
    size_t max_memory;
    size_t used_memory;
    cache_stats_t stats;
    entry_t entries[MAX_ENTRIES];
    char data[];  
} cache_t;

#endif