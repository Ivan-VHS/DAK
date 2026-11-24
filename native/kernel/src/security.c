#include "security_api.h"

static duckos_security_engine security_engine;
static int security_initialized;

void duckos_kernel_security_init(void)
{
    duckos_security_engine_init(&security_engine);
    security_initialized = 1;
}

duckos_security_status duckos_kernel_security_submit(
    const duckos_security_event_v1 *event,
    duckos_security_evaluation_v1 *evaluation
)
{
    if (security_initialized == 0) {
        return DUCKOS_SECURITY_INVALID_ARGUMENT;
    }
    return duckos_security_ingest(&security_engine, event, evaluation);
}
