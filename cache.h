#ifndef CACHE_H
#define CACHE_H

#include <stddef.h>
#include <stdint.h>

int cache_init(size_t max_memory_size);
int cache_connect(void);
void cache_destroy(void);
int cache_set(const char* key, const void* value, size_t value_size);
int cache_get(const char* key, void* value, size_t* value_size);
int cache_delete(const char* key);

typedef struct {
    size_t total_size;
    size_t used_size;
    size_t total_entries;
    size_t hits;
    size_t misses;
} cache_stats_t;

int cache_get_stats(cache_stats_t* stats);

#endif