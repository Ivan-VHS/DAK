#include "desktop_ipc.h"
#include "reaper/dabi64_desktop.h"
#include "reaper/system.h"
#include <stdint.h>
#include <string.h>
_Static_assert(sizeof(ReaperDabi64DesktopRequestV1)==40U,"DABI64 request layout mismatch");
_Static_assert(DUCKOS_DESKTOP_IPC_MAX_FRAME_BYTES ==
 sizeof(ReaperDabi64DesktopRequestV1)+REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES,
 "DABI64 frame ceiling mismatch");
static int principal_valid(const duckos_desktop_ipc_principal *p) {
 return p!=NULL && p->task_id!=0U && p->generation!=0U;
}
static int principal_equal(const duckos_desktop_ipc_principal *a,const duckos_desktop_ipc_principal *b) {
 return a->task_id==b->task_id && a->generation==b->generation;
}
static int overlap(const uint8_t *a,uint32_t as,const uint8_t *b,uint32_t bs) {
 uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
 if ((uintptr_t)as>UINTPTR_MAX-x || (uintptr_t)bs>UINTPTR_MAX-y) return 1;
 return x<y+(uintptr_t)bs && y<x+(uintptr_t)as;
}
static duckos_desktop_ipc_status validate_slots(duckos_desktop_ipc_slot *s,uint32_t n) {
 uint32_t i,j;
 if(s==NULL || n==0U || n>DUCKOS_DESKTOP_IPC_MAX_QUEUE_SLOTS)
  return DUCKOS_DESKTOP_IPC_INVALID_CAPACITY;
 for(i=0U;i<n;i++) {
  if(s[i].storage==NULL || s[i].storage_capacity<sizeof(ReaperDabi64DesktopRequestV1) ||
     s[i].storage_capacity>DUCKOS_DESKTOP_IPC_MAX_FRAME_BYTES)
   return DUCKOS_DESKTOP_IPC_INVALID_CAPACITY;
  for(j=0U;j<i;j++) if(overlap(s[i].storage,s[i].storage_capacity,s[j].storage,s[j].storage_capacity))
   return DUCKOS_DESKTOP_IPC_INVALID_CAPACITY;
 }
 return DUCKOS_DESKTOP_IPC_OK;
}
static void init_queue(duckos_desktop_ipc_queue *q) {
 uint32_t i;
 for(i=0U;i<q->capacity;i++) {
  uint8_t *p=q->slots[i].storage; uint32_t n=q->slots[i].storage_capacity;
  memset(&q->slots[i],0,sizeof(q->slots[i]));
  q->slots[i].storage=p; q->slots[i].storage_capacity=n;
 }
 q->head=0U; q->tail=0U; q->count=0U;
}
static void clear_slot(duckos_desktop_ipc_slot *s) {
 uint8_t *p=s->storage; uint32_t n=s->storage_capacity;
 if(p!=NULL && s->frame_size>0U) memset(p,0,s->frame_size);
 memset(s,0,sizeof(*s)); s->storage=p; s->storage_capacity=n;
}
static void clear_queue(duckos_desktop_ipc_queue *q) {
 uint32_t i; for(i=0U;i<q->capacity;i++) clear_slot(&q->slots[i]);
 q->head=0U; q->tail=0U; q->count=0U;
}
static int side_of(const duckos_desktop_ipc_endpoint *e,const duckos_desktop_ipc_principal *p) {
 if(principal_equal(&e->owner,p)) return 0;
 if(principal_equal(&e->peer,p)) return 1;
 return -1;
}
duckos_desktop_ipc_status duckos_desktop_ipc_endpoint_init(
 duckos_desktop_ipc_endpoint *e,uint64_t id,duckos_desktop_ipc_principal owner,
 duckos_desktop_ipc_principal peer,duckos_desktop_ipc_slot *op,uint32_t on,
 duckos_desktop_ipc_slot *po,uint32_t pn) {
 uint32_t i,j; duckos_desktop_ipc_status st;
 if(e==NULL || id==0U || !principal_valid(&owner) || !principal_valid(&peer) ||
    principal_equal(&owner,&peer)) return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 st=validate_slots(op,on); if(st!=DUCKOS_DESKTOP_IPC_OK) return st;
 st=validate_slots(po,pn); if(st!=DUCKOS_DESKTOP_IPC_OK) return st;
 for(i=0U;i<on;i++) for(j=0U;j<pn;j++)
  if(overlap(op[i].storage,op[i].storage_capacity,po[j].storage,po[j].storage_capacity))
   return DUCKOS_DESKTOP_IPC_INVALID_CAPACITY;
 memset(e,0,sizeof(*e)); e->endpoint_id=id; e->owner=owner; e->peer=peer;
 e->outbound[0].slots=op; e->outbound[0].capacity=on;
 e->outbound[1].slots=po; e->outbound[1].capacity=pn;
 init_queue(&e->outbound[0]); init_queue(&e->outbound[1]);
 e->active=1U; return DUCKOS_DESKTOP_IPC_OK;
}
static duckos_desktop_ipc_status validate_frame(const void *frame,size_t size,
 ReaperDabi64DesktopRequestV1 *r) {
 ReaperDabi64DesktopStatus st;
 if(frame==NULL || r==NULL || size<sizeof(*r) || size>DUCKOS_DESKTOP_IPC_MAX_FRAME_BYTES)
  return DUCKOS_DESKTOP_IPC_MALFORMED_FRAME;
 memcpy(r,frame,sizeof(*r));
 if(r->operation<(uint16_t)REAPER_SYSTEM_WINDOW_CREATE ||
    r->operation>(uint16_t)REAPER_SYSTEM_SHELL_SETTINGS_QUERY)
  return DUCKOS_DESKTOP_IPC_NOT_DESKTOP_OPERATION;
 st=reaper_dabi64_desktop_request_validate(r,size);
 if(st==REAPER_DABI64_DESKTOP_STATUS_UNKNOWN_OPERATION) return DUCKOS_DESKTOP_IPC_UNKNOWN_OPERATION;
 if(st!=REAPER_DABI64_DESKTOP_STATUS_OK) return DUCKOS_DESKTOP_IPC_MALFORMED_FRAME;
 return DUCKOS_DESKTOP_IPC_OK;
}
duckos_desktop_ipc_status duckos_desktop_ipc_send(
 duckos_desktop_ipc_endpoint *e,const duckos_desktop_ipc_principal *caller,
 const void *frame,size_t size) {
 ReaperDabi64DesktopRequestV1 r; duckos_desktop_ipc_status st;
 duckos_desktop_ipc_queue *q; duckos_desktop_ipc_slot *s; int side;
 if(e==NULL || !principal_valid(caller)) return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 if(e->active==0U) return DUCKOS_DESKTOP_IPC_CLOSED;
 side=side_of(e,caller); if(side<0) return DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH;
 st=validate_frame(frame,size,&r); if(st!=DUCKOS_DESKTOP_IPC_OK) return st;
 if(e->last_sequence[(uint32_t)side]==UINT64_MAX) return DUCKOS_DESKTOP_IPC_SEQUENCE_EXHAUSTED;
 if(r.sequence!=e->last_sequence[(uint32_t)side]+UINT64_C(1)) return DUCKOS_DESKTOP_IPC_SEQUENCE_MISMATCH;
 q=&e->outbound[(uint32_t)side];
 if(q->count==q->capacity) return DUCKOS_DESKTOP_IPC_QUEUE_FULL;
 s=&q->slots[q->tail]; if(size>s->storage_capacity) return DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL;
 memcpy(s->storage,frame,size); s->frame_size=(uint32_t)size;
 s->sender_task_id=caller->task_id; s->sender_generation=caller->generation;
 s->receiver_task_id=side==0?e->peer.task_id:e->owner.task_id;
 s->receiver_generation=side==0?e->peer.generation:e->owner.generation;
 s->sequence=r.sequence; s->request_id=r.request_id; s->operation=r.operation;
 e->last_sequence[(uint32_t)side]=r.sequence;
 q->tail=(q->tail+1U)%q->capacity; q->count++;
 return DUCKOS_DESKTOP_IPC_OK;
}
duckos_desktop_ipc_status duckos_desktop_ipc_receive(
 duckos_desktop_ipc_endpoint *e,const duckos_desktop_ipc_principal *caller,
 void *frame,size_t cap,size_t *size,duckos_desktop_ipc_metadata *meta) {
 duckos_desktop_ipc_queue *q; duckos_desktop_ipc_slot *s; int side;
 if(size!=NULL) *size=0U;
 if(e==NULL || !principal_valid(caller) || size==NULL || meta==NULL)
  return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 if(e->active==0U) return DUCKOS_DESKTOP_IPC_CLOSED;
 side=side_of(e,caller); if(side<0) return DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH;
 q=&e->outbound[(uint32_t)(1-side)]; if(q->count==0U) return DUCKOS_DESKTOP_IPC_QUEUE_EMPTY;
 s=&q->slots[q->head];
 if(s->receiver_task_id!=caller->task_id || s->receiver_generation!=caller->generation)
  return DUCKOS_DESKTOP_IPC_INTERNAL_ERROR;
 *size=s->frame_size;
 if(frame==NULL || cap<s->frame_size) return DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL;
 memcpy(frame,s->storage,s->frame_size);
 meta->sender_task_id=s->sender_task_id; meta->sender_generation=s->sender_generation;
 meta->receiver_task_id=s->receiver_task_id; meta->receiver_generation=s->receiver_generation;
 meta->sequence=s->sequence; meta->request_id=s->request_id; meta->operation=s->operation;
 clear_slot(s); q->head=(q->head+1U)%q->capacity; q->count--;
 if(q->count==0U) q->tail=q->head;
 return DUCKOS_DESKTOP_IPC_OK;
}
duckos_desktop_ipc_status duckos_desktop_ipc_endpoint_close(
 duckos_desktop_ipc_endpoint *e,const duckos_desktop_ipc_principal *caller) {
 if(e==NULL || !principal_valid(caller)) return DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT;
 if(e->active==0U) return DUCKOS_DESKTOP_IPC_CLOSED;
 if(!principal_equal(&e->owner,caller)) return DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH;
 clear_queue(&e->outbound[0]); clear_queue(&e->outbound[1]); e->active=0U;
 return DUCKOS_DESKTOP_IPC_OK;
}
const char *duckos_desktop_ipc_status_name(duckos_desktop_ipc_status s) {
 switch(s) {
 case DUCKOS_DESKTOP_IPC_OK:return "ok";
 case DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT:return "invalid-argument";
 case DUCKOS_DESKTOP_IPC_INVALID_CAPACITY:return "invalid-capacity";
 case DUCKOS_DESKTOP_IPC_CLOSED:return "closed";
 case DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH:return "identity-mismatch";
 case DUCKOS_DESKTOP_IPC_QUEUE_FULL:return "queue-full";
 case DUCKOS_DESKTOP_IPC_QUEUE_EMPTY:return "queue-empty";
 case DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL:return "buffer-too-small";
 case DUCKOS_DESKTOP_IPC_MALFORMED_FRAME:return "malformed-frame";
 case DUCKOS_DESKTOP_IPC_UNKNOWN_OPERATION:return "unknown-operation";
 case DUCKOS_DESKTOP_IPC_NOT_DESKTOP_OPERATION:return "not-desktop-operation";
 case DUCKOS_DESKTOP_IPC_SEQUENCE_MISMATCH:return "sequence-mismatch";
 case DUCKOS_DESKTOP_IPC_SEQUENCE_EXHAUSTED:return "sequence-exhausted";
 case DUCKOS_DESKTOP_IPC_INTERNAL_ERROR:return "internal-error";
 }
 return "unknown-status";
}
