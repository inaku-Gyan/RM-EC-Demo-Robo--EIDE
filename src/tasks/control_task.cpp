#include "FreeRTOS.h"
#include "task.h"

// Stub: 1 kHz control loop skeleton.
// TODO: read sensor data, run PID, write actuator outputs.
void control_task(void* /*unused*/) {
    TickType_t last_wake = xTaskGetTickCount();
    for (;;) {
        // placeholder — add control logic here
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(1));
    }
}
