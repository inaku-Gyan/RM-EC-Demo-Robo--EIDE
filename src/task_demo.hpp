#pragma once
#include "cmsis_os2.h"

inline static void task_demo(void*) {
    while (true) { osDelay(1000); }
}
