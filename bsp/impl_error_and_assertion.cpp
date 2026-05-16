#include "cubemx_inc/bsp_hooks/general.h"
#include "stm32f4xx.h"  // IWYU pragma: keep — for __disable_irq()

extern "C" void bsp_error_handler() {
    __disable_irq();
    for (;;) {}
}

extern "C" void bsp_assert_failed(const uint8_t* file, uint32_t line) {
    (void)file;
    (void)line;
    bsp_error_handler();
}
