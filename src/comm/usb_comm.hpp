#pragma once
#include <array>
#include <cstdint>
#include <span>

#include "FreeRTOS.h"
#include "queue.h"

namespace usb {

struct RxPacket {
    std::array<uint8_t, 64> data;
    uint32_t                len;
};

// 通过 USB CDC 发送数据。阻塞等待上一次传输完成后再发起新传输。
// data 超过 TX 缓冲区大小时返回 false。
bool send(std::span<const uint8_t> data);

// 阻塞等待一个 USB RX 数据包到来（或超时）。超时返回 false。
bool rx_receive(RxPacket& pkt, TickType_t timeout = portMAX_DELAY);

}  // namespace usb
