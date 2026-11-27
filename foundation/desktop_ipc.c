#include "desktop_ipc.h"
#include <string.h>
static uint16_t r16(const uint8_t *p){return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8u));}
static uint32_t r32(const uint8_t *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8u)|((uint32_t)p[2]<<16u)|((uint32_t)p[3]<<24u);}
static uint64_t r64(const uint8_t *p){return (uint64_t)r32(p)|((uint64_t)r32(p+4u)<<32u);}
static int known_type(uint32_t t){
 switch(t){
 case DUCKOS_DESKTOP_MSG_HELLO: case DUCKOS_DESKTOP_MSG_CREATE_WINDOW:
 case DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW: case DUCKOS_DESKTOP_MSG_CLOSE_WINDOW:
 case DUCKOS_DESKTOP_MSG_FOCUS_WINDOW: case DUCKOS_DESKTOP_MSG_CREATE_SURFACE:
 case DUCKOS_DESKTOP_MSG_COMMIT_SURFACE: case DUCKOS_DESKTOP_MSG_INPUT_EVENT:
 case DUCKOS_DESKTOP_MSG_SWITCH_WORKSPACE: case DUCKOS_DESKTOP_MSG_POST_NOTIFICATION:
 case DUCKOS_DESKTOP_MSG_SET_THEME: case DUCKOS_DESKTOP_MSG_ACK:
 case DUCKOS_DESKTOP_MSG_ERROR: return 1;
 default: return 0;
 }
}
static int needs_object(uint32_t t){
 return t==DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW ||
 t==DUCKOS_DESKTOP_MSG_CLOSE_WINDOW || t==DUCKOS_DESKTOP_MSG_FOCUS_WINDOW ||
 t==DUCKOS_DESKTOP_MSG_COMMIT_SURFACE || t==DUCKOS_DESKTOP_MSG_INPUT_EVENT;
}
static int payload_ok(uint32_t t,uint32_t n){
 switch(t){
 case DUCKOS_DESKTOP_MSG_HELLO:return n>=16u&&n<=64u;
 case DUCKOS_DESKTOP_MSG_CREATE_WINDOW:return n>=16u&&n<=512u;
 case DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW:return n==24u;
 case DUCKOS_DESKTOP_MSG_CLOSE_WINDOW:case DUCKOS_DESKTOP_MSG_FOCUS_WINDOW:return n==0u;
 case DUCKOS_DESKTOP_MSG_CREATE_SURFACE:return n==24u;
 case DUCKOS_DESKTOP_MSG_COMMIT_SURFACE:return n>=16u&&n<=4096u;
 case DUCKOS_DESKTOP_MSG_INPUT_EVENT:return n==32u;
 case DUCKOS_DESKTOP_MSG_SWITCH_WORKSPACE:return n==8u;
 case DUCKOS_DESKTOP_MSG_POST_NOTIFICATION:return n>=8u&&n<=4096u;
 case DUCKOS_DESKTOP_MSG_SET_THEME:return n==4u;
 case DUCKOS_DESKTOP_MSG_ACK:return n<=64u;
 case DUCKOS_DESKTOP_MSG_ERROR:return n>=4u&&n<=256u;
 default:return 0;
 }
}
duckos_desktop_ipc_status duckos_desktop_message_decode(
 const uint8_t *wire,size_t wire_size,uint64_t expected_sequence,
 uint64_t expected_session_id,duckos_desktop_message *m){
 uint32_t n,reserved;
 if(wire==NULL||m==NULL||expected_sequence==0u)return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 (void)memset(m,0,sizeof(*m));
 if(wire_size<DUCKOS_DESKTOP_IPC_HEADER_SIZE)return DUCKOS_DESKTOP_IPC_INVALID_LENGTH;
 if(memcmp(wire,"DIPC",4u)!=0)return DUCKOS_DESKTOP_IPC_BAD_MAGIC;
 m->major=r16(wire+4u);m->minor=r16(wire+6u);m->header_size=r16(wire+8u);m->flags=r16(wire+10u);
 m->type=r32(wire+12u);n=r32(wire+16u);m->payload_length=n;
 m->sequence=r64(wire+20u);m->session_id=r64(wire+28u);
 m->object_id=r32(wire+36u);m->object_generation=r32(wire+40u);reserved=r32(wire+44u);
 if(m->major!=1u||m->minor!=0u)return DUCKOS_DESKTOP_IPC_UNSUPPORTED_VERSION;
 if(m->header_size!=DUCKOS_DESKTOP_IPC_HEADER_SIZE||
    (m->flags&(uint16_t)~DUCKOS_DESKTOP_FLAG_KNOWN_MASK)!=0u||reserved!=0u)
    return DUCKOS_DESKTOP_IPC_INVALID_HEADER;
 if(n>DUCKOS_DESKTOP_IPC_MAX_PAYLOAD||
    wire_size!=(size_t)DUCKOS_DESKTOP_IPC_HEADER_SIZE+(size_t)n)
    return DUCKOS_DESKTOP_IPC_INVALID_LENGTH;
 if(!known_type(m->type))return DUCKOS_DESKTOP_IPC_UNKNOWN_MESSAGE;
 if(m->sequence!=expected_sequence)return DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE;
 if(m->type==DUCKOS_DESKTOP_MSG_HELLO){
   if(expected_session_id!=0u||m->session_id!=0u)return DUCKOS_DESKTOP_IPC_SESSION_MISMATCH;
 }else if(expected_session_id==0u||m->session_id!=expected_session_id){
   return DUCKOS_DESKTOP_IPC_SESSION_MISMATCH;
 }
 if(needs_object(m->type)){
   if(m->object_id==0u||m->object_generation==0u)return DUCKOS_DESKTOP_IPC_INVALID_OBJECT;
 }else if(m->object_id!=0u||m->object_generation!=0u){
   return DUCKOS_DESKTOP_IPC_INVALID_OBJECT;
 }
 if(!payload_ok(m->type,n))return DUCKOS_DESKTOP_IPC_INVALID_PAYLOAD;
 m->payload=wire+DUCKOS_DESKTOP_IPC_HEADER_SIZE;
 return DUCKOS_DESKTOP_IPC_OK;
}
const char *duckos_desktop_ipc_status_name(duckos_desktop_ipc_status s){
 switch(s){
 case DUCKOS_DESKTOP_IPC_OK:return "ok";case DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT:return "invalid-argument";
 case DUCKOS_DESKTOP_IPC_BAD_MAGIC:return "bad-magic";case DUCKOS_DESKTOP_IPC_UNSUPPORTED_VERSION:return "unsupported-version";
 case DUCKOS_DESKTOP_IPC_INVALID_HEADER:return "invalid-header";case DUCKOS_DESKTOP_IPC_INVALID_LENGTH:return "invalid-length";
 case DUCKOS_DESKTOP_IPC_UNKNOWN_MESSAGE:return "unknown-message";case DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE:return "invalid-sequence";
 case DUCKOS_DESKTOP_IPC_SESSION_MISMATCH:return "session-mismatch";case DUCKOS_DESKTOP_IPC_INVALID_OBJECT:return "invalid-object";
 case DUCKOS_DESKTOP_IPC_INVALID_PAYLOAD:return "invalid-payload";case DUCKOS_DESKTOP_IPC_BACKPRESSURE:return "backpressure";
 case DUCKOS_DESKTOP_IPC_EMPTY:return "empty";case DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL:return "buffer-too-small";
 }
 return "unknown";
}
void duckos_desktop_event_queue_init(duckos_desktop_event_queue *q){if(q!=NULL)(void)memset(q,0,sizeof(*q));}
duckos_desktop_ipc_status duckos_desktop_event_queue_push(
 duckos_desktop_event_queue *q,uint64_t seq,const uint8_t *bytes,size_t n){
 duckos_desktop_event *e;
 if(q==NULL||bytes==NULL||seq==0u||n==0u||n>DUCKOS_DESKTOP_EVENT_MAX_BYTES)
   return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 if(q->count>=DUCKOS_DESKTOP_EVENT_CAPACITY)return DUCKOS_DESKTOP_IPC_BACKPRESSURE;
 if(q->last_sequence==UINT64_MAX||seq!=q->last_sequence+1u)return DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE;
 e=&q->events[q->tail];e->sequence=seq;e->length=(uint32_t)n;(void)memcpy(e->bytes,bytes,n);
 q->tail=(q->tail+1u)%DUCKOS_DESKTOP_EVENT_CAPACITY;q->count++;q->last_sequence=seq;
 return DUCKOS_DESKTOP_IPC_OK;
}
duckos_desktop_ipc_status duckos_desktop_event_queue_pop(
 duckos_desktop_event_queue *q,uint8_t *dst,size_t cap,size_t *written,uint64_t *seq){
 const duckos_desktop_event *e;
 if(written==NULL||seq==NULL)return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 *written=0u;*seq=0u;
 if(q==NULL)return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 if(q->count==0u)return DUCKOS_DESKTOP_IPC_EMPTY;
 e=&q->events[q->head];
 if(dst==NULL||cap<e->length)return DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL;
 (void)memcpy(dst,e->bytes,e->length);*written=e->length;*seq=e->sequence;
 (void)memset(&q->events[q->head],0,sizeof(q->events[q->head]));
 q->head=(q->head+1u)%DUCKOS_DESKTOP_EVENT_CAPACITY;q->count--;
 return DUCKOS_DESKTOP_IPC_OK;
}
