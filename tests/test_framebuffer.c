#include "framebuffer.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define W 320u
#define H 200u
static uint32_t px(const uint8_t*p,uint32_t x,uint32_t y){uint32_t v;memcpy(&v,p+((size_t)y*W+x)*4u,4u);return v;}
static duckos_framebuffer_target target(uint8_t*p,size_t n){duckos_framebuffer_target t={p,n,W,H,W*4u,8u,16u,8u,8u,8u,0u};return t;}
static void test_bounds(void){
 uint8_t mem[W*H*4u];duckos_framebuffer_target t=target(mem,sizeof(mem));memset(mem,0,sizeof(mem));
 assert(duckos_framebuffer_validate_target(&t)==DUCKOS_FRAMEBUFFER_OK);
 assert(duckos_framebuffer_fill_rect(&t,-2,-2,4u,4u,255u,0u,0u)==DUCKOS_FRAMEBUFFER_OK);
 assert(px(mem,0u,0u)==0x00ff0000u&&px(mem,1u,1u)==0x00ff0000u&&px(mem,2u,2u)==0u);
 t.mapped_size=16u;assert(duckos_framebuffer_validate_target(&t)==DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL);
}
static void test_blend_z(void){
 uint8_t mem[W*H*4u],red[4]={255u,0u,0u,255u},blue[4]={0u,0u,255u,128u};
 duckos_framebuffer_target t=target(mem,sizeof(mem));
 duckos_framebuffer_surface s[2]={
  {1u,1u,10,10,1u,1u,4u,4u,4u,10u,1u,DUCKOS_SURFACE_RGBA8888,red},
  {2u,1u,10,10,1u,1u,4u,4u,4u,20u,1u,DUCKOS_SURFACE_RGBA8888,blue}
 };
 assert(duckos_framebuffer_compose(&t,0u,0u,0u,s,2u)==DUCKOS_FRAMEBUFFER_OK);
 {uint32_t v=px(mem,10u,10u);assert(((v>>16u)&255u)==127u&&((v>>8u)&255u)==0u&&(v&255u)==128u);}
 assert(duckos_framebuffer_compose(&t,0u,0u,0u,s,33u)==DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES);
 s[1].id=1u;assert(duckos_framebuffer_compose(&t,0u,0u,0u,s,2u)==DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE);
}
static void test_surface_bounds(void){
 uint8_t mem[W*H*4u],red[4]={255u,0u,0u,255u};duckos_framebuffer_target t=target(mem,sizeof(mem));
 duckos_framebuffer_surface s={1u,1u,-4,-4,1u,1u,4u,4u,4u,1u,1u,DUCKOS_SURFACE_RGBA8888,red};
 assert(duckos_framebuffer_clear(&t,0u,0u,0u)==DUCKOS_FRAMEBUFFER_OK);
 assert(duckos_framebuffer_blit_surface(&t,&s)==DUCKOS_FRAMEBUFFER_OK);
 assert(px(mem,0u,0u)==0u);
 s.buffer_size=1u;assert(duckos_framebuffer_surface_validate(&s)==DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL);
}
int main(void){test_bounds();test_blend_z();test_surface_bounds();puts("DuckOS framebuffer tests passed");return 0;}
