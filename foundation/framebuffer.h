#ifndef DUCKOS_FRAMEBUFFER_H
#define DUCKOS_FRAMEBUFFER_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define DUCKOS_FRAMEBUFFER_MAX_WIDTH 16384u
#define DUCKOS_FRAMEBUFFER_MAX_HEIGHT 16384u
#define DUCKOS_COMPOSITOR_MAX_SURFACES 32u
typedef enum { DUCKOS_SURFACE_RGBA8888=1, DUCKOS_SURFACE_BGRA8888=2 } duckos_surface_format;
typedef enum {
 DUCKOS_FRAMEBUFFER_OK=0, DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT=-1,
 DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY=-2, DUCKOS_FRAMEBUFFER_INVALID_FORMAT=-3,
 DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL=-4, DUCKOS_FRAMEBUFFER_INVALID_MASKS=-5,
 DUCKOS_FRAMEBUFFER_INVALID_SURFACE=-6, DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES=-7,
 DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE=-8
} duckos_framebuffer_status;
typedef struct {
 volatile uint8_t *pixels; size_t mapped_size; uint32_t width,height,pitch_bytes;
 uint8_t red_size,red_shift,green_size,green_shift,blue_size,blue_shift;
} duckos_framebuffer_target;
typedef struct {
 uint32_t id,generation; int32_t x,y; uint32_t width,height,pitch_bytes;
 size_t buffer_size; uint32_t z_index; uint8_t visible,format; const uint8_t *pixels;
} duckos_framebuffer_surface;
duckos_framebuffer_status duckos_framebuffer_validate_target(const duckos_framebuffer_target *);
duckos_framebuffer_status duckos_framebuffer_clear(duckos_framebuffer_target *,uint8_t,uint8_t,uint8_t);
duckos_framebuffer_status duckos_framebuffer_fill_rect(duckos_framebuffer_target *,int32_t,int32_t,uint32_t,uint32_t,uint8_t,uint8_t,uint8_t);
duckos_framebuffer_status duckos_framebuffer_surface_validate(const duckos_framebuffer_surface *);
duckos_framebuffer_status duckos_framebuffer_blit_surface(duckos_framebuffer_target *,const duckos_framebuffer_surface *);
duckos_framebuffer_status duckos_framebuffer_compose(duckos_framebuffer_target *,uint8_t,uint8_t,uint8_t,const duckos_framebuffer_surface *,size_t);
const char *duckos_framebuffer_status_name(duckos_framebuffer_status);
#ifdef __cplusplus
}
#endif
#endif
