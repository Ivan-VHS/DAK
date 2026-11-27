#include "framebuffer_compositor.h"

#include <limits.h>

static uint32_t channel_mask(uint8_t width, uint8_t shift) {
    if (width == 0U || width > 8U || shift >= 32U ||
        (uint32_t)width + (uint32_t)shift > 32U) return 0U;
    return ((UINT32_C(1) << width) - UINT32_C(1)) << shift;
}

static int address_range_valid(const void *address, uint64_t bytes) {
    const uintptr_t start = (uintptr_t)address;
    return address != (const void *)0 &&
           bytes <= (uint64_t)(UINTPTR_MAX - start);
}

static int ranges_overlap(const void *left, uint64_t left_bytes,
                          const void *right, uint64_t right_bytes) {
    const uintptr_t left_start = (uintptr_t)left;
    const uintptr_t right_start = (uintptr_t)right;
    const uintptr_t left_end = left_start + (uintptr_t)left_bytes;
    const uintptr_t right_end = right_start + (uintptr_t)right_bytes;
    return left_start < right_end && right_start < left_end;
}

static int target_valid(const duckos_framebuffer_target *target) {
    uint32_t red, green, blue;
    uint64_t required_bytes;
    if (target == (const duckos_framebuffer_target *)0 ||
        target->pixels == (volatile uint32_t *)0 ||
        target->width == 0U || target->height == 0U ||
        target->width > UINT32_MAX / 4U ||
        target->pitch_bytes < target->width * 4U ||
        (target->pitch_bytes & 3U) != 0U ||
        ((uintptr_t)target->pixels & (uintptr_t)3U) != 0U) return 0;

    required_bytes = (uint64_t)target->pitch_bytes * (uint64_t)target->height;
    if (required_bytes > target->mapped_bytes ||
        !address_range_valid((const void *)target->pixels, target->mapped_bytes)) return 0;

    red = channel_mask(target->red_mask_size, target->red_mask_shift);
    green = channel_mask(target->green_mask_size, target->green_mask_shift);
    blue = channel_mask(target->blue_mask_size, target->blue_mask_shift);
    if (red == 0U || green == 0U || blue == 0U ||
        (red & green) != 0U || (red & blue) != 0U || (green & blue) != 0U) return 0;
    return 1;
}

static int surface_valid(const duckos_framebuffer_surface *surface) {
    uint64_t required_bytes;
    if (surface == (const duckos_framebuffer_surface *)0 ||
        surface->id == 0U || surface->pixels == (const uint32_t *)0 ||
        surface->width == 0U || surface->height == 0U ||
        surface->width > UINT32_MAX / 4U ||
        surface->pitch_bytes < surface->width * 4U ||
        (surface->pitch_bytes & 3U) != 0U ||
        ((uintptr_t)surface->pixels & (uintptr_t)3U) != 0U ||
        surface->visible > 1U) return 0;

    required_bytes = (uint64_t)surface->pitch_bytes * (uint64_t)surface->height;
    if (required_bytes > surface->buffer_bytes ||
        surface->buffer_bytes > DUCKOS_FRAMEBUFFER_MAX_SURFACE_BYTES ||
        !address_range_valid(surface->pixels, surface->buffer_bytes)) return 0;
    return 1;
}

static duckos_framebuffer_surface *find_surface(
    duckos_framebuffer_compositor *compositor, uint64_t surface_id) {
    uint32_t index;
    for (index = 0U; index < compositor->surface_capacity; ++index) {
        duckos_framebuffer_surface *surface = &compositor->surfaces[index];
        if (surface->active != 0U && surface->id == surface_id) return surface;
    }
    return (duckos_framebuffer_surface *)0;
}

static uint8_t unpack_channel(uint32_t pixel, uint8_t width, uint8_t shift) {
    const uint32_t mask = channel_mask(width, shift);
    const uint32_t maximum = (UINT32_C(1) << width) - UINT32_C(1);
    const uint32_t value = (pixel & mask) >> shift;
    return (uint8_t)((value * UINT32_C(255) + maximum / 2U) / maximum);
}

static uint32_t pack_channel(uint8_t value, uint8_t width, uint8_t shift) {
    const uint32_t maximum = (UINT32_C(1) << width) - UINT32_C(1);
    const uint32_t scaled = ((uint32_t)value * maximum + UINT32_C(127)) / UINT32_C(255);
    return scaled << shift;
}

static uint32_t pack_rgb(const duckos_framebuffer_target *target,
                         uint8_t red, uint8_t green, uint8_t blue) {
    return pack_channel(red, target->red_mask_size, target->red_mask_shift) |
           pack_channel(green, target->green_mask_size, target->green_mask_shift) |
           pack_channel(blue, target->blue_mask_size, target->blue_mask_shift);
}

static uint8_t blend_channel(uint8_t source, uint8_t destination, uint32_t alpha) {
    return (uint8_t)(((uint32_t)source * alpha +
        (uint32_t)destination * (UINT32_C(255) - alpha) + UINT32_C(127)) /
        UINT32_C(255));
}

static void clear_target(duckos_framebuffer_compositor *compositor) {
    const uint32_t background = compositor->background_argb;
    const uint32_t pixel = pack_rgb(&compositor->target,
        (uint8_t)(background >> 16U), (uint8_t)(background >> 8U),
        (uint8_t)background);
    uint32_t y;
    for (y = 0U; y < compositor->target.height; ++y) {
        volatile uint8_t *bytes = (volatile uint8_t *)compositor->target.pixels +
                                  (uint64_t)y * compositor->target.pitch_bytes;
        volatile uint32_t *row = (volatile uint32_t *)bytes;
        uint32_t x;
        for (x = 0U; x < compositor->target.width; ++x) row[x] = pixel;
    }
}

static void render_surface(const duckos_framebuffer_target *target,
                           const duckos_framebuffer_surface *surface) {
    const int64_t left = (int64_t)surface->x;
    const int64_t top = (int64_t)surface->y;
    const int64_t right = left + (int64_t)surface->width;
    const int64_t bottom = top + (int64_t)surface->height;
    const int64_t clip_left = left > 0 ? left : 0;
    const int64_t clip_top = top > 0 ? top : 0;
    const int64_t clip_right = right < (int64_t)target->width ? right : (int64_t)target->width;
    const int64_t clip_bottom = bottom < (int64_t)target->height ? bottom : (int64_t)target->height;
    int64_t dy;

    if (clip_left >= clip_right || clip_top >= clip_bottom) return;

    for (dy = clip_top; dy < clip_bottom; ++dy) {
        const uint32_t sy = (uint32_t)(dy - top);
        const uint8_t *source_bytes = (const uint8_t *)surface->pixels +
                                      (uint64_t)sy * surface->pitch_bytes;
        const uint32_t *source_row = (const uint32_t *)source_bytes;
        volatile uint8_t *dest_bytes = (volatile uint8_t *)target->pixels +
                                       (uint64_t)dy * target->pitch_bytes;
        volatile uint32_t *dest_row = (volatile uint32_t *)dest_bytes;
        int64_t dx;

        for (dx = clip_left; dx < clip_right; ++dx) {
            const uint32_t sx = (uint32_t)(dx - left);
            const uint32_t src = source_row[sx];
            const uint32_t source_alpha = src >> 24U;
            const uint32_t alpha = (source_alpha * (uint32_t)surface->opacity +
                                    UINT32_C(127)) / UINT32_C(255);
            const uint32_t index = (uint32_t)dx;
            if (alpha == 0U) continue;
            if (alpha >= UINT32_C(255)) {
                dest_row[index] = pack_rgb(target, (uint8_t)(src >> 16U),
                                           (uint8_t)(src >> 8U), (uint8_t)src);
            } else {
                const uint32_t dst = dest_row[index];
                dest_row[index] = pack_rgb(target,
                    blend_channel((uint8_t)(src >> 16U),
                        unpack_channel(dst, target->red_mask_size, target->red_mask_shift), alpha),
                    blend_channel((uint8_t)(src >> 8U),
                        unpack_channel(dst, target->green_mask_size, target->green_mask_shift), alpha),
                    blend_channel((uint8_t)src,
                        unpack_channel(dst, target->blue_mask_size, target->blue_mask_shift), alpha));
            }
        }
    }
}

duckos_framebuffer_status duckos_framebuffer_compositor_init(
    duckos_framebuffer_compositor *compositor,
    const duckos_framebuffer_target *target,
    duckos_framebuffer_surface *surfaces,
    uint32_t surface_capacity,
    uint32_t background_argb) {
    uint32_t i;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        surfaces == (duckos_framebuffer_surface *)0 || surface_capacity == 0U ||
        surface_capacity > DUCKOS_FRAMEBUFFER_MAX_SURFACES)
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    if (!target_valid(target)) return DUCKOS_FRAMEBUFFER_INVALID_TARGET;

    for (i = 0U; i < surface_capacity; ++i) {
        surfaces[i].id = 0U;
        surfaces[i].pixels = (const uint32_t *)0;
        surfaces[i].buffer_bytes = 0U;
        surfaces[i].width = 0U;
        surfaces[i].height = 0U;
        surfaces[i].pitch_bytes = 0U;
        surfaces[i].x = 0;
        surfaces[i].y = 0;
        surfaces[i].z = 0;
        surfaces[i].opacity = 0U;
        surfaces[i].visible = 0U;
        surfaces[i].active = 0U;
        surfaces[i].reserved = 0U;
    }
    compositor->target = *target;
    compositor->surfaces = surfaces;
    compositor->surface_capacity = surface_capacity;
    compositor->surface_count = 0U;
    compositor->frame_sequence = 0U;
    compositor->background_argb = background_argb;
    compositor->initialized = 1U;
    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_surface_add(
    duckos_framebuffer_compositor *compositor,
    const duckos_framebuffer_surface *surface) {
    uint32_t i;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        compositor->initialized == 0U || !surface_valid(surface))
        return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
    if (find_surface(compositor, surface->id) != (duckos_framebuffer_surface *)0)
        return DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE;
    if (ranges_overlap((const void *)compositor->target.pixels,
                       compositor->target.mapped_bytes,
                       surface->pixels, surface->buffer_bytes))
        return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
    if (compositor->surface_count >= compositor->surface_capacity)
        return DUCKOS_FRAMEBUFFER_SURFACE_LIMIT;

    for (i = 0U; i < compositor->surface_capacity; ++i) {
        if (compositor->surfaces[i].active == 0U) {
            compositor->surfaces[i] = *surface;
            compositor->surfaces[i].active = 1U;
            compositor->surfaces[i].reserved = 0U;
            compositor->surface_count += 1U;
            return DUCKOS_FRAMEBUFFER_OK;
        }
    }
    return DUCKOS_FRAMEBUFFER_SURFACE_LIMIT;
}

duckos_framebuffer_status duckos_framebuffer_surface_remove(
    duckos_framebuffer_compositor *compositor, uint64_t surface_id) {
    duckos_framebuffer_surface *surface;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        compositor->initialized == 0U || surface_id == 0U)
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    surface = find_surface(compositor, surface_id);
    if (surface == (duckos_framebuffer_surface *)0)
        return DUCKOS_FRAMEBUFFER_SURFACE_NOT_FOUND;
    surface->id = 0U;
    surface->pixels = (const uint32_t *)0;
    surface->buffer_bytes = 0U;
    surface->width = 0U;
    surface->height = 0U;
    surface->pitch_bytes = 0U;
    surface->x = 0; surface->y = 0; surface->z = 0;
    surface->opacity = 0U; surface->visible = 0U;
    surface->active = 0U; surface->reserved = 0U;
    if (compositor->surface_count > 0U) compositor->surface_count -= 1U;
    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_surface_set_state(
    duckos_framebuffer_compositor *compositor, uint64_t surface_id,
    int32_t x, int32_t y, int32_t z, uint8_t opacity, uint8_t visible) {
    duckos_framebuffer_surface *surface;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        compositor->initialized == 0U || surface_id == 0U || visible > 1U)
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    surface = find_surface(compositor, surface_id);
    if (surface == (duckos_framebuffer_surface *)0)
        return DUCKOS_FRAMEBUFFER_SURFACE_NOT_FOUND;
    surface->x = x; surface->y = y; surface->z = z;
    surface->opacity = opacity; surface->visible = visible;
    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_surface_configure(
    duckos_framebuffer_compositor *compositor, uint64_t surface_id,
    int32_t x, int32_t y, int32_t z, uint32_t width, uint32_t height,
    uint8_t opacity, uint8_t visible) {
    duckos_framebuffer_surface *surface;
    uint64_t required_bytes;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        compositor->initialized == 0U || surface_id == 0U ||
        width == 0U || height == 0U || width > UINT32_MAX / 4U || visible > 1U)
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    surface = find_surface(compositor, surface_id);
    if (surface == (duckos_framebuffer_surface *)0)
        return DUCKOS_FRAMEBUFFER_SURFACE_NOT_FOUND;
    if (surface->pitch_bytes < width * 4U)
        return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
    required_bytes = (uint64_t)surface->pitch_bytes * (uint64_t)height;
    if (required_bytes > surface->buffer_bytes)
        return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
    surface->x = x; surface->y = y; surface->z = z;
    surface->width = width; surface->height = height;
    surface->opacity = opacity; surface->visible = visible;
    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_compositor_present(
    duckos_framebuffer_compositor *compositor) {
    uint32_t order[DUCKOS_FRAMEBUFFER_MAX_SURFACES];
    uint32_t count = 0U, i;
    if (compositor == (duckos_framebuffer_compositor *)0 ||
        compositor->initialized == 0U) return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    if (compositor->frame_sequence == UINT64_MAX)
        return DUCKOS_FRAMEBUFFER_FRAME_SEQUENCE_EXHAUSTED;

    for (i = 0U; i < compositor->surface_capacity; ++i) {
        const duckos_framebuffer_surface *surface = &compositor->surfaces[i];
        if (surface->active != 0U && surface->visible != 0U) {
            uint32_t position = count;
            while (position > 0U) {
                const duckos_framebuffer_surface *prior =
                    &compositor->surfaces[order[position - 1U]];
                if (prior->z < surface->z ||
                    (prior->z == surface->z && prior->id <= surface->id)) break;
                order[position] = order[position - 1U];
                position -= 1U;
            }
            order[position] = i;
            count += 1U;
        }
    }
    clear_target(compositor);
    for (i = 0U; i < count; ++i)
        render_surface(&compositor->target, &compositor->surfaces[order[i]]);
    compositor->frame_sequence += 1U;
    return DUCKOS_FRAMEBUFFER_OK;
}

const char *duckos_framebuffer_status_name(duckos_framebuffer_status status) {
    switch (status) {
        case DUCKOS_FRAMEBUFFER_OK: return "ok";
        case DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT: return "invalid-argument";
        case DUCKOS_FRAMEBUFFER_INVALID_TARGET: return "invalid-target";
        case DUCKOS_FRAMEBUFFER_INVALID_SURFACE: return "invalid-surface";
        case DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE: return "duplicate-surface";
        case DUCKOS_FRAMEBUFFER_SURFACE_NOT_FOUND: return "surface-not-found";
        case DUCKOS_FRAMEBUFFER_SURFACE_LIMIT: return "surface-limit";
        case DUCKOS_FRAMEBUFFER_FRAME_SEQUENCE_EXHAUSTED: return "frame-sequence-exhausted";
    }
    return "unknown-status";
}
