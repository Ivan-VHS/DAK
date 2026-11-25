#include "framebuffer.h"

#include <limits.h>
#include <stdint.h>

static int channel_mask_valid(uint8_t size, uint8_t shift)
{
    return size > 0u && size <= 8u && shift < 32u &&
           (uint32_t)size + (uint32_t)shift <= 32u;
}

static uint32_t channel_mask(uint8_t size, uint8_t shift)
{
    const uint32_t bits = (UINT32_C(1) << size) - 1u;
    return bits << shift;
}

static uint32_t encode_channel(uint8_t value, uint8_t size, uint8_t shift)
{
    const uint32_t maximum = (UINT32_C(1) << size) - 1u;
    const uint32_t scaled = ((uint32_t)value * maximum + 127u) / 255u;

    return scaled << shift;
}

static uint8_t decode_channel(uint32_t pixel, uint8_t size, uint8_t shift)
{
    const uint32_t maximum = (UINT32_C(1) << size) - 1u;
    const uint32_t channel = (pixel >> shift) & maximum;
    const uint32_t scaled = (channel * 255u + maximum / 2u) / maximum;

    return (uint8_t)scaled;
}

static uint32_t encode_rgb(const duckos_framebuffer_target *target,
                           uint8_t red, uint8_t green, uint8_t blue)
{
    return encode_channel(red, target->red_size, target->red_shift) |
           encode_channel(green, target->green_size, target->green_shift) |
           encode_channel(blue, target->blue_size, target->blue_shift);
}

static int clip_rectangle(const duckos_framebuffer_target *target,
                          int32_t x, int32_t y, uint32_t width, uint32_t height,
                          uint32_t *left, uint32_t *top,
                          uint32_t *right, uint32_t *bottom)
{
    int64_t x0 = (int64_t)x;
    int64_t y0 = (int64_t)y;
    int64_t x1 = x0 + (int64_t)width;
    int64_t y1 = y0 + (int64_t)height;

    if (width == 0u || height == 0u ||
        x1 <= 0 || y1 <= 0 ||
        x0 >= (int64_t)target->width ||
        y0 >= (int64_t)target->height) {
        return 0;
    }

    if (x0 < 0) {
        x0 = 0;
    }
    if (y0 < 0) {
        y0 = 0;
    }
    if (x1 > (int64_t)target->width) {
        x1 = (int64_t)target->width;
    }
    if (y1 > (int64_t)target->height) {
        y1 = (int64_t)target->height;
    }

    *left = (uint32_t)x0;
    *top = (uint32_t)y0;
    *right = (uint32_t)x1;
    *bottom = (uint32_t)y1;
    return 1;
}

duckos_framebuffer_status duckos_framebuffer_validate_target(
    const duckos_framebuffer_target *target)
{
    size_t required_bytes;
    uint32_t red_mask;
    uint32_t green_mask;
    uint32_t blue_mask;

    if (target == NULL || target->pixels == NULL) {
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    }

    if (target->width < 320u ||
        target->width > DUCKOS_FRAMEBUFFER_MAX_WIDTH ||
        target->height < 200u ||
        target->height > DUCKOS_FRAMEBUFFER_MAX_HEIGHT) {
        return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
    }

    if ((target->pitch_bytes & 3u) != 0u ||
        ((uintptr_t)target->pixels & 3u) != 0u ||
        target->pitch_bytes < target->width * 4u ||
        (size_t)target->height > SIZE_MAX / (size_t)target->pitch_bytes) {
        return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
    }

    required_bytes = (size_t)target->pitch_bytes * (size_t)target->height;
    if (target->mapped_size < required_bytes ||
        (uintptr_t)target->pixels > UINTPTR_MAX - required_bytes) {
        return DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL;
    }

    if (!channel_mask_valid(target->red_size, target->red_shift) ||
        !channel_mask_valid(target->green_size, target->green_shift) ||
        !channel_mask_valid(target->blue_size, target->blue_shift)) {
        return DUCKOS_FRAMEBUFFER_INVALID_MASKS;
    }

    red_mask = channel_mask(target->red_size, target->red_shift);
    green_mask = channel_mask(target->green_size, target->green_shift);
    blue_mask = channel_mask(target->blue_size, target->blue_shift);

    if ((red_mask & green_mask) != 0u ||
        (red_mask & blue_mask) != 0u ||
        (green_mask & blue_mask) != 0u) {
        return DUCKOS_FRAMEBUFFER_INVALID_MASKS;
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_clear(
    duckos_framebuffer_target *target, uint8_t red, uint8_t green, uint8_t blue)
{
    duckos_framebuffer_status status;
    uint32_t color;
    uint32_t y;

    status = duckos_framebuffer_validate_target(target);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    color = encode_rgb(target, red, green, blue);
    for (y = 0u; y < target->height; ++y) {
        volatile uint32_t *row = (volatile uint32_t *)(void *)(
            target->pixels + (size_t)y * (size_t)target->pitch_bytes);
        uint32_t x;

        for (x = 0u; x < target->width; ++x) {
            row[x] = color;
        }
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_fill_rect(
    duckos_framebuffer_target *target, int32_t x, int32_t y,
    uint32_t width, uint32_t height,
    uint8_t red, uint8_t green, uint8_t blue)
{
    duckos_framebuffer_status status;
    uint32_t left;
    uint32_t top;
    uint32_t right;
    uint32_t bottom;
    uint32_t row_index;
    uint32_t color;

    status = duckos_framebuffer_validate_target(target);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    if (!clip_rectangle(target, x, y, width, height,
                        &left, &top, &right, &bottom)) {
        return DUCKOS_FRAMEBUFFER_OK;
    }

    color = encode_rgb(target, red, green, blue);
    for (row_index = top; row_index < bottom; ++row_index) {
        volatile uint32_t *row = (volatile uint32_t *)(void *)(
            target->pixels + (size_t)row_index * (size_t)target->pitch_bytes);
        uint32_t column;

        for (column = left; column < right; ++column) {
            row[column] = color;
        }
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_surface_validate(
    const duckos_framebuffer_surface *surface)
{
    size_t required_bytes;

    if (surface == NULL || surface->pixels == NULL) {
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    }

    if (surface->id == 0u || surface->generation == 0u ||
        surface->visible > 1u) {
        return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
    }

    if (surface->format != DUCKOS_SURFACE_RGBA8888 &&
        surface->format != DUCKOS_SURFACE_BGRA8888) {
        return DUCKOS_FRAMEBUFFER_INVALID_FORMAT;
    }

    if (surface->width == 0u || surface->height == 0u ||
        surface->width > DUCKOS_FRAMEBUFFER_MAX_WIDTH ||
        surface->height > DUCKOS_FRAMEBUFFER_MAX_HEIGHT ||
        surface->pitch_bytes < surface->width * 4u ||
        (size_t)surface->height > SIZE_MAX / (size_t)surface->pitch_bytes) {
        return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
    }

    required_bytes = (size_t)surface->pitch_bytes * (size_t)surface->height;
    if (surface->buffer_size < required_bytes ||
        (uintptr_t)surface->pixels > UINTPTR_MAX - required_bytes) {
        return DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL;
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

duckos_framebuffer_status duckos_framebuffer_blit_surface(
    duckos_framebuffer_target *target, const duckos_framebuffer_surface *surface)
{
    duckos_framebuffer_status status;
    uint32_t left;
    uint32_t top;
    uint32_t right;
    uint32_t bottom;
    uint32_t destination_y;

    status = duckos_framebuffer_validate_target(target);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    status = duckos_framebuffer_surface_validate(surface);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    if (surface->visible == 0u ||
        !clip_rectangle(target, surface->x, surface->y,
                        surface->width, surface->height,
                        &left, &top, &right, &bottom)) {
        return DUCKOS_FRAMEBUFFER_OK;
    }

    for (destination_y = top; destination_y < bottom; ++destination_y) {
        const uint32_t source_y = (uint32_t)(
            (int64_t)destination_y - (int64_t)surface->y);
        const uint8_t *source_row = surface->pixels +
            (size_t)source_y * (size_t)surface->pitch_bytes;
        volatile uint32_t *destination_row = (volatile uint32_t *)(void *)(
            target->pixels +
            (size_t)destination_y * (size_t)target->pitch_bytes);
        uint32_t destination_x;

        for (destination_x = left; destination_x < right; ++destination_x) {
            const uint32_t source_x = (uint32_t)(
                (int64_t)destination_x - (int64_t)surface->x);
            const uint8_t *source_pixel = source_row + (size_t)source_x * 4u;
            uint8_t source_red;
            uint8_t source_green = source_pixel[1];
            uint8_t source_blue;
            const uint8_t alpha = source_pixel[3];

            if (surface->format == DUCKOS_SURFACE_RGBA8888) {
                source_red = source_pixel[0];
                source_blue = source_pixel[2];
            } else {
                source_red = source_pixel[2];
                source_blue = source_pixel[0];
            }

            if (alpha == 0u) {
                continue;
            }

            if (alpha != 255u) {
                const uint32_t destination_pixel = destination_row[destination_x];
                const uint8_t destination_red = decode_channel(
                    destination_pixel, target->red_size, target->red_shift);
                const uint8_t destination_green = decode_channel(
                    destination_pixel, target->green_size, target->green_shift);
                const uint8_t destination_blue = decode_channel(
                    destination_pixel, target->blue_size, target->blue_shift);
                const uint32_t inverse_alpha = 255u - (uint32_t)alpha;

                source_red = (uint8_t)(
                    ((uint32_t)source_red * (uint32_t)alpha +
                     (uint32_t)destination_red * inverse_alpha + 127u) / 255u);
                source_green = (uint8_t)(
                    ((uint32_t)source_green * (uint32_t)alpha +
                     (uint32_t)destination_green * inverse_alpha + 127u) / 255u);
                source_blue = (uint8_t)(
                    ((uint32_t)source_blue * (uint32_t)alpha +
                     (uint32_t)destination_blue * inverse_alpha + 127u) / 255u);
            }

            destination_row[destination_x] = encode_rgb(
                target, source_red, source_green, source_blue);
        }
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

static int surface_precedes(const duckos_framebuffer_surface *surfaces,
                            uint32_t left, uint32_t right)
{
    if (surfaces[left].z_index != surfaces[right].z_index) {
        return surfaces[left].z_index < surfaces[right].z_index;
    }

    return surfaces[left].id < surfaces[right].id;
}

duckos_framebuffer_status duckos_framebuffer_compose(
    duckos_framebuffer_target *target, uint8_t red, uint8_t green, uint8_t blue,
    const duckos_framebuffer_surface *surfaces, size_t surface_count)
{
    uint32_t order[DUCKOS_COMPOSITOR_MAX_SURFACES];
    duckos_framebuffer_status status;
    size_t index;
    size_t other;

    status = duckos_framebuffer_validate_target(target);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    if (surface_count > DUCKOS_COMPOSITOR_MAX_SURFACES) {
        return DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES;
    }

    if (surface_count > 0u && surfaces == NULL) {
        return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
    }

    /* Validate everything before clearing the output, so rejection is atomic. */
    for (index = 0u; index < surface_count; ++index) {
        status = duckos_framebuffer_surface_validate(&surfaces[index]);
        if (status != DUCKOS_FRAMEBUFFER_OK) {
            return status;
        }

        order[index] = (uint32_t)index;
        for (other = 0u; other < index; ++other) {
            if (surfaces[other].id == surfaces[index].id) {
                return DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE;
            }
        }
    }

    /* Stable deterministic order: lower Z first, then lower surface ID. */
    for (index = 1u; index < surface_count; ++index) {
        const uint32_t selected = order[index];
        size_t position = index;

        while (position > 0u &&
               surface_precedes(surfaces, selected, order[position - 1u])) {
            order[position] = order[position - 1u];
            --position;
        }
        order[position] = selected;
    }

    status = duckos_framebuffer_clear(target, red, green, blue);
    if (status != DUCKOS_FRAMEBUFFER_OK) {
        return status;
    }

    for (index = 0u; index < surface_count; ++index) {
        status = duckos_framebuffer_blit_surface(
            target, &surfaces[order[index]]);
        if (status != DUCKOS_FRAMEBUFFER_OK) {
            return status;
        }
    }

    return DUCKOS_FRAMEBUFFER_OK;
}

const char *duckos_framebuffer_status_name(duckos_framebuffer_status status)
{
    switch (status) {
    case DUCKOS_FRAMEBUFFER_OK:
        return "ok";
    case DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT:
        return "invalid-argument";
    case DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY:
        return "invalid-geometry";
    case DUCKOS_FRAMEBUFFER_INVALID_FORMAT:
        return "invalid-format";
    case DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL:
        return "buffer-too-small";
    case DUCKOS_FRAMEBUFFER_INVALID_MASKS:
        return "invalid-masks";
    case DUCKOS_FRAMEBUFFER_INVALID_SURFACE:
        return "invalid-surface";
    case DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES:
        return "too-many-surfaces";
    case DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE:
        return "duplicate-surface";
    }

    return "unknown";
}
