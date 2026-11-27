#ifndef DUCKOS_FRAMEBUFFER_COMPOSITOR_H
#define DUCKOS_FRAMEBUFFER_COMPOSITOR_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_FRAMEBUFFER_MAX_SURFACES 16U
#define DUCKOS_FRAMEBUFFER_MAX_SURFACE_BYTES (16U * 1024U * 1024U)

typedef struct {
    volatile uint32_t *pixels;
    uint64_t mapped_bytes;
    uint32_t width;
    uint32_t height;
    uint32_t pitch_bytes;
    uint8_t red_mask_size;
    uint8_t red_mask_shift;
    uint8_t green_mask_size;
    uint8_t green_mask_shift;
    uint8_t blue_mask_size;
    uint8_t blue_mask_shift;
} duckos_framebuffer_target;

typedef struct {
    uint64_t id;
    const uint32_t *pixels;
    uint64_t buffer_bytes;
    uint32_t width;
    uint32_t height;
    uint32_t pitch_bytes;
    int32_t x;
    int32_t y;
    int32_t z;
    uint8_t opacity;
    uint8_t visible;
    uint8_t active;
    uint8_t reserved;
} duckos_framebuffer_surface;

typedef struct {
    duckos_framebuffer_target target;
    duckos_framebuffer_surface *surfaces;
    uint32_t surface_capacity;
    uint32_t surface_count;
    uint64_t frame_sequence;
    uint32_t background_argb;
    uint32_t initialized;
} duckos_framebuffer_compositor;

typedef enum {
    DUCKOS_FRAMEBUFFER_OK = 0,
    DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT = 1,
    DUCKOS_FRAMEBUFFER_INVALID_TARGET = 2,
    DUCKOS_FRAMEBUFFER_INVALID_SURFACE = 3,
    DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE = 4,
    DUCKOS_FRAMEBUFFER_SURFACE_NOT_FOUND = 5,
    DUCKOS_FRAMEBUFFER_SURFACE_LIMIT = 6,
    DUCKOS_FRAMEBUFFER_FRAME_SEQUENCE_EXHAUSTED = 7
} duckos_framebuffer_status;

/* Kernel-owned ARGB8888 surfaces are synchronously composed into a validated
   32-bpp linear RGB scanout target. The owning service serializes all calls. */
duckos_framebuffer_status duckos_framebuffer_compositor_init(
    duckos_framebuffer_compositor *compositor,
    const duckos_framebuffer_target *target,
    duckos_framebuffer_surface *surfaces,
    uint32_t surface_capacity,
    uint32_t background_argb
);
duckos_framebuffer_status duckos_framebuffer_surface_add(
    duckos_framebuffer_compositor *compositor,
    const duckos_framebuffer_surface *surface
);
duckos_framebuffer_status duckos_framebuffer_surface_remove(
    duckos_framebuffer_compositor *compositor,
    uint64_t surface_id
);
duckos_framebuffer_status duckos_framebuffer_surface_set_state(
    duckos_framebuffer_compositor *compositor,
    uint64_t surface_id,
    int32_t x,
    int32_t y,
    int32_t z,
    uint8_t opacity,
    uint8_t visible
);
duckos_framebuffer_status duckos_framebuffer_surface_configure(
    duckos_framebuffer_compositor *compositor,
    uint64_t surface_id,
    int32_t x,
    int32_t y,
    int32_t z,
    uint32_t width,
    uint32_t height,
    uint8_t opacity,
    uint8_t visible
);
duckos_framebuffer_status duckos_framebuffer_compositor_present(
    duckos_framebuffer_compositor *compositor
);
const char *duckos_framebuffer_status_name(duckos_framebuffer_status status);

#ifdef __cplusplus
}
#endif

#endif
