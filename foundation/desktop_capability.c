#include "desktop_capability.h"
#include <string.h>
static int lookup(duckos_desktop_capability_broker *b,uint64_t id,duckos_desktop_peer_identity *p){
 if(b==NULL||b->lookup_peer==NULL||id==0u||p==NULL)return 0;
 (void)memset(p,0,sizeof(*p));
 if(b->lookup_peer(b->context,id,p)!=0)return 0;
 return p->process_id!=0u&&p->process_generation!=0u&&p->session_id!=0u&&p->reserved==0u;
}
static int admin(duckos_desktop_capability_broker *b,uint64_t id){
 duckos_desktop_peer_identity p;
 return lookup(b,id,&p)&&
  (p.role_flags&DUCKOS_DESKTOP_ROLE_SYSTEM)!=0u&&
  (p.authority_rights&DUCKOS_DESKTOP_AUTHORITY_ADMIN)!=0u;
}
duckos_desktop_broker_status duckos_desktop_broker_init(
 duckos_desktop_capability_broker *b,duckos_desktop_peer_lookup_fn fn,void *ctx){
 if(b==NULL||fn==NULL)return DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT;
 (void)memset(b,0,sizeof(*b));b->context=ctx;b->lookup_peer=fn;b->next_token_id=1u;
 return DUCKOS_DESKTOP_BROKER_OK;
}
duckos_desktop_broker_status duckos_desktop_broker_issue(
 duckos_desktop_capability_broker *b,uint64_t issuer,uint64_t target,uint64_t rights,
 uint64_t resource,uint32_t generation,uint64_t now,uint64_t ttl,uint64_t *token){
 duckos_desktop_peer_identity peer;uint64_t expiry;uint32_t i;
 if(token==NULL)return DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT;
 *token=0u;
 if(b==NULL||issuer==0u||target==0u||rights==0u||
    (rights&~DUCKOS_DESKTOP_CAP_KNOWN_MASK)!=0u||now==0u||ttl==0u||
    ttl>DUCKOS_DESKTOP_BROKER_MAX_TTL_NS||((resource==0u)!=(generation==0u)))
  return DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT;
 if(ttl>UINT64_MAX-now)return DUCKOS_DESKTOP_BROKER_OVERFLOW;
 expiry=now+ttl;
 if(!admin(b,issuer))return DUCKOS_DESKTOP_BROKER_ACCESS_DENIED;
 if(!lookup(b,target,&peer))return DUCKOS_DESKTOP_BROKER_UNAUTHENTICATED;
 if((peer.role_flags&DUCKOS_DESKTOP_ROLE_SYSTEM)!=0u)return DUCKOS_DESKTOP_BROKER_INVALID_SCOPE;
 for(i=0u;i<DUCKOS_DESKTOP_BROKER_MAX_GRANTS;i++){
  duckos_desktop_capability_grant *g=&b->grants[i];
  /* Expired leases must not permanently consume bounded grant slots. */
  if(g->active!=0u&&now>=g->expires_at_ns){
   (void)memset(g,0,sizeof(*g));
   if(b->active_count>0u)b->active_count--;
  }
  if(g->active!=0u)continue;
  if(b->next_token_id==0u||b->next_token_id==UINT64_MAX)return DUCKOS_DESKTOP_BROKER_OVERFLOW;
  g->token_id=b->next_token_id++;g->process_id=peer.process_id;
  g->process_generation=peer.process_generation;g->session_id=peer.session_id;
  g->rights=rights;g->resource_id=resource;g->resource_generation=generation;
  g->expires_at_ns=expiry;g->active=1u;b->active_count++;*token=g->token_id;
  return DUCKOS_DESKTOP_BROKER_OK;
 }
 return DUCKOS_DESKTOP_BROKER_FULL;
}
duckos_desktop_broker_status duckos_desktop_broker_authorize(
 duckos_desktop_capability_broker *b,uint64_t connection,uint64_t token,
 uint64_t rights,uint64_t resource,uint32_t generation,uint64_t now){
 duckos_desktop_peer_identity p;uint32_t i;
 if(b==NULL||token==0u||rights==0u||(rights&~DUCKOS_DESKTOP_CAP_KNOWN_MASK)!=0u||
    now==0u||((resource==0u)!=(generation==0u)))return DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT;
 if(!lookup(b,connection,&p))return DUCKOS_DESKTOP_BROKER_UNAUTHENTICATED;
 if((p.role_flags&DUCKOS_DESKTOP_ROLE_SYSTEM)!=0u)return DUCKOS_DESKTOP_BROKER_INVALID_SCOPE;
 for(i=0u;i<DUCKOS_DESKTOP_BROKER_MAX_GRANTS;i++){
  const duckos_desktop_capability_grant *g=&b->grants[i];
  if(g->active==0u||g->token_id!=token)continue;
  if(g->process_id!=p.process_id||g->process_generation!=p.process_generation||
     g->session_id!=p.session_id)return DUCKOS_DESKTOP_BROKER_ACCESS_DENIED;
  if(now>=g->expires_at_ns)return DUCKOS_DESKTOP_BROKER_EXPIRED;
  if((g->rights&rights)!=rights)return DUCKOS_DESKTOP_BROKER_ACCESS_DENIED;
  if(g->resource_id!=0u&&(g->resource_id!=resource||g->resource_generation!=generation))
    return DUCKOS_DESKTOP_BROKER_INVALID_SCOPE;
  return DUCKOS_DESKTOP_BROKER_OK;
 }
 return DUCKOS_DESKTOP_BROKER_NOT_FOUND;
}
duckos_desktop_broker_status duckos_desktop_broker_revoke(
 duckos_desktop_capability_broker *b,uint64_t issuer,uint64_t token){
 uint32_t i;
 if(b==NULL||token==0u)return DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT;
 if(!admin(b,issuer))return DUCKOS_DESKTOP_BROKER_ACCESS_DENIED;
 for(i=0u;i<DUCKOS_DESKTOP_BROKER_MAX_GRANTS;i++){
  duckos_desktop_capability_grant *g=&b->grants[i];
  if(g->active!=0u&&g->token_id==token){g->active=0u;b->active_count--;return DUCKOS_DESKTOP_BROKER_OK;}
 }
 return DUCKOS_DESKTOP_BROKER_NOT_FOUND;
}
const char *duckos_desktop_broker_status_name(duckos_desktop_broker_status s){
 switch(s){
 case DUCKOS_DESKTOP_BROKER_OK:return "ok";
 case DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT:return "invalid-argument";
 case DUCKOS_DESKTOP_BROKER_UNAUTHENTICATED:return "unauthenticated";
 case DUCKOS_DESKTOP_BROKER_ACCESS_DENIED:return "access-denied";
 case DUCKOS_DESKTOP_BROKER_INVALID_SCOPE:return "invalid-scope";
 case DUCKOS_DESKTOP_BROKER_EXPIRED:return "expired";
 case DUCKOS_DESKTOP_BROKER_NOT_FOUND:return "not-found";
 case DUCKOS_DESKTOP_BROKER_FULL:return "grant-table-full";
 case DUCKOS_DESKTOP_BROKER_OVERFLOW:return "overflow";
 }
 return "unknown";
}
