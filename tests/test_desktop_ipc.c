#include "desktop_ipc.h"
#include "reaper/dabi64_desktop.h"
#include "reaper/system.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define CAP DUCKOS_DESKTOP_IPC_MAX_FRAME_BYTES
#define N 2U
static uint8_t a_mem[N][CAP], b_mem[N][CAP];
static duckos_desktop_ipc_slot a_slots[N]={
 {a_mem[0],CAP,0U,0U,0U,0U,0U,0U,0U,0U,0U},
 {a_mem[1],CAP,0U,0U,0U,0U,0U,0U,0U,0U,0U}
};
static duckos_desktop_ipc_slot b_slots[N]={
 {b_mem[0],CAP,0U,0U,0U,0U,0U,0U,0U,0U,0U},
 {b_mem[1],CAP,0U,0U,0U,0U,0U,0U,0U,0U,0U}
};
static const duckos_desktop_ipc_principal owner={11U,3U}, peer={22U,8U}, outsider={33U,1U};
static void init(duckos_desktop_ipc_endpoint *e) {
 memset(a_mem,0,sizeof(a_mem)); memset(b_mem,0,sizeof(b_mem));
 assert(duckos_desktop_ipc_endpoint_init(e,77U,owner,peer,a_slots,N,b_slots,N)==DUCKOS_DESKTOP_IPC_OK);
}
static size_t request(uint8_t *out,size_t cap,uint16_t op,uint64_t seq,uint64_t id,const char *p) {
 ReaperDabi64DesktopRequestV1 r={0}; size_t n=strlen(p), total=sizeof(r)+n;
 assert(total<=cap); r.struct_size=(uint32_t)sizeof(r); r.abi_version=1U;
 r.operation=op; r.payload_size=(uint32_t)n; r.request_id=id; r.sequence=seq;
 memcpy(out,&r,sizeof(r)); memcpy(out+sizeof(r),p,n); return total;
}
static void test_delivery(void) {
 duckos_desktop_ipc_endpoint e; uint8_t frame[CAP],out[CAP];
 size_t n,m=0U; duckos_desktop_ipc_metadata meta; ReaperDabi64DesktopRequestV1 h;
 init(&e); n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_CREATE,1U,500U,"window");
 assert(duckos_desktop_ipc_send(&e,&outsider,frame,n)==DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH);
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,4U,&m,&meta)==DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL && m==n);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_OK);
 assert(meta.sender_task_id==owner.task_id && meta.receiver_task_id==peer.task_id && meta.sequence==1U && meta.request_id==500U);
 memcpy(&h,out,sizeof(h)); assert(reaper_dabi64_desktop_request_validate(&h,m)==REAPER_DABI64_DESKTOP_STATUS_OK);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_INPUT_NEXT_EVENT,1U,501U,"event");
 assert(duckos_desktop_ipc_send(&e,&peer,frame,n)==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_ipc_receive(&e,&owner,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_OK);
 assert(meta.sender_task_id==peer.task_id && meta.receiver_task_id==owner.task_id);
}
static void test_backpressure_and_sequence(void) {
 duckos_desktop_ipc_endpoint e; uint8_t frame[CAP],out[CAP]; size_t n,m;
 duckos_desktop_ipc_metadata meta; init(&e);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_CREATE,1U,1U,"1");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_OK);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_SET_STATE,2U,2U,"2");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_OK);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_FOCUS,3U,3U,"3");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_QUEUE_FULL);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_OK && meta.sequence==1U);
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_OK && meta.sequence==2U);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_OK && meta.sequence==3U);
 assert(duckos_desktop_ipc_receive(&e,&peer,out,sizeof(out),&m,&meta)==DUCKOS_DESKTOP_IPC_QUEUE_EMPTY);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_QUERY,3U,4U,"replay");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_SEQUENCE_MISMATCH);
}
static void test_rejection_and_close(void) {
 duckos_desktop_ipc_endpoint e; uint8_t frame[CAP]; size_t n;
 init(&e); n=request(frame,sizeof(frame),REAPER_SYSTEM_PROCESS_SPAWN,1U,1U,"not-desktop");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_NOT_DESKTOP_OPERATION);
 n=request(frame,sizeof(frame),0x8007U,1U,2U,"unknown");
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_UNKNOWN_OPERATION);
 n=request(frame,sizeof(frame),REAPER_SYSTEM_WINDOW_CREATE,1U,3U,"bad");
 ((ReaperDabi64DesktopRequestV1 *)frame)->flags=1U;
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_MALFORMED_FRAME);
 assert(duckos_desktop_ipc_endpoint_close(&e,&peer)==DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH);
 assert(duckos_desktop_ipc_endpoint_close(&e,&owner)==DUCKOS_DESKTOP_IPC_OK);
 assert(duckos_desktop_ipc_send(&e,&owner,frame,n)==DUCKOS_DESKTOP_IPC_CLOSED);
}
int main(void) {
 test_delivery(); test_backpressure_and_sequence(); test_rejection_and_close();
 puts("DuckOS DABI64 IPC foundation tests passed"); return 0;
}
