#ifndef DUCKOS_INITRAMFS_H
#define DUCKOS_INITRAMFS_H

#include <stdbool.h>
#include <stdint.h>

bool initramfs_validate(const void *archive, uint64_t archive_size,
                        uint64_t *entry_count);

#endif
