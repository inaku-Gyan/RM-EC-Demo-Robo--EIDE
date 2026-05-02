#include "comm/usb_comm.hpp"

// Stub: receives USB packets and discards them.
// TODO: add COBS decode → CRC check → MsgType dispatch.
void comm_task(void* /*unused*/) {
    usb::RxPacket pkt;
    for (;;) {
        usb::rx_receive(pkt);
        // placeholder — packet received, dispatch here
    }
}
