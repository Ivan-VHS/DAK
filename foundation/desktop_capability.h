#ifndef DUCKOS_DESKTOP_CAPABILITY_H
#define DUCKOS_DESKTOP_CAPABILITY_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define DUCKOS_DESKTOP_BROKER_MAX_GRANTS 128u
#define DUCKOS_DESKTOP_BROKER_MAX_TTL_NS UINT64_C(86400000000000)
#define DUCKOS_DESKTOP_ROLE_SYSTEM (UINT32_C(1)<<0)
#define DUCKOS_DESKTOP_AUTHORITY_ADMIN (UINT64_C(1)<<63)
#define DUCKOS_DESKTOP_CAP_DISPLAY_READ       (UINT64_C(1)<<0)
#define DUCKOS_DESKTOP_CAP_WINDOW_CREATE      (UINT64_C(1)<<1)
#define DUCKOS_DESKTOP_CAP_WINDOW_CONTROL     (UINT64_C(1)<<2)
#define DUCKOS_DESKTOP_CAP_SURFACE_PRESENT    (UINT64_C(1)<<3)
#define DUCKOS_DESKTOP_CAP_INPUT_READ         (UINT64_C(1)<<4)
#define DUCKOS_DESKTOP_CAP_SESSION_CONTROL    (UINT64_C(1)<<5)
#define DUCKOS_DESKTOP_CAP_NOTIFICATION_POST  (UINT64_C(1)<<6)
#define DUCKOS_DESKTOP_CAP_THEME_CONTROL      (UINT64_C(1)<<7)
#define DUCKOS_DESKTOP_CAP_KNOWN_MASK         ((UINT64_C(1)<<8)-UINT64_C(1))
typedef struct {
 uint64_t process_id; uint32_t process_generation; uint64_t session_id;
 uint32_t role_flags; uint32_t reserved; uint64_t authority_rights;
} duckos_desktop_peer_identity;
/* Must use authenticated kernel IPC or trusted host peer credentials. */
typedef int (*duckos_desktop_peer_lookup_fn)(void *,uint64_t,duckos_desktop_peer_identity *);
typedef struct {
 uint64_t token_id,process_id; uint32_t process_generation; uint64_t session_id;
 uint64_t rights,resource_id; uint32_t resource_generation,active; uint64_t expires_at_ns;
} duckos_desktop_capability_grant;
typedef struct {
 void *context; duckos_desktop_peer_lookup_fn lookup_peer;
 uint64_t next_token_id; uint32_t active_count;
 duckos_desktop_capability_grant grants[DUCKOS_DESKTOP_BROKER_MAX_GRANTS];
} duckos_desktop_capability_broker;
typedef enum {
 DUCKOS_DESKTOP_BROKER_OK=0, DUCKOS_DESKTOP_BROKER_INVALID_ARGUMENT=-1,
 DUCKOS_DESKTOP_BROKER_UNAUTHENTICATED=-2, DUCKOS_DESKTOP_BROKER_ACCESS_DENIED=-3,
 DUCKOS_DESKTOP_BROKER_INVALID_SCOPE=-4, DUCKOS_DESKTOP_BROKER_EXPIRED=-5,
 DUCKOS_DESKTOP_BROKER_NOT_FOUND=-6, DUCKOS_DESKTOP_BROKER_FULL=-7,
 DUCKOS_DESKTOP_BROKER_OVERFLOW=-8
} duckos_desktop_broker_status;
duckos_desktop_broker_status duckos_desktop_broker_init(
 duckos_desktop_capability_broker *,duckos_desktop_peer_lookup_fn,void *);
duckos_desktop_broker_status duckos_desktop_broker_issue(
 duckos_desktop_capability_broker *,uint64_t,uint64_t,uint64_t,
 uint64_t,uint32_t,uint64_t,uint64_t,uint64_t *);
duckos_desktop_broker_status duckos_desktop_broker_authorize(
 duckos_desktop_capability_broker *,uint64_t,uint64_t,uint64_t,
 uint64_t,uint32_t,uint64_t);
duckos_desktop_broker_status duckos_desktop_broker_revoke(
 duckos_desktop_capability_broker *,uint64_t,uint64_t);
const char *duckos_desktop_broker_status_name(duckos_desktop_broker_status);
#ifdef __cplusplus
}
#endif
#endif
