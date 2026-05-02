#pragma once
#include <cstdint>

namespace proto {

enum class MsgType : uint8_t {
    Heartbeat = 0x01,
};

// 所有消息结构体均为 packed，字段间无填充。
// 帧格式：COBS( [type:u8] [payload:N字节] [crc16_le:2字节] ) + 0x00

struct [[gnu::packed]] MsgHeartbeat {
    uint32_t seq;
};

}  // namespace proto
