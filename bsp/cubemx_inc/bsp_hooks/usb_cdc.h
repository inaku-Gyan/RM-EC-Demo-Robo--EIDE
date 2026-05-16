#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// "usbd_def.h" 提供的 USBD_StatusTypeDef 类型没有限制位数
// 这里重新定义一个类型，限制为 int8_t。
// 因为 usbd_cdc_if.c 中的函数返回值是 int8_t 类型的。（对应 USBD_CDC_ItfTypeDef 中的函数指针类型）
typedef enum : int8_t
{
  BSP_USBD_OK_i8 = 0,
  BSP_USBD_BUSY_i8,
  BSP_USBD_EMEM_i8,
  BSP_USBD_FAIL_i8,
} bsp_usbd_status_t;

/**
  * @brief  Initializes the CDC media low layer over the FS USB IP
  * @retval USBD_OK if all operations are OK else USBD_FAIL
  */
bsp_usbd_status_t bsp_usb_cdc_init(void);

/**
  * @brief  DeInitializes the CDC media low layer
  * @retval USBD_OK if all operations are OK else USBD_FAIL
  */
bsp_usbd_status_t bsp_usb_cdc_deinit(void);

/**
  * @brief  Data received over USB OUT endpoint are sent over CDC interface
  *         through this function.
  *
  *         @note
  *         This function will issue a NAK packet on any OUT packet received on
  *         USB endpoint until exiting this function. If you exit this function
  *         before transfer is complete on CDC interface (ie. using DMA controller)
  *         it will result in receiving more data while previous ones are still
  *         not sent.
  *
  * @param  Buf: Buffer of data to be received
  * @param  Len: Number of data received (in bytes)
  * @retval Result of the operation: USBD_OK if all operations are OK else USBD_FAIL
  */
bsp_usbd_status_t usb_cdc_rx(uint8_t* buf, uint32_t *len);

/**
  * @brief  CDC_TransmitCplt_FS
  *         Data transmitted callback
  *
  *         @note
  *         This function is IN transfer complete callback used to inform user that
  *         the submitted Data is successfully sent over USB.
  *
  * @param  Buf: Buffer of data to be received
  * @param  Len: Number of data received (in bytes)
  * @retval Result of the operation: USBD_OK if all operations are OK else USBD_FAIL
  */
bsp_usbd_status_t usb_cdc_tx_cplt(void);

#ifdef __cplusplus
}
#endif
