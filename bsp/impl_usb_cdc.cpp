#include "cubemx_inc/bsp_hooks/usb_cdc.h"
#include "usbd_cdc_if.h"

extern "C" bsp_usbd_status_t bsp_usb_cdc_init() { return BSP_USBD_OK_i8; }

extern "C" bsp_usbd_status_t bsp_usb_cdc_deinit() { return BSP_USBD_OK_i8; }

extern "C" bsp_usbd_status_t usb_cdc_rx(uint8_t* buf, uint32_t* len) { return BSP_USBD_OK_i8; }

extern "C" bsp_usbd_status_t usb_cdc_tx_cplt() { return BSP_USBD_OK_i8; }
