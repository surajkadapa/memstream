// cache_manager.c
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include "cache.h"

volatile sig_atomic_t running = 1;

void handle_signal(int signum) {
    running = 0;
}

int main() {
    // Set up signal handling
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    printf("Starting Cache Manager...\n");

    // Initialize cache
    if (cache_init(1024 * 1024) != 0) {  // 1MB cache
        printf("Failed to initialize cache\n");
        return 1;
    }

    printf("Cache initialized successfully\n");
    printf("Cache Manager running (PID: %d)\n", getpid());
    printf("Press Ctrl+C to shutdown\n");

    // Keep running and maintain cache
    while (running) {
        // Print some basic stats every 5 seconds
        cache_stats_t stats;
        if (cache_get_stats(&stats) == 0) {
            printf("\rEntries: %zu, Used: %zu bytes    ", 
                   stats.total_entries, stats.used_size);
            fflush(stdout);
        }
        sleep(5);
    }

    printf("\nShutting down Cache Manager...\n");
    cache_destroy();
    printf("Cache Manager stopped\n");

    return 0;
}