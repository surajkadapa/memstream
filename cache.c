#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/shm.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include "cache_internal.h"
#include <bits/pthreadtypes.h>

static cache_t* cache = NULL;
static int shm_id = -1;

int cache_init(size_t max_memory_size) {
    if (cache != NULL) {
        return -1;
    }

    shm_id = shmget(SHM_KEY, sizeof(cache_t) + max_memory_size, 
                    IPC_CREAT | 0666);
    if (shm_id == -1) {
        return -1;
    }

    // Attach to shared memory
    cache = (cache_t*)shmat(shm_id, NULL, 0);
    if (cache == (void*)-1) {
        return -1;
    }

    // Initialize cache structure
    pthread_rwlockattr_t attr;
    pthread_rwlockattr_init(&attr);
    pthread_rwlockattr_setpshared(&attr, PTHREAD_PROCESS_SHARED);
    pthread_rwlock_init(&cache->lock, &attr);
    pthread_rwlockattr_destroy(&attr);

    cache->max_memory = max_memory_size;
    cache->used_memory = 0;
    memset(&cache->stats, 0, sizeof(cache_stats_t));
    memset(cache->entries, 0, sizeof(entry_t) * MAX_ENTRIES);

    return 0;
}

void cache_destroy(void) {
    if (cache) {
        pthread_rwlock_destroy(&cache->lock);
        shmdt(cache);
        if (shm_id != -1) {
            shmctl(shm_id, IPC_RMID, NULL);
        }
        cache = NULL;
        shm_id = -1;
    }
}

static entry_t* find_entry(const char* key) {
    for (size_t i = 0; i < MAX_ENTRIES; i++) {
        if (cache->entries[i].is_valid && 
            strcmp(cache->entries[i].key, key) == 0) {
            return &cache->entries[i];
        }
    }
    return NULL;
}

static entry_t* find_free_entry(void) {
    for (size_t i = 0; i < MAX_ENTRIES; i++) {
        if (!cache->entries[i].is_valid) {
            return &cache->entries[i];
        }
    }
    return NULL;
}

int cache_set(const char* key, const void* value, size_t value_size) {
    if (!cache || !key || !value || value_size == 0 || 
        strlen(key) >= MAX_KEY_LENGTH) {
        return -1;
    }

    pthread_rwlock_wrlock(&cache->lock);

    entry_t* entry = find_entry(key);
    if (entry) {
        // Update existing entry
        if (value_size > entry->value_size) {
            if (cache->used_memory - entry->value_size + value_size > cache->max_memory) {
                pthread_rwlock_unlock(&cache->lock);
                return -1;
            }
            cache->used_memory = cache->used_memory - entry->value_size + value_size;
        }
        memcpy(cache->data + entry->data_offset, value, value_size);
        entry->value_size = value_size;
    } else {
        // Create new entry
        if (cache->used_memory + value_size > cache->max_memory) {
            pthread_rwlock_unlock(&cache->lock);
            return -1;
        }
        entry = find_free_entry();
        if (!entry) {
            pthread_rwlock_unlock(&cache->lock);
            return -1;
        }
        strcpy(entry->key, key);
        entry->data_offset = cache->used_memory;
        entry->value_size = value_size;
        entry->is_valid = 1;
        entry->created_at = time(NULL);
        cache->used_memory += value_size;
        cache->stats.total_entries++;
        memcpy(cache->data + entry->data_offset, value, value_size);
    }

    entry->last_access = time(NULL);
    entry->access_count++;

    pthread_rwlock_unlock(&cache->lock);
    return 0;
}

int cache_get(const char* key, void* value, size_t* value_size) {
    if (!cache || !key || !value || !value_size) {
        return -1;
    }

    pthread_rwlock_rdlock(&cache->lock);

    entry_t* entry = find_entry(key);
    if (!entry) {
        cache->stats.misses++;
        pthread_rwlock_unlock(&cache->lock);
        return -1;
    }

    if (*value_size < entry->value_size) {
        pthread_rwlock_unlock(&cache->lock);
        return -1;
    }

    memcpy(value, cache->data + entry->data_offset, entry->value_size);
    *value_size = entry->value_size;
    entry->last_access = time(NULL);
    entry->access_count++;
    cache->stats.hits++;

    pthread_rwlock_unlock(&cache->lock);
    return 0;
}

int cache_delete(const char* key) {
    if (!cache || !key) {
        return -1;
    }

    pthread_rwlock_wrlock(&cache->lock);

    entry_t* entry = find_entry(key);
    if (!entry) {
        pthread_rwlock_unlock(&cache->lock);
        return -1;
    }

    cache->used_memory -= entry->value_size;
    cache->stats.total_entries--;
    entry->is_valid = 0;

    pthread_rwlock_unlock(&cache->lock);
    return 0;
}

int cache_get_stats(cache_stats_t* stats) {
    if (!cache || !stats) {
        return -1;
    }

    pthread_rwlock_rdlock(&cache->lock);
    memcpy(stats, &cache->stats, sizeof(cache_stats_t));
    pthread_rwlock_unlock(&cache->lock);
    return 0;
}