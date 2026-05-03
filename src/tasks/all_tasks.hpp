#pragma once

#include "FreeRTOS.h"  // IWYU pragma: export
#include "cmsis_os.h"  // IWYU pragma: export
#include "task.h"      // IWYU pragma: export

void comm_task(void* /*unused*/);

void control_task(void* /*unused*/);

void monitor_task(void* /*unused*/);
