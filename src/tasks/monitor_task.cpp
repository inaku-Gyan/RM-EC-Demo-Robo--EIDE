#include "cmsis_os.h"

// Stub: system monitor / heartbeat skeleton.
// TODO: toggle LED, send USB heartbeat, check task stack watermarks.
void monitor_task(void* /*unused*/) {
    for (;;) {
        // placeholder — add LED blink / watchdog / telemetry here
        osDelay(500);
    }
}
