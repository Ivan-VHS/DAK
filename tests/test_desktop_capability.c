#include "desktop_capability.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
typedef struct {duckos_desktop_peer_identity peers[4];} Fake;
static int lookup(void *ctx,uint64_t id,duckos_desktop_peer_identity *p){
 Fake*f=(Fake*)ctx;if(id==0u||id>3u||p==NULL)return -1;*p=f->peers[id];return p->process_id==0u?-1:0;
}
static void setup(Fake*f){
 f->peers[1].process_id=1u;f->peers[1].process_generation=1u;f->peers[1].session_id=10u;
 f->peers[1].role_flags=DUCKOS_DESKTOP_ROLE_SYSTEM;f->peers[1].authority_rights=DUCKOS_DESKTOP_AUTHORITY_ADMIN;
 f->peers[2].process_id=42u;f->peers[2].process_generation=7u;f->peers[2].session_id=10u;
}
static void test_lifecycle(void){
 Fake f={0};duckos_desktop_capability_broker b;uint64_t token=0u;setup(&f);
 assert(duckos_desktop_broker_init(&b,lookup,&f)==DUCKOS_DESKTOP_BROKER_OK);
 assert(duckos_desktop_broker_issue(&b,1u,2u,DUCKOS_DESKTOP_CAP_WINDOW_CREATE|DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,0u,0u,100u,500u,&token)==DUCKOS_DESKTOP_BROKER_OK);
 assert(token!=0u&&b.active_count==1u);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CREATE,0u,0u,101u)==DUCKOS_DESKTOP_BROKER_OK);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_INPUT_READ,0u,0u,101u)==DUCKOS_DESKTOP_BROKER_ACCESS_DENIED);
 f.peers[3]=f.peers[2];f.peers[3].process_generation++;
 assert(duckos_desktop_broker_authorize(&b,3u,token,DUCKOS_DESKTOP_CAP_WINDOW_CREATE,0u,0u,101u)==DUCKOS_DESKTOP_BROKER_ACCESS_DENIED);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CREATE,0u,0u,600u)==DUCKOS_DESKTOP_BROKER_EXPIRED);
 assert(duckos_desktop_broker_revoke(&b,1u,token)==DUCKOS_DESKTOP_BROKER_OK&&b.active_count==0u);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CREATE,0u,0u,102u)==DUCKOS_DESKTOP_BROKER_NOT_FOUND);
}
static void test_scope_and_issuer(void){
 Fake f={0};duckos_desktop_capability_broker b;uint64_t token=0u;
 f.peers[1].process_id=8u;f.peers[1].process_generation=1u;f.peers[1].session_id=3u;
 f.peers[2].process_id=9u;f.peers[2].process_generation=1u;f.peers[2].session_id=3u;
 assert(duckos_desktop_broker_init(&b,lookup,&f)==DUCKOS_DESKTOP_BROKER_OK);
 assert(duckos_desktop_broker_issue(&b,1u,2u,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,77u,2u,100u,500u,&token)==DUCKOS_DESKTOP_BROKER_ACCESS_DENIED);
 f.peers[1].role_flags=DUCKOS_DESKTOP_ROLE_SYSTEM;f.peers[1].authority_rights=DUCKOS_DESKTOP_AUTHORITY_ADMIN;
 assert(duckos_desktop_broker_issue(&b,1u,2u,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,77u,2u,100u,500u,&token)==DUCKOS_DESKTOP_BROKER_OK);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,77u,2u,101u)==DUCKOS_DESKTOP_BROKER_OK);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,78u,2u,101u)==DUCKOS_DESKTOP_BROKER_INVALID_SCOPE);
 assert(duckos_desktop_broker_authorize(&b,2u,token,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,77u,3u,101u)==DUCKOS_DESKTOP_BROKER_INVALID_SCOPE);
 assert(duckos_desktop_broker_issue(&b,1u,2u,UINT64_C(1)<<40u,0u,0u,100u,500u,&token)==DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT);
}
static void test_expired_grants_are_reclaimed(void){
 Fake f={0};duckos_desktop_capability_broker b;uint64_t token=0u;
 setup(&f);
 assert(duckos_desktop_broker_init(&b,lookup,&f)==DUCKOS_DESKTOP_BROKER_OK);
 for(uint32_t i=0u;i<DUCKOS_DESKTOP_BROKER_MAX_GRANTS;i++){
  assert(duckos_desktop_broker_issue(&b,1u,2u,DUCKOS_DESKTOP_CAP_WINDOW_CREATE,
   0u,0u,100u,100u,&token)==DUCKOS_DESKTOP_BROKER_OK);
 }
 assert(b.active_count==DUCKOS_DESKTOP_BROKER_MAX_GRANTS);
 const uint64_t expired_token=token;
 assert(duckos_desktop_broker_issue(&b,1u,2u,DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,
  0u,0u,201u,100u,&token)==DUCKOS_DESKTOP_BROKER_OK);
 assert(token!=0u&&token!=expired_token);
 assert(b.active_count==1u);
 assert(duckos_desktop_broker_authorize(&b,2u,expired_token,
  DUCKOS_DESKTOP_CAP_WINDOW_CREATE,0u,0u,202u)==DUCKOS_DESKTOP_BROKER_NOT_FOUND);
 assert(duckos_desktop_broker_authorize(&b,2u,token,
  DUCKOS_DESKTOP_CAP_WINDOW_CONTROL,0u,0u,202u)==DUCKOS_DESKTOP_BROKER_OK);
}
int main(void){test_lifecycle();test_scope_and_issuer();test_expired_grants_are_reclaimed();puts("DuckOS desktop broker tests passed");return 0;}
