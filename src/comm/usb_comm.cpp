#include "usb_comm.hpp"

#include <etl/array.h>
#include <etl/span.h>

#include <cstdint>
#include <cstring>

#include "FreeRTOS.h"
#include "queue.h"
#include "semphr.h"
#include "usbd_cdc_if.h"

namespace usb {

namespace {

alignas(4) etl::array<etl::array<uint8_t, 64>, 2> rx_buf{};
int rx_active = 0;

alignas(4) etl::array<uint8_t, 512> tx_buf{};
StaticSemaphore_t tx_sem_storage;
SemaphoreHandle_t tx_sem = nullptr;

constexpr size_t                                       RX_QUEUE_DEPTH = 4;
StaticQueue_t                                          rx_q_storage;
etl::array<uint8_t, RX_QUEUE_DEPTH * sizeof(RxPacket)> rx_q_buf{};
QueueHandle_t                                          rx_queue = nullptr;

}  // namespace

// ─── CubeMX CDC 回调（从 bsp_interface.h 接入）────────────────────────────────

extern "C" void usb_cdc_init_rx() {
    // TX 信号量初始为"已给出"，第一次 send() 可直接进行，无需等待 TransmitCplt。
    tx_sem = xSemaphoreCreateBinaryStatic(&tx_sem_storage);
    xSemaphoreGive(tx_sem);

    rx_queue = xQueueCreateStatic(RX_QUEUE_DEPTH, sizeof(RxPacket), rx_q_buf.data(), &rx_q_storage);

    // 将端点缓冲区指向 ping-pong buf[0] 并 arm。
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, rx_buf[rx_active].data());
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
}

extern "C" void usb_cdc_rx_handler(uint8_t* buf, uint32_t len) {
    // 先切换缓冲区并重新 arm，再入队，确保 USB 核心不会写入正在入队的缓冲区。
    rx_active ^= 1;
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, rx_buf[rx_active].data());
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);

    if (rx_queue == nullptr) { return; }

    RxPacket pkt;
    pkt.len = etl::min(len, static_cast<uint32_t>(pkt.data.size()));
    std::memcpy(pkt.data.data(), buf, pkt.len);

    BaseType_t woken = pdFALSE;
    xQueueSendFromISR(rx_queue, &pkt, &woken);
    portYIELD_FROM_ISR(woken);
}

extern "C" void usb_cdc_tx_cplt() {
    if (tx_sem == nullptr) { return; }
    BaseType_t woken = pdFALSE;
    xSemaphoreGiveFromISR(tx_sem, &woken);
    portYIELD_FROM_ISR(woken);
}

// ─── 对外 API ─────────────────────────────────────────────────────────────────

bool send(const etl::span<const uint8_t>& data) {
    if (data.size() > tx_buf.size()) { return false; }
    xSemaphoreTake(tx_sem, portMAX_DELAY);
    std::memcpy(tx_buf.data(), data.data(), data.size());
    return CDC_Transmit_FS(tx_buf.data(), static_cast<uint16_t>(data.size())) == USBD_OK;
}

bool rx_receive(RxPacket& pkt, TickType_t timeout) {
    return xQueueReceive(rx_queue, &pkt, timeout) == pdTRUE;
}

}  // namespace usb
