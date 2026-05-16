#pragma once

// 检查用户对 ECX 的使用是否正确
#define ECX_USE_USAGE_CHECK 1

// 检查 ECX 的代码是否正确（用于开发 ECX 库本身）
#define ECX_USE_DEV_DEBUG 1

#define ECX_INC_CMSIS_DEVICE_HEADER "stm32f4xx.h"

#define ECX_INC_HAL "stm32f4xx_hal.h"

#define ECX_INC_CMSIS_RTOS2 "cmsis_os2.h"

// 如果通过其他方式（比如编译指令等）手动引入了该配置文件，则可以定义如下宏来避免重复引入。
// 当然，重复引入一般不会导致问题，因为有头文件守卫。
// 此开关预留于可能的特殊情况。
// 如果是用 ECX 的自动机制引入用户配置，则在此处定义该宏不会有任何效果。
// #define ECX_USER_CONFIG_INCLUDED 1
