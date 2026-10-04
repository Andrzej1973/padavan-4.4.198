#ifndef WR_BAND_PROTOCOL_H
#define WR_BAND_PROTOCOL_H
#include <stddef.h>
#include <stdint.h>
enum wr_band_protocol { WR_MT76X2 = 2, WR_MT76X3 = 3 };
enum wr_band_command { WR_QUERY, WR_ENABLE, WR_ADD, WR_DELETE, WR_HEARTBEAT, WR_IDLE_QUERY };
struct wr_band_request {
    enum wr_band_command command;
    const char *interface_name;
    uint8_t enabled, band, channel, mode, table_index;
    uint8_t mac[6];
    uint32_t cookie;
};
/* Returns encoded length or -1. Does not send commands or change radio state. */
int wr_band_encode(enum wr_band_protocol protocol, const struct wr_band_request *request,
                   uint8_t *output, size_t capacity);
#endif
