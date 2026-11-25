#include "framebuffer.h"
#include <string.h>
static int mask_ok(uint8_t n,uint8_t shift){return n>0u&&n<=8u&&shift<32u&&(uint32_t)n+(uint32_t)shift<=32u;}
static uint32_t mask(uint8_t n,uint8_t s){return ((UINT32_C(1)<<n)-1u)<<s;}
static uint32_t pack(uint8_t v,uint8_t n,uint8_t s){uint32_t m=(UINT32_C(1)<<n)-1u;return (((uint32_t)v*m+127u)/255u)<<s;}
static uint8_t unpack(uint32_t p,uint8_t n,uint8_t s){uint32_t m=(UINT32_C(1)<<n)-1u;return (uint8_t)((((p>>s)&m)*255u+m/2u)/m);}
static uint32_t rgb(const duckos_framebuffer_target*t,uint8_t r,uint8_t g,uint8_t b){
 return pack(r,t->red_size,t->red_shift)|pack(g,t->green_size,t->green_shift)|pack(b,t->blue_size,t->blue_shift);
}
static int clip(const duckos_framebuffer_target*t,int32_t x,int32_t y,uint32_t w,uint32_t h,
 uint32_t*l,uint32_t*top,uint32_t*r,uint32_t*bottom){
 int64_t x0=x,y0=y,x1=x0+(int64_t)w,y1=y0+(int64_t)h;
 if(w==0u||h==0u||x1<=0||y1<=0||x0>=(int64_t)t->width||y0>=(int64_t)t->height)return 0;
 if(x0<0)x0=0;if(y0<0)y0=0;if(x1>(int64_t)t->width)x1=t->width;if(y1>(int64_t)t->height)y1=t->height;
 *l=(uint32_t)x0;*top=(uint32_t)y0;*r=(uint32_t)x1;*bottom=(uint32_t)y1;return 1;
}
duckos_framebuffer_status duckos_framebuffer_validate_target(const duckos_framebuffer_target*t){
 size_t need;uint32_t rm,gm,bm;
 if(t==NULL||t->pixels==NULL)return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
 if(t->width<320u||t->width>DUCKOS_FRAMEBUFFER_MAX_WIDTH||t->height<200u||t->height>DUCKOS_FRAMEBUFFER_MAX_HEIGHT)
  return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
 if((t->pitch_bytes&3u)!=0u||((uintptr_t)t->pixels&3u)!=0u||
    t->pitch_bytes<t->width*4u||(size_t)t->height>SIZE_MAX/(size_t)t->pitch_bytes)
  return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
 need=(size_t)t->pitch_bytes*t->height;
 if(t->mapped_size<need||(uintptr_t)t->pixels>UINTPTR_MAX-need)return DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL;
 if(!mask_ok(t->red_size,t->red_shift)||!mask_ok(t->green_size,t->green_shift)||!mask_ok(t->blue_size,t->blue_shift))
  return DUCKOS_FRAMEBUFFER_INVALID_MASKS;
 rm=mask(t->red_size,t->red_shift);gm=mask(t->green_size,t->green_shift);bm=mask(t->blue_size,t->blue_shift);
 if((rm&gm)||(rm&bm)||(gm&bm))return DUCKOS_FRAMEBUFFER_INVALID_MASKS;
 return DUCKOS_FRAMEBUFFER_OK;
}
duckos_framebuffer_status duckos_framebuffer_clear(duckos_framebuffer_target*t,uint8_t r,uint8_t g,uint8_t b){
 uint32_t y,x,color;duckos_framebuffer_status s=duckos_framebuffer_validate_target(t);if(s!=DUCKOS_FRAMEBUFFER_OK)return s;
 color=rgb(t,r,g,b);
 for(y=0u;y<t->height;y++){volatile uint32_t*row=(volatile uint32_t*)(void*)(t->pixels+(size_t)y*t->pitch_bytes);for(x=0u;x<t->width;x++)row[x]=color;}
 return DUCKOS_FRAMEBUFFER_OK;
}
duckos_framebuffer_status duckos_framebuffer_fill_rect(duckos_framebuffer_target*t,int32_t x,int32_t y,uint32_t w,uint32_t h,uint8_t r,uint8_t g,uint8_t b){
 uint32_t l,tp,rt,bt,row_index,color;duckos_framebuffer_status s=duckos_framebuffer_validate_target(t);if(s!=DUCKOS_FRAMEBUFFER_OK)return s;
 if(!clip(t,x,y,w,h,&l,&tp,&rt,&bt))return DUCKOS_FRAMEBUFFER_OK;color=rgb(t,r,g,b);
 for(row_index=tp;row_index<bt;row_index++){volatile uint32_t*row=(volatile uint32_t*)(void*)(t->pixels+(size_t)row_index*t->pitch_bytes);uint32_t col;for(col=l;col<rt;col++)row[col]=color;}
 return DUCKOS_FRAMEBUFFER_OK;
}
duckos_framebuffer_status duckos_framebuffer_surface_validate(const duckos_framebuffer_surface*s){
 size_t need;
 if(s==NULL||s->pixels==NULL)return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
 if(s->id==0u||s->generation==0u||s->visible>1u||
    (s->format!=DUCKOS_SURFACE_RGBA8888&&s->format!=DUCKOS_SURFACE_BGRA8888))
  return DUCKOS_FRAMEBUFFER_INVALID_SURFACE;
 if(s->width==0u||s->height==0u||s->width>DUCKOS_FRAMEBUFFER_MAX_WIDTH||s->height>DUCKOS_FRAMEBUFFER_MAX_HEIGHT||
    s->pitch_bytes<s->width*4u||(size_t)s->height>SIZE_MAX/(size_t)s->pitch_bytes)
  return DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY;
 need=(size_t)s->pitch_bytes*s->height;
 if(s->buffer_size<need||(uintptr_t)s->pixels>UINTPTR_MAX-need)return DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL;
 return DUCKOS_FRAMEBUFFER_OK;
}
duckos_framebuffer_status duckos_framebuffer_blit_surface(duckos_framebuffer_target*t,const duckos_framebuffer_surface*s){
 uint32_t l,tp,rt,bt,y;duckos_framebuffer_status st=duckos_framebuffer_validate_target(t);
 if(st!=DUCKOS_FRAMEBUFFER_OK)return st;st=duckos_framebuffer_surface_validate(s);if(st!=DUCKOS_FRAMEBUFFER_OK)return st;
 if(!s->visible||!clip(t,s->x,s->y,s->width,s->height,&l,&tp,&rt,&bt))return DUCKOS_FRAMEBUFFER_OK;
 for(y=tp;y<bt;y++){
  uint32_t sy=(uint32_t)((int64_t)y-s->y);const uint8_t*src=s->pixels+(size_t)sy*s->pitch_bytes;
  volatile uint32_t*dst=(volatile uint32_t*)(void*)(t->pixels+(size_t)y*t->pitch_bytes);uint32_t x;
  for(x=l;x<rt;x++){
   uint32_t sx=(uint32_t)((int64_t)x-s->x);const uint8_t*p=src+(size_t)sx*4u;
   uint8_t r=s->format==DUCKOS_SURFACE_RGBA8888?p[0]:p[2],g=p[1];
   uint8_t b=s->format==DUCKOS_SURFACE_RGBA8888?p[2]:p[0],a=p[3];
   if(a==0u)continue;
   if(a!=255u){
    uint32_t d=dst[x];uint8_t dr=unpack(d,t->red_size,t->red_shift);
    uint8_t dg=unpack(d,t->green_size,t->green_shift);uint8_t db=unpack(d,t->blue_size,t->blue_shift);
    r=(uint8_t)(((uint32_t)r*a+(uint32_t)dr*(255u-a)+127u)/255u);
    g=(uint8_t)(((uint32_t)g*a+(uint32_t)dg*(255u-a)+127u)/255u);
    b=(uint8_t)(((uint32_t)b*a+(uint32_t)db*(255u-a)+127u)/255u);
   }
   dst[x]=rgb(t,r,g,b);
  }
 }
 return DUCKOS_FRAMEBUFFER_OK;
}
static int before(const duckos_framebuffer_surface*s,uint32_t a,uint32_t b){
 if(s[a].z_index!=s[b].z_index)return s[a].z_index<s[b].z_index;return s[a].id<s[b].id;
}
duckos_framebuffer_status duckos_framebuffer_compose(duckos_framebuffer_target*t,uint8_t r,uint8_t g,uint8_t b,const duckos_framebuffer_surface*s,size_t n){
 uint32_t order[DUCKOS_COMPOSITOR_MAX_SURFACES];size_t i,j;duckos_framebuffer_status st=duckos_framebuffer_validate_target(t);
 if(st!=DUCKOS_FRAMEBUFFER_OK)return st;
 if(n>DUCKOS_COMPOSITOR_MAX_SURFACES)return DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES;
 if(n>0u&&s==NULL)return DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT;
 for(i=0u;i<n;i++){
  st=duckos_framebuffer_surface_validate(&s[i]);if(st!=DUCKOS_FRAMEBUFFER_OK)return st;order[i]=(uint32_t)i;
  for(j=0u;j<i;j++)if(s[j].id==s[i].id)return DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE;
 }
 for(i=1u;i<n;i++){uint32_t v=order[i];j=i;while(j>0u&&before(s,v,order[j-1u])){order[j]=order[j-1u];--j;}order[j]=v;}
 st=duckos_framebuffer_clear(t,r,g,b);if(st!=DUCKOS_FRAMEBUFFER_OK)return st;
 for(i=0u;i<n;i++){st=duckos_framebuffer_blit_surface(t,&s[order[i]]);if(st!=DUCKOS_FRAMEBUFFER_OK)return st;}
 return DUCKOS_FRAMEBUFFER_OK;
}
const char*duckos_framebuffer_status_name(duckos_framebuffer_status s){
 switch(s){
 case DUCKOS_FRAMEBUFFER_OK:return "ok";case DUCKOS_FRAMEBUFFER_INVALID_ARGUMENT:return "invalid-argument";
 case DUCKOS_FRAMEBUFFER_INVALID_GEOMETRY:return "invalid-geometry";case DUCKOS_FRAMEBUFFER_INVALID_FORMAT:return "invalid-format";
 case DUCKOS_FRAMEBUFFER_BUFFER_TOO_SMALL:return "buffer-too-small";case DUCKOS_FRAMEBUFFER_INVALID_MASKS:return "invalid-masks";
 case DUCKOS_FRAMEBUFFER_INVALID_SURFACE:return "invalid-surface";case DUCKOS_FRAMEBUFFER_TOO_MANY_SURFACES:return "too-many-surfaces";
 case DUCKOS_FRAMEBUFFER_DUPLICATE_SURFACE:return "duplicate-surface";
 }return "unknown";
}
