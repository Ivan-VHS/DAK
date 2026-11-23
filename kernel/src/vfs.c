#include "duckos/kernel.h"

#include <string.h>

#define VFS_NODE_COUNT 32u
#define VFS_FD_COUNT 32u
#define VFS_FILE_CAPACITY 2048u
#define VFS_PATH_CAPACITY (DUCKOS_MAX_PATH_LENGTH + 1u)
#define VFS_MODE_READ 0u
#define VFS_MODE_WRITE 1u
#define VFS_MODE_APPEND 2u

typedef struct {
    char path[VFS_PATH_CAPACITY];
    uint8_t data[VFS_FILE_CAPACITY];
    uint32_t size;
    uint8_t used;
} DuckOsVfsNode;

typedef struct {
    DuckOsVfsNode *node;
    uint32_t position;
    uint8_t mode;
    uint8_t used;
} DuckOsVfsDescriptor;

static DuckOsVfsNode nodes[VFS_NODE_COUNT];
static DuckOsVfsDescriptor descriptors[VFS_FD_COUNT];
static uint8_t vfs_initialized;

static int valid_path(const char *path) {
    if (path == NULL || path[0] != '/') return 0;
    size_t length = 0u;
    while (length <= DUCKOS_MAX_PATH_LENGTH && path[length] != '\0') {
        if ((uint8_t)path[length] < 0x20u) return 0;
        length++;
    }
    if (length <= 1u || length > DUCKOS_MAX_PATH_LENGTH) return 0;

    size_t component_start = 1u;
    for (size_t i = 1u; i <= length; ++i) {
        if (i != length && path[i] != '/') continue;
        size_t component_length = i - component_start;
        if ((component_length == 1u && path[component_start] == '.') ||
            (component_length == 2u && path[component_start] == '.' &&
             path[component_start + 1u] == '.'))
            return 0;
        if (component_length == 0u && i != length) return 0;
        component_start = i + 1u;
    }
    return 1;
}

static DuckOsVfsNode *find_node(const char *path) {
    for (uint32_t i = 0u; i < VFS_NODE_COUNT; ++i)
        if (nodes[i].used && strcmp(nodes[i].path, path) == 0)
            return &nodes[i];
    return NULL;
}

static DuckOsVfsNode *create_node(const char *path) {
    DuckOsVfsNode *existing = find_node(path);
    if (existing != NULL) return existing;
    for (uint32_t i = 0u; i < VFS_NODE_COUNT; ++i) {
        if (nodes[i].used) continue;
        size_t length = strlen(path);
        if (length >= sizeof nodes[i].path) return NULL;
        nodes[i].used = 1u;
        nodes[i].size = 0u;
        memcpy(nodes[i].path, path, length + 1u);
        return &nodes[i];
    }
    return NULL;
}

static int allocate_descriptor(DuckOsVfsNode *node, uint8_t mode) {
    for (uint32_t i = 3u; i < VFS_FD_COUNT; ++i) {
        if (descriptors[i].used) continue;
        descriptors[i].node = node;
        descriptors[i].mode = mode;
        descriptors[i].position = mode == VFS_MODE_APPEND ? node->size : 0u;
        descriptors[i].used = 1u;
        return (int)i;
    }
    return -1;
}

void duckos_vfs_init(void) {
    memset(nodes, 0, sizeof nodes);
    memset(descriptors, 0, sizeof descriptors);
    (void)create_node("/");
    (void)create_node("/tmp");
    (void)create_node("/etc");
    DuckOsVfsNode *welcome = create_node("/init.txt");
    if (welcome != NULL) {
        static const char text[] = "DuckOS kernel is running.\n";
        memcpy(welcome->data, text, sizeof text - 1u);
        welcome->size = sizeof text - 1u;
    }
    vfs_initialized = 1u;
}

int64_t duckos_vfs_open(const char *path, uint32_t mode) {
    if (!vfs_initialized || !valid_path(path) || mode > VFS_MODE_APPEND)
        return -1;
    DuckOsVfsNode *node = find_node(path);
    if (node == NULL) {
        if (mode == VFS_MODE_READ) return -2;
        node = create_node(path);
    }
    if (node == NULL) return -3;
    if (mode == VFS_MODE_WRITE) node->size = 0u;
    int descriptor = allocate_descriptor(node, (uint8_t)mode);
    return descriptor < 0 ? -4 : descriptor;
}

int64_t duckos_vfs_read(int64_t descriptor, void *buffer, uint64_t capacity) {
    if (!vfs_initialized || descriptor < 0 || descriptor >= (int64_t)VFS_FD_COUNT ||
        (capacity != 0u && buffer == NULL))
        return -1;
    if (descriptor == 0) return 0;
    if (descriptor == 1 || descriptor == 2) return -2;
    DuckOsVfsDescriptor *fd = &descriptors[(uint32_t)descriptor];
    if (!fd->used || fd->mode != VFS_MODE_READ || fd->node == NULL)
        return -3;
    uint32_t remaining = fd->node->size - fd->position;
    uint64_t count = remaining < capacity ? remaining : capacity;
    if (count != 0u)
        memcpy(buffer, fd->node->data + fd->position, (size_t)count);
    fd->position += (uint32_t)count;
    return (int64_t)count;
}

int64_t duckos_vfs_write(int64_t descriptor, const void *buffer, uint64_t length) {
    if (!vfs_initialized || descriptor < 0 || descriptor >= (int64_t)VFS_FD_COUNT ||
        (length != 0u && buffer == NULL))
        return -1;
    if (descriptor == 1 || descriptor == 2) {
        const uint8_t *bytes = (const uint8_t *)buffer;
        for (uint64_t i = 0u; i < length; ++i) {
            char one[2] = {(char)bytes[i], '\0'};
            duckos_serial_write(one);
        }
        return (int64_t)length;
    }
    if (descriptor < 3) return -2;
    DuckOsVfsDescriptor *fd = &descriptors[(uint32_t)descriptor];
    if (!fd->used || (fd->mode != VFS_MODE_WRITE &&
                      fd->mode != VFS_MODE_APPEND) || fd->node == NULL)
        return -3;
    uint32_t position = fd->mode == VFS_MODE_APPEND ?
                        fd->node->size : fd->position;
    if (position > VFS_FILE_CAPACITY) return -4;
    uint64_t available = VFS_FILE_CAPACITY - position;
    uint64_t count = length < available ? length : available;
    if (count != 0u)
        memcpy(fd->node->data + position, buffer, (size_t)count);
    fd->position = position + (uint32_t)count;
    if (fd->position > fd->node->size) fd->node->size = fd->position;
    return count == 0u && length != 0u ? -5 : (int64_t)count;
}

int64_t duckos_vfs_close(int64_t descriptor) {
    if (descriptor < 3 || descriptor >= (int64_t)VFS_FD_COUNT)
        return -1;
    DuckOsVfsDescriptor *fd = &descriptors[(uint32_t)descriptor];
    if (!fd->used) return -2;
    memset(fd, 0, sizeof *fd);
    return 0;
}
