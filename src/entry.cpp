#include <array>

#include "FreeRTOS.h"
#include "bsp/interface.h"
#include "task.h"

// Forward declarations — defined in tasks/*.cpp
void comm_task(void*);
void control_task(void*);
void monitor_task(void*);

namespace {

StaticTask_t s_comm_tcb;
StaticTask_t s_control_tcb;
StaticTask_t s_monitor_tcb;

std::array<StackType_t, 512> s_comm_stack;
std::array<StackType_t, 256> s_control_stack;
std::array<StackType_t, 256> s_monitor_stack;

}  // namespace

extern "C" void user_init() {
    xTaskCreateStatic(comm_task, "comm", s_comm_stack.size(), nullptr, 3, s_comm_stack.data(),
                      &s_comm_tcb);
    xTaskCreateStatic(control_task, "ctrl", s_control_stack.size(), nullptr, 4,
                      s_control_stack.data(), &s_control_tcb);
    xTaskCreateStatic(monitor_task, "mon", s_monitor_stack.size(), nullptr, 2,
                      s_monitor_stack.data(), &s_monitor_tcb);
}

extern "C" void user_error_handler() {
    __asm volatile("CPSID I" : : : "memory");
    for (;;) {}
}

extern "C" void user_assert_failed(const uint8_t* file, uint32_t line) {
    (void)file;
    (void)line;
    user_error_handler();
}
