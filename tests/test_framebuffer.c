#include "framebuffer.h"

#ifdef NDEBUG
#undef NDEBUG
#endif

#include <assert.h>
#include <stdio.h>
#include <string.h>

#define TEST_WIDTH 320u
#define TEST_HEIGHT 200u

static uint32_t pixel_at(const uint8_t *pixels, uint32_t x, uint32_t y)
{
    uint32_t value;

    memcpy(&value, pixels + ((size_t)y * TEST_WIDTH + x) * 4u, sizeof(value));
    return value;
}

static duckos_framebuffer_target make_target(uint8_t *pixels, size_t size)
{
    duckos_framebuffer_target target = {
        .pixels = pixels,
        .mapped_size = size,
        .width = TEST_WIDTH,
        .height = TEST_HEIGHT,
        .pitch_bytes = TEST_WIDTH * 4u,
        .red_size = 8u,
        .red_shift = 16u,
        .green_size = 8u,
        .green_shift = 8u,
        .blue_size = 8u,
        .blue_shift = 0u
    };

    return target;
}

static void test_target_and_rectangle_bounds(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));

    memset(memory, 0, sizeof(memory));
    assert(duckos_framebuffer_validate_target(&target) == DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_fill_rect(
        &target, -2, -2, 4u, 4u, 255u, 0u, 0u) == DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 0u, 0u) == 0x00ff0000u);
    assert(pixel_at(memory, 1u, 1u) == 0x00ff0000u);
    assert(pixel_at(memory, 2u, 2u) == 0u);

    assert(duckos_framebuffer_fill_rect(
        &target, (int32_t)TEST_WIDTH, 0, 8u, 8u, 0u, 255u, 0u) ==
        DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 0u, 0u) == 0x00ff0000u);

    target.mapped_size = 16u;
    assert(duckos_framebuffer_validate_target(&target) ==
           DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL);

    target = make_target(memory, sizeof(memory));
    target.pitch_bytes -= 4u;
    assert(duckos_framebuffer_validate_target(&target) ==
           DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY);

    target = make_target(memory, sizeof(memory));
    target.green_shift = target.red_shift;
    assert(duckos_framebuffer_validate_target(&target) ==
           DUCKOS_FRAMEBUFFER_INVALID_MASKS);
}

static void test_alpha_blending_and_z_order(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    uint8_t red[4] = {255u, 0u, 0u, 255u};
    uint8_t half_blue[4] = {0u, 0u, 255u, 128u};
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));
    duckos_framebuffer_surface surfaces[2] = {
        {
            .id = 1u, .generation = 1u, .x = 10, .y = 10,
            .width = 1u, .height = 1u, .pitch_bytes = 4u,
            .buffer_size = sizeof(red), .z_index = 10u,
            .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888, .pixels = red
        },
        {
            .id = 2u, .generation = 1u, .x = 10, .y = 10,
            .width = 1u, .height = 1u, .pitch_bytes = 4u,
            .buffer_size = sizeof(half_blue), .z_index = 20u,
            .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888,
            .pixels = half_blue
        }
    };

    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, surfaces, 2u) == DUCKOS_FRAMEBUFFER_OK);

    {
        const uint32_t blended = pixel_at(memory, 10u, 10u);

        assert(((blended >> 16u) & 255u) == 127u);
        assert(((blended >> 8u) & 255u) == 0u);
        assert((blended & 255u) == 128u);
    }

    /* Equal Z values use surface ID as a deterministic tie-breaker. */
    surfaces[0].z_index = 5u;
    surfaces[1].z_index = 5u;
    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, surfaces, 2u) == DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 10u, 10u) == 0x007f0080u);
}

static void test_bgra_and_invisible_surfaces(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    uint8_t bgra_red[4] = {0u, 0u, 255u, 255u};
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));
    duckos_framebuffer_surface surface = {
        .id = 7u, .generation = 2u, .x = 20, .y = 30,
        .width = 1u, .height = 1u, .pitch_bytes = 4u,
        .buffer_size = sizeof(bgra_red), .z_index = 1u,
        .visible = 1u, .format = DUCKOS_SURFACE_BGRA8888, .pixels = bgra_red
    };

    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, &surface, 1u) == DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 20u, 30u) == 0x00ff0000u);

    surface.visible = 0u;
    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, &surface, 1u) == DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 20u, 30u) == 0u);
}

static void test_surface_validation_and_atomic_rejection(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    uint8_t red[4] = {255u, 0u, 0u, 255u};
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));
    duckos_framebuffer_surface surface = {
        .id = 1u, .generation = 1u, .x = -4, .y = -4,
        .width = 1u, .height = 1u, .pitch_bytes = 4u,
        .buffer_size = sizeof(red), .z_index = 1u,
        .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888, .pixels = red
    };

    memset(memory, 0x5au, sizeof(memory));
    assert(duckos_framebuffer_surface_validate(&surface) == DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_blit_surface(
        &target, &surface) == DUCKOS_FRAMEBUFFER_OK);
    assert(pixel_at(memory, 0u, 0u) == 0x5a5a5a5au);

    surface.format = 99u;
    assert(duckos_framebuffer_surface_validate(&surface) ==
           DUCKOS_FRAMEBUFFER_INVALID_FORMAT);
    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, &surface, 1u) ==
        DUCKOS_FRAMEBUFFER_INVALID_FORMAT);
    assert(pixel_at(memory, 0u, 0u) == 0x5a5a5a5au);

    surface.format = DUCKOS_SURFACE_RGBA8888;
    surface.id = 0u;
    assert(duckos_framebuffer_surface_validate(&surface) ==
           DUCKOS_FRAMEBUFFER_INVALID_SURFACE);

    surface.id = 1u;
    surface.buffer_size = 1u;
    assert(duckos_framebuffer_surface_validate(&surface) ==
           DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL);

    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, &surface, 33u) ==
        DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES);
}

static void test_duplicate_surfaces_are_rejected_before_drawing(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    uint8_t red[4] = {255u, 0u, 0u, 255u};
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));
    duckos_framebuffer_surface surfaces[2] = {
        {
            .id = 1u, .generation = 1u, .x = 0, .y = 0,
            .width = 1u, .height = 1u, .pitch_bytes = 4u,
            .buffer_size = sizeof(red), .z_index = 0u,
            .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888, .pixels = red
        },
        {
            .id = 1u, .generation = 2u, .x = 1, .y = 1,
            .width = 1u, .height = 1u, .pitch_bytes = 4u,
            .buffer_size = sizeof(red), .z_index = 1u,
            .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888, .pixels = red
        }
    };

    memset(memory, 0x33, sizeof(memory));
    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, surfaces, 2u) ==
        DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE);
    assert(pixel_at(memory, 0u, 0u) == 0x33333333u);
}

static void test_aliasing_is_rejected_before_drawing(void)
{
    uint8_t memory[TEST_WIDTH * TEST_HEIGHT * 4u];
    duckos_framebuffer_target target = make_target(memory, sizeof(memory));
    duckos_framebuffer_surface surface = {
        .id = 4u, .generation = 1u, .x = 0, .y = 0,
        .width = 1u, .height = 1u, .pitch_bytes = 4u,
        .buffer_size = 4u, .z_index = 1u,
        .visible = 1u, .format = DUCKOS_SURFACE_RGBA8888,
        .pixels = memory
    };

    memset(memory, 0x7cu, sizeof(memory));
    assert(duckos_framebuffer_compose(
        &target, 0u, 0u, 0u, &surface, 1u) ==
        DUCKOS_FRAMEBUFFER_OVERLAPPING_BUFFERS);
    assert(pixel_at(memory, 0u, 0u) == 0x7c7c7c7cu);
    assert(duckos_framebuffer_blit_surface(
        &target, &surface) == DUCKOS_FRAMEBUFFER_OVERLAPPING_BUFFERS);
    assert(pixel_at(memory, 0u, 0u) == 0x7c7c7c7cu);
}

int main(void)
{
    test_target_and_rectangle_bounds();
    test_alpha_blending_and_z_order();
    test_bgra_and_invisible_surfaces();
    test_surface_validation_and_atomic_rejection();
    test_duplicate_surfaces_are_rejected_before_drawing();
    test_aliasing_is_rejected_before_drawing();
    puts("DuckOS framebuffer tests passed");
    return 0;
}
