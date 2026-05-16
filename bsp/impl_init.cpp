#include <task_demo.hpp>

#include "cubemx_inc/bsp_hooks/general.h"

extern "C" void bsp_init_before_rtos_init() {}

extern "C" void bsp_init_after_rtos_init() { osThreadNew(task_demo, nullptr, nullptr); }

extern "C" void bsp_init_in_rtos_thread() {}
