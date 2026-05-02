#pragma once
#include <cstddef>
#include <cstdint>
#include <span>

namespace ecx::proto {

// Consistent Overhead Byte Stuffing (COBS).
//
// encode: writes COBS-encoded bytes into dst, appends a 0x00 frame delimiter.
//   dst must be at least src.size() + 2 bytes.
//   Returns the total number of bytes written (including the trailing 0x00).
//
// decode: decodes one COBS frame (without the trailing 0x00) from src into dst.
//   Returns the decoded payload length, or 0 on framing error.

[[nodiscard]]
inline size_t cobs_encode(std::span<const uint8_t> src, std::span<uint8_t> dst) {
    if (dst.size() < src.size() + 2) return 0;

    size_t  write    = 1;  // position of the current overhead byte
    size_t  code_pos = 0;  // index of the last overhead byte written
    uint8_t code     = 1;

    for (const uint8_t b : src) {
        if (b != 0) {
            dst[write++] = b;
            ++code;
            if (code == 0xFF) {
                dst[code_pos] = code;
                code_pos      = write;
                dst[write++]  = 1;
                code          = 1;
            }
        } else {
            dst[code_pos] = code;
            code_pos      = write;
            dst[write++]  = 1;
            code          = 1;
        }
    }
    dst[code_pos] = code;
    dst[write++]  = 0x00;  // frame delimiter
    return write;
}

[[nodiscard]]
inline size_t cobs_decode(std::span<const uint8_t> src, std::span<uint8_t> dst) {
    if (src.empty() || dst.size() < src.size()) return 0;

    size_t read  = 0;
    size_t write = 0;

    while (read < src.size()) {
        const uint8_t code = src[read++];
        if (code == 0) return 0;  // unexpected zero (framing error)

        for (uint8_t i = 1; i < code; ++i) {
            if (read >= src.size()) return 0;
            dst[write++] = src[read++];
        }
        if (code < 0xFF && read < src.size()) { dst[write++] = 0x00; }
    }
    return write;
}

}  // namespace ecx::proto
