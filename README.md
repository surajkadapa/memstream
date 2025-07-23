# MemStream: A Shared Memory Key-Value Cache with Multi-Language Access

## Overview

**MemStream** is a high-performance inter-process key-value cache built using **POSIX shared memory**, a custom **C backend**, and **Python bindings via `ctypes`**. It enables zero-copy access to a central in-memory store across multiple processes without traditional socket or message-passing overhead.

---

## Motivation

Traditional key-value caches like Redis use networking and serialization even on local systems. MemStream bypasses this overhead by allowing all microservices to interact directly with shared memory. It’s designed to be fast, minimal, and extensible across C and Python environments.

---

## Architecture Overview

At the heart of MemStream lies a **shared memory segment** (`cache_t`) that acts as the central cache. All client processes (writers, readers, analytics) attach to this memory via a small C shared library (`libcache.so`) and interact with it through defined APIs. Python services access these APIs through `ctypes`, enabling native shared-memory access from Python with no socket, file, or RPC overhead.

---

## Key Components

### `libcache.so` (C Shared Library)
- Exposes `cache_connect`, `cache_put`, and `cache_get` to client processes.
- Built from `cache.c`, handles all memory and locking logic internally.

### `cache.c` / `cache.h`
- Implements the core shared-memory cache.
- Allocates a flat memory region storing both metadata (`entry_t[]`) and data blobs (`char data[]`).
- Uses `pthread_rwlock_t` for concurrent read-write access across processes.

### `writer.py`
- Uses `ctypes` to load `libcache.so` and insert key-value pairs.
- Supports arbitrary binary values.

### `reader.py`
- Queries keys from the shared cache using C library functions.

### `analytics.py`
- Scans the shared cache to log access statistics like usage, frequency, and timestamps.

---

## Inter-Process Communication (IPC)

MemStream uses **System V shared memory** (`shmget`, `shmat`) to allocate and attach to a single cache region in RAM. Each process maps this region into its virtual address space, resulting in direct access to the same physical memory. All services operate on the same `cache_t` instance in memory.

---

## Concurrency Model

All cache operations are synchronized using a **process-shared `pthread_rwlock_t`** embedded inside the shared memory. This allows:
- Multiple concurrent readers
- Exclusive writers
- Prevents race conditions and corruption even with overlapping access

---

## Shared Memory Design

Shared memory layout:

[ pthread_rwlock_t lock ]
[ size_t max_memory ]
[ size_t used_memory ]
[ cache_stats_t stats ]
[ entry_t entries[] ] <- Fixed metadata for each key
[ char data[] ] <- Flexible region for raw values


Each `entry_t` tracks:
- `key`, `value_size`
- `data_offset`: offset into `data[]`
- `last_access`, `created_at`, `access_count`
- `is_valid`: used/free marker

Values are manually stored at `cache->data + offset`. This enables flexible binary data storage but requires explicit memory management and fragmentation control.

---

## `ctypes` Integration

Python services use `ctypes` to bind to `libcache.so`:
- Dynamically loads and links C functions at runtime
- Passes keys, values, and lengths from Python directly into the C layer
- Enables fast cross-language memory access with minimal overhead

Example:

```python
from ctypes import *
lib = CDLL('./libcache.so')
lib.cache_connect()
lib.cache_put(b"key", b"value", len(b"value"))
```
---

## Example Flow
1. `writer.py` calls lib.cache_connect() → maps shared memory

2. Inserts key foo → value "bar" stored at offset 0

3. `reader.py` connects, retrieves value from same memory

4. `analytics.py` reports hit count and timestamps

---

## Summary

MemStream demonstrates a lightweight, multi-language key-value system with shared-memory-backed zero-copy access. It explores memory layout control, concurrency primitives, and Python-C interop without relying on external databases or IPC mechanisms.
---
