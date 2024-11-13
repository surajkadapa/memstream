// cache_manager.c
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "cache.h"

volatile sig_atomic_t running = 1;

void handle_signal(int signum) {
    running = 0;
}

int main() {
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    printf("Starting Cache Manager...\n");

    // Initialize cache
    int result = cache_init(1024 * 1024);  // 1MB cache
    if (result != 0) {
        printf("Failed to initialize cache: error code %d\n", result);
        return 1;
    }

    // Print shared memory info
    int shm_id = shmget(0x1234, 0, 0);
    if (shm_id != -1) {
        struct shmid_ds shm_info;
        if (shmctl(shm_id, IPC_STAT, &shm_info) == 0) {
            printf("Shared Memory Info:\n");
            printf("Segment ID: %d\n", shm_id);
            printf("Size: %lu bytes\n", shm_info.shm_segsz);
            printf("Number of attaches: %lu\n", shm_info.shm_nattch);
        }
    }

    printf("Cache initialized successfully\n");
    printf("Cache Manager running (PID: %d)\n", getpid());
    printf("Press Ctrl+C to shutdown\n");

    while (running) {
        cache_stats_t stats;
        if (cache_get_stats(&stats) == 0) {
            printf("\rEntries: %zu, Used: %zu bytes    ",
                   stats.total_entries, stats.used_size);
            fflush(stdout);
        } else {
            printf("\rFailed to get stats    ");
            fflush(stdout);
        }
        sleep(1);
    }

    printf("\nShutting down Cache Manager...\n");
    cache_destroy();
    printf("Cache Manager stopped\n");

    return 0;
}