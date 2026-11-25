#include "desktop_ipc.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void p16(uint8_t*p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8u);}
static void p32(uint8_t*p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8u);p[2]=(uint8_t)(v>>16u);p[3]=(uint8_t)(v>>24u);}
static void p64(uint8_t*p,uint64_t v){p32(p,(uint32_t)v);p32(p+4u,(uint32_t)(v>>32u));}
static size_t frame(uint8_t*f,uint32_t type,uint64_t seq,uint64_t session,uint32_t obj,uint32_t gen,const uint8_t*payload,uint32_t n){
 (void)memset(f,0,DUCKOS_DESKTOP_IPC_HEADER_SIZE+n);(void)memcpy(f,"DIPC",4u);
 p16(f+4u,1u);p16(f+6u,0u);p16(f+8u,DUCKOS_DESKTOP_IPC_HEADER_SIZE);p32(f+12u,type);
 p32(f+16u,n);p64(f+20u,seq);p64(f+28u,session);p32(f+36u,obj);p32(f+40u,gen);
 if(n>0u&&payload!=NULL)(void)memcpy(f+48u,payload,n);
 return DUCKOS_DESKTOP_IPC_HEADER_SIZE+n;
}
static void test_decode(void){
 uint8_t f[72],data[24]={0};duckos_desktop_message m;
 size_t n=frame(f,DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW,4u,99u,12u,3u,data,24u);
 assert(duckos_desktop_message_decode(f,n,4u,99u,&m)==DUCKOS_DESKTOP_IPC_OK);
 assert(m.object_id==12u&&m.object_generation==3u&&m.payload==f+48u);
 assert(duckos_desktop_message_decode(f,n,5u,99u,&m)==DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE);
 assert(duckos_desktop_message_decode(f,n,4u,100u,&m)==DUCKOS_DESKTOP_IPC_SESSION_MISMATCH);
 f[0]='X';assert(duckos_desktop_message_decode(f,n,4u,99u,&m)==DUCKOS_DESKTOP_IPC_BAD_MAGIC);
 f[0]='D';p16(f+4u,2u);assert(duckos_desktop_message_decode(f,n,4u,99u,&m)==DUCKOS_DESKTOP_IPC_UNSUPPORTED_VERSION);
 p16(f+4u,1u);p32(f+16u,DUCKOS_DESKTOP_IPC_MAX_PAYLOAD+1u);
 assert(duckos_desktop_message_decode(f,n,4u,99u,&m)==DUCKOS_DESKTOP_IPC_INVALID_LENGTH);
 n=frame(f,DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW,1u,2u,0u,0u,data,24u);
 assert(duckos_desktop_message_decode(f,n,1u,2u,&m)==DUCKOS_DESKTOP_IPC_INVALID_OBJECT);
 n=frame(f,DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW,1u,2u,7u,1u,data,8u);
 assert(duckos_desktop_message_decode(f,n,1u,2u,&m)==DUCKOS_DESKTOP_IPC_INVALID_PAYLOAD);
}
static void test_hello(void){
 uint8_t f[64],data[16]={0};duckos_desktop_message m;
 size_t n=frame(f,DUCKOS_DESKTOP_MSG_HELLO,1u,0u,0u,0u,data,16u);
 assert(duckos_desktop_message_decode(f,n,1u,0u,&m)==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_message_decode(f,n,1u,9u,&m)==DUCKOS_DESKTOP_IPC_SESSION_MISMATCH);
}
static void test_event_queue(void){
 duckos_desktop_event_queue q;const uint8_t in[4]={1u,2u,3u,4u};uint8_t out[4]={0};
 size_t written=0u;uint64_t seq=0u;uint64_t i;
 duckos_desktop_event_queue_init(&q);
 assert(duckos_desktop_event_queue_pop(&q,out,sizeof(out),&written,&seq)==DUCKOS_DESKTOP_IPC_EMPTY);
 assert(duckos_desktop_event_queue_push(&q,1u,in,sizeof(in))==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_event_queue_push(&q,3u,in,sizeof(in))==DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE);
 assert(duckos_desktop_event_queue_pop(&q,out,2u,&written,&seq)==DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL);
 assert(q.count==1u);
 assert(duckos_desktop_event_queue_pop(&q,out,sizeof(out),&written,&seq)==DUCKOS_DESKTOP_IPC_OK);
 assert(written==sizeof(in)&&seq==1u&&memcmp(in,out,sizeof(in))==0);
 for(i=2u;i<2u+DUCKOS_DESKTOP_EVENT_CAPACITY;i++)
  assert(duckos_desktop_event_queue_push(&q,i,in,sizeof(in))==DUCKOS_DESKTOP_IPC_OK);
 assert(q.count==DUCKOS_DESKTOP_EVENT_CAPACITY);
 assert(duckos_desktop_event_queue_push(&q,2u+DUCKOS_DESKTOP_EVENT_CAPACITY,in,sizeof(in))==DUCKOS_DESKTOP_IPC_BACKPRESSURE);
 assert(q.count==DUCKOS_DESKTOP_EVENT_CAPACITY);
}
int main(void){test_decode();test_hello();test_event_queue();puts("DuckOS desktop IPC tests passed");return 0;}
