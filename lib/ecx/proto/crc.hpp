#pragma once
#include <cstdint>
#include <span>

namespace ecx::proto {

// CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflection).
[[nodiscard]]
constexpr uint16_t crc16_update(uint16_t crc, uint8_t byte) {
    crc ^= static_cast<uint16_t>(byte) << 8;
    for (int i = 0; i < 8; ++i) { crc = (crc & 0x8000U) ? ((crc << 1) ^ 0x1021U) : (crc << 1); }
    return crc;
}

[[nodiscard]]
inline uint16_t crc16(std::span<const uint8_t> data) {
    uint16_t crc = 0xFFFFu;
    for (uint8_t b : data) crc = crc16_update(crc, b);
    return crc;
}

}  // namespace ecx::proto
