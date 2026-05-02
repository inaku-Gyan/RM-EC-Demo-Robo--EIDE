#pragma once
#include "FreeRTOS.h"
#include "semphr.h"

namespace ecx::rtos {

// Statically-allocated binary semaphore.
class BinarySemaphore {
public:
    explicit BinarySemaphore(bool initial_state = false) {
        handle_ = xSemaphoreCreateBinaryStatic(&storage_);
        if (initial_state) { xSemaphoreGive(handle_); }
    }

    bool take(TickType_t timeout = portMAX_DELAY) {
        return xSemaphoreTake(handle_, timeout) == pdTRUE;
    }

    void give() { xSemaphoreGive(handle_); }

    void give_from_isr(BaseType_t* woken) { xSemaphoreGiveFromISR(handle_, woken); }

private:
    StaticSemaphore_t storage_;
    SemaphoreHandle_t handle_;
};

}  // namespace ecx::rtos
