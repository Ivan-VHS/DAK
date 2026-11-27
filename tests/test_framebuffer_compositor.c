#include "framebuffer_compositor.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#define WIDTH 8U
#define HEIGHT 8U
static uint32_t scanout[WIDTH * HEIGHT];
static duckos_framebuffer_surface surfaces[4];
static uint32_t red_pixels[4]={0xffff0000U,0xffff0000U,0xffff0000U,0xffff0000U};
static uint32_t green_pixel[1]={0x8000ff00U};
static duckos_framebuffer_target make_target(void) {
    duckos_framebuffer_target t={0};
    t.pixels=scanout;t.mapped_bytes=sizeof(scanout);t.width=WIDTH;t.height=HEIGHT;
    t.pitch_bytes=WIDTH*4U;t.red_mask_size=8U;t.red_mask_shift=16U;
    t.green_mask_size=8U;t.green_mask_shift=8U;t.blue_mask_size=8U;t.blue_mask_shift=0U;
    return t;
}
static void init(duckos_framebuffer_compositor *c) {
    const duckos_framebuffer_target t=make_target();
    assert(duckos_framebuffer_compositor_init(c,&t,surfaces,4U,0xff0000ffU)==DUCKOS_FRAMEBUFFER_OK);
}
static duckos_framebuffer_surface make_surface(uint64_t id,const uint32_t *pixels,
 uint32_t w,uint32_t h,uint32_t pitch,uint64_t bytes,int32_t x,int32_t y,
 int32_t z,uint8_t opacity,uint8_t visible) {
    duckos_framebuffer_surface s={0};
    s.id=id;s.pixels=pixels;s.width=w;s.height=h;s.pitch_bytes=pitch;s.buffer_bytes=bytes;
    s.x=x;s.y=y;s.z=z;s.opacity=opacity;s.visible=visible;return s;
}
static void test_target_validation(void) {
    duckos_framebuffer_compositor c;duckos_framebuffer_surface local[1];
    duckos_framebuffer_target t=make_target();
    assert(duckos_framebuffer_compositor_init(NULL,&t,local,1U,0U)==DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT);
    t.pitch_bytes=1U;
    assert(duckos_framebuffer_compositor_init(&c,&t,local,1U,0U)==DUCKOS_FRAMEBUFFER_INVALID_TARGET);
    t=make_target();t.mapped_bytes=4U;
    assert(duckos_framebuffer_compositor_init(&c,&t,local,1U,0U)==DUCKOS_FRAMEBUFFER_INVALID_TARGET);
    t=make_target();t.red_mask_shift=8U;
    assert(duckos_framebuffer_compositor_init(&c,&t,local,1U,0U)==DUCKOS_FRAMEBUFFER_INVALID_TARGET);
}
static void test_blend_order_and_clip(void) {
    duckos_framebuffer_compositor c;duckos_framebuffer_surface red,green;
    init(&c);
    red=make_surface(2U,red_pixels,2U,2U,8U,sizeof(red_pixels),-1,1,0,255U,1U);
    green=make_surface(1U,green_pixel,1U,1U,4U,sizeof(green_pixel),0,1,5,255U,1U);
    assert(duckos_framebuffer_surface_add(&c,&green)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_surface_add(&c,&red)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_compositor_present(&c)==DUCKOS_FRAMEBUFFER_OK);
    assert(scanout[1U*WIDTH+0U]==0x007f8000U);
    assert(scanout[1U*WIDTH+1U]==0x000000ffU);\n    assert(scanout[2U*WIDTH+0U]==0x00ff0000U);
    assert(scanout[0U]==0x000000ffU);
}
static void test_surface_bounds_and_state(void) {
    duckos_framebuffer_compositor c;duckos_framebuffer_surface s;
    init(&c);
    s=make_surface(7U,red_pixels,2U,2U,8U,sizeof(red_pixels),0,0,0,255U,1U);
    assert(duckos_framebuffer_surface_add(&c,&s)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_surface_configure(&c,7U,2,3,4,1U,2U,255U,1U)==DUCKOS_FRAMEBUFFER_OK);
    assert(surfaces[0].width==1U && surfaces[0].height==2U);
    assert(duckos_framebuffer_surface_configure(&c,7U,2,3,4,3U,2U,255U,1U)==DUCKOS_FRAMEBUFFER_INVALID_SURFACE);
    assert(duckos_framebuffer_surface_set_state(&c,7U,0,0,0,255U,0U)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_compositor_present(&c)==DUCKOS_FRAMEBUFFER_OK);
    assert(scanout[0U]==0x000000ffU);
}
static void test_alias_duplicate_capacity_and_remove(void) {
    duckos_framebuffer_compositor c,small;duckos_framebuffer_surface local[1],s;
    const duckos_framebuffer_target t=make_target();
    init(&c);
    s=make_surface(10U,scanout,2U,2U,8U,sizeof(scanout),0,0,0,255U,1U);
    assert(duckos_framebuffer_surface_add(&c,&s)==DUCKOS_FRAMEBUFFER_INVALID_SURFACE);
    s=make_surface(11U,red_pixels,2U,2U,8U,sizeof(red_pixels),0,0,0,255U,1U);
    assert(duckos_framebuffer_compositor_init(&small,&t,local,1U,0U)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_surface_add(&small,&s)==DUCKOS_FRAMEBUFFER_OK);
    assert(duckos_framebuffer_surface_add(&small,&s)==DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE);
    s.id=12U;assert(duckos_framebuffer_surface_add(&small,&s)==DUCKOS_FRAMEBUFFER_SURFACE_LIMIT);
    assert(duckos_framebuffer_surface_remove(&small,11U)==DUCKOS_FRAMEBUFFER_OK);
    assert(small.surface_count==0U);
}
int main(void) {
    test_target_validation();test_blend_order_and_clip();
    test_surface_bounds_and_state();test_alias_duplicate_capacity_and_remove();
    puts("DuckOS framebuffer compositor tests passed");return 0;
}
