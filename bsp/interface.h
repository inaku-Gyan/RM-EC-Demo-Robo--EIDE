// bsp/interface.h — CubeMX 与 C++ 层之间的唯一耦合点
// C 兼容，不含任何 C++ 语法
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void user_init(void);
void user_error_handler(void);
void user_assert_failed(const uint8_t* file, uint32_t line);

void usb_cdc_init_rx(void);
void usb_cdc_rx_handler(uint8_t* buf, uint32_t len);
void usb_cdc_tx_cplt(void);

#ifdef __cplusplus
}
#endif
