#include <stdio.h>
#include <string.h>
#include "cache.h"

void print_stats() {
    cache_stats_t stats;
    if (cache_get_stats(&stats) == 0) {
        printf("\nCache Statistics:\n");
        printf("Total Entries: %zu\n", stats.total_entries);
        printf("Used Size: %zu bytes\n", stats.used_size);
        printf("Hits: %zu\n", stats.hits);
        printf("Misses: %zu\n", stats.misses);
    } else {
        printf("Failed to get cache stats\n");
    }
}

int main() {
    printf("Initializing cache...\n");
    if (cache_init(1024 * 1024) != 0) {  // 1MB cache
        printf("Failed to initialize cache\n");
        return 1;
    }
    printf("Cache initialized successfully\n");

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
        printf("Failed to set value\n");
    }

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

    // Test 3: Delete Key
    printf("\nTest 3: Delete Key\n");
    if (cache_delete(test_key) == 0) {
        printf("Successfully deleted key '%s'\n", test_key);
        
        char buffer[256];
        size_t size = sizeof(buffer);
        if (cache_get(test_key, buffer, &size) != 0) {
            printf("Verified key no longer exists\n");
        }
    }

    // Print final stats
    print_stats();

    // Cleanup
    cache_destroy();
    printf("\nCache destroyed successfully\n");

    return 0;
}