#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

#include "FreeRTOS.h"
#include "queue.h"

namespace ecx::rtos {

// Type-safe, statically-allocated FreeRTOS queue.
// T must be trivially copyable; N is the maximum number of items.
template <typename T, size_t N>
class Queue {
public:
    Queue() { handle_ = xQueueCreateStatic(N, sizeof(T), buf_.data(), &storage_); }

    // Send from task context. Returns true on success.
    bool send(const T& item, TickType_t timeout = 0) const {
        return xQueueSend(handle_, &item, timeout) == pdTRUE;
    }

    // Send from ISR context. Sets *woken if a higher-priority task was unblocked.
    bool send_from_isr(const T& item, BaseType_t* woken) const {
        return xQueueSendFromISR(handle_, &item, woken) == pdTRUE;
    }

    // Receive from task context. Blocks up to timeout ticks.
    bool receive(T& item, TickType_t timeout = portMAX_DELAY) const {
        return xQueueReceive(handle_, &item, timeout) == pdTRUE;
    }

    [[nodiscard]]
    UBaseType_t waiting() const {
        return uxQueueMessagesWaiting(handle_);
    }

private:
    alignas(T) std::array<uint8_t, N * sizeof(T)> buf_{};
    StaticQueue_t storage_;
    QueueHandle_t handle_;
};

}  // namespace ecx::rtos
