#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 在 RTOS 初始化之前、大部分外设初始化之后 执行的 BSP 初始化
 */
void bsp_init_before_rtos_init(void);

/**
 * @brief 在 RTOS 初始化之后、调度器启动之前 执行的 BSP 初始化
 */
void bsp_init_after_rtos_init(void);

/**
 * @brief 调度器启动之后，在 RTOS 线程中 执行的 BSP 初始化
 */
void bsp_init_in_rtos_thread(void);

/**
 * @brief  This function is executed in case of error occurrence.
 * @retval None
 */
void bsp_error_handler(void);

/**
 * @brief  Reports the name of the source file and the source line number
 *         where the assert_param error has occurred.
 * @param  file: pointer to the source file name
 * @param  line: assert_param error line source number
 * @retval None
 */
void bsp_assert_failed(const uint8_t* file, uint32_t line);

#ifdef __cplusplus
}
#endif
