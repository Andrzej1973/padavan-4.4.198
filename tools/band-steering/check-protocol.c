#include "protocol.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void)
{
    uint8_t out[81], expected[80];
    struct wr_band_request r = {0};
    r.interface_name = "ra0";
    r.command = WR_ENABLE;
    r.enabled = 1; r.band = 1; r.channel = 6; r.mode = 1;
    memset(expected, 0, sizeof(expected));
    expected[0] = 12; expected[8] = 1; expected[9] = 6;
    expected[10] = 1; expected[11] = 1; memcpy(expected + 12, "ra0", 3);
    memset(out, 0xa5, sizeof(out));
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == 80);
    assert(memcmp(out, expected, 80) == 0 && out[80] == 0xa5);
    memset(expected, 0, sizeof(expected)); expected[0] = 11; expected[3] = 1;
    assert(wr_band_encode(WR_MT76X2, &r, out, 32) == 32);
    assert(memcmp(out, expected, 32) == 0);
    r.command = WR_HEARTBEAT;
    assert(wr_band_encode(WR_MT76X2, &r, out, 80) == -1);
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == 80);
    assert(out[0] == 16 && memcmp(out + 8, "ra0", 4) == 0);
    r.command = WR_QUERY;
    assert(wr_band_encode(WR_MT76X2, &r, out, 32) == 32 && out[0] == 6);
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == 80 && out[0] == 8);
    r.command = WR_ADD; r.table_index = 63;
    memcpy(r.mac, "\x02\x01\x02\x03\x04\x05", 6);
    assert(wr_band_encode(WR_MT76X2, &r, out, 32) == 32);
    assert(out[0] == 2 && out[2] == 63 && memcmp(out + 24, r.mac, 6) == 0);
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == 80);
    assert(out[0] == 2 && out[8] == 63 && memcmp(out + 9, r.mac, 6) == 0);
    r.command = WR_DELETE;
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == 80 && out[0] == 3);
    assert(wr_band_encode(WR_MT76X3, &r, out, 79) == -1);
    assert(wr_band_encode(99, &r, out, 80) == -1);
    r.enabled = 2;
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == -1);
    r.enabled = 0; r.interface_name = "1234567890123456";
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == -1);
    r.interface_name = "ra0/bad";
    assert(wr_band_encode(WR_MT76X3, &r, out, 80) == -1);
    assert(wr_band_encode(WR_MT76X3, NULL, out, 80) == -1);
    puts("PASS: Band Steering byte encoders and rejection cases");
    return 0;
}
