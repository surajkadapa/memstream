// test.c
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/shm.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include "../cache.h"
#include "../cache_internal.h"

void print_stats() {
    cache_stats_t stats;
    if (cache_get_stats(&stats) == 0) {
        printf("\nCache Statistics:\n");
        printf("Total Entries: %zu\n", stats.total_entries);
        printf("Used Size: %zu bytes\n", stats.used_size);
        printf("Hits: %zu\n", stats.hits);
        printf("Misses: %zu\n", stats.misses);
    } else {
        printf("Failed to get cache stats - Is cache manager running?\n");
    }
}

int main() {
    printf("Starting cache tests...\n");

    // Check shared memory segment
    int shm_id = shmget(SHM_KEY, 0, 0);
    if (shm_id == -1) {
        printf("Cannot access shared memory segment - Cache manager not running?\n");
        printf("Error: %s\n", strerror(errno));
        return 1;
    }
    printf("Found shared memory segment ID: %d\n", shm_id);

    // Connect to existing cache
    if (cache_connect() != 0) {
        printf("Failed to connect to cache\n");
        return 1;
    }
    printf("Successfully connected to cache\n");

    printf("Note: Ensure cache manager is running before running tests\n");
    sleep(1);  // Give a moment to read the message

    // Test 1: Basic Set and Get
    printf("\nTest 1: Basic Set and Get\n");
    const char *test_key = "hello";
    const char *test_value = "world";

    if (cache_set(test_key, test_value, strlen(test_value) + 1) == 0) {
        printf("Successfully set key '%s'\n", test_key);

        char buffer[256];
        size_t size = sizeof(buffer);
        if (cache_get(test_key, buffer, &size) == 0) {
            printf("Successfully retrieved value: '%s'\n", buffer);
        } else {
            printf("Failed to get value\n");
        }
    } else {
        printf("Failed to set value - Is cache manager running?\n");
        return 1;
    }

    print_stats();

    // Test 2: Update Existing Key
    printf("\nTest 2: Update Existing Key\n");
    const char *new_value = "WORLD UPDATED";
    if (cache_set(test_key, new_value, strlen(new_value) + 1) == 0) {
        printf("Successfully updated key '%s'\n", test_key);

        char buffer[256];
        size_t size = sizeof(buffer);
        if (cache_get(test_key, buffer, &size) == 0) {
            printf("Retrieved updated value: '%s'\n", buffer);
        }
    }

    print_stats();

    // Test 3: Multiple Keys
    printf("\nTest 3: Multiple Keys\n");
    const char *keys[] = {"key1", "key2", "key3"};
    const char *values[] = {"value1", "value2", "value3"};

    for (int i = 0; i < 3; i++) {
        if (cache_set(keys[i], values[i], strlen(values[i]) + 1) == 0) {
            printf("Set key '%s'\n", keys[i]);

            char buffer[256];
            size_t size = sizeof(buffer);
            if (cache_get(keys[i], buffer, &size) == 0) {
                printf("Retrieved key '%s': '%s'\n", keys[i], buffer);
            }
        }
    }

    print_stats();

    // Test 4: Delete Key
    printf("\nTest 4: Delete Key\n");
    if (cache_delete(test_key) == 0) {
        printf("Successfully deleted key '%s'\n", test_key);

        char buffer[256];
        size_t size = sizeof(buffer);
        if (cache_get(test_key, buffer, &size) != 0) {
            printf("Verified key no longer exists\n");
        }
    }

    print_stats();

    // Test 5: Cache Miss
    printf("\nTest 5: Cache Miss Test\n");
    char buffer[256];
    size_t size = sizeof(buffer);
    if (cache_get("nonexistent_key", buffer, &size) != 0) {
        printf("Correctly handled cache miss for nonexistent key\n");
    }

    print_stats();

    printf("\nTests completed. Cache manager continues running.\n");
    printf("You can run these tests multiple times while cache manager is running.\n");

    return 0;
}