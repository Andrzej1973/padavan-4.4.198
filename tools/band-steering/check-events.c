#include "events.h"
#include "protocol-layout.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void)
{
    uint8_t p[160] = {0};
    struct wr_band_event e, before;
    size_t n;
    p[0] = 1; p[WR_MT76X2_FRAMETYPE] = 3;
    p[WR_MT76X2_RSSI] = 186;
    memcpy(p + WR_MT76X2_ADDR, "\x02\x01\x02\x03\x04\x05", 6);
    assert(wr_band_decode(WR_MT76X2, p, 32, &e) == 1);
    assert(e.type == WR_EVENT_CLIENT && e.rssi_count == 3 && e.rssi[0] == -70);
    assert(e.mac[0] == 2 && e.frame_type == 3);
    memset(p, 0, sizeof(p));
    p[0] = 1; p[WR_MT76X3_DATA_CLI_EVENT_FRAMETYPE] = 0;
    p[WR_MT76X3_DATA_CLI_EVENT_DATA_CLI_PROBE_RSSI] = 191;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1);
    assert(e.rssi_count == 4 && e.rssi[0] == -65);
    p[WR_MT76X3_DATA_CLI_EVENT_FRAMETYPE] = 2;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1 && e.rssi_count == 0);
    memset(p, 0, sizeof(p));
    p[0] = 9; p[WR_MT76X3_DATA_INF_STATUS_RSP_BINFREADY] = 1;
    memcpy(p + WR_MT76X3_DATA_INF_STATUS_RSP_UCIFNAME, "ra0", 4);
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1);
    assert(e.type == WR_EVENT_READY && e.ready == 1 && strcmp(e.interface_name, "ra0") == 0);
    p[WR_MT76X3_DATA_INF_STATUS_RSP_BINFREADY] = 2;
    before = e;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == -1 && memcmp(&e, &before, sizeof(e)) == 0);
    p[WR_MT76X3_DATA_INF_STATUS_RSP_BINFREADY] = 1;
    memset(p + WR_MT76X3_DATA_INF_STATUS_RSP_UCIFNAME, 'x', 32);
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == -1);
    memset(p, 0, sizeof(p));
    p[0] = 12; p[WR_MT76X3_DATA_ONOFF_ONOFF] = 1;
    memcpy(p + WR_MT76X3_DATA_ONOFF_UCIFNAME, "ra0", 4);
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1 && e.enabled == 1);
    memset(p, 0, sizeof(p));
    p[0] = 15; p[WR_MT76X3_DATA_REJECT_BODY_DAEMONPID] = 0x34;
    p[WR_MT76X3_DATA_REJECT_BODY_DAEMONPID + 1] = 0x12;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1 && e.owner_pid == 0x1234);
    memset(p, 0, sizeof(p));
    p[0] = 5; p[WR_MT76X2_TALBEINDEX] = 7; p[WR_MT76X2_RETURNCODE] = 8;
    p[WR_MT76X2_TIME] = 1;
    assert(wr_band_decode(WR_MT76X2, p, 32, &e) == 1 && e.type == WR_EVENT_IDLE && e.idle_state == 1 && e.cookie == 1);
    p[WR_MT76X2_RETURNCODE] = 0;
    assert(wr_band_decode(WR_MT76X2, p, 32, &e) == 1 && e.idle_state == 0);
    memset(p, 0, sizeof(p));
    p[0] = 0x71; p[WR_MT76X3_DATA_IDLE_TABLEINDEX] = 7; p[WR_MT76X3_DATA_IDLE_COOKIE] = 1;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 1 && e.type == WR_EVENT_IDLE && e.table_index == 7 && e.cookie == 1);
    p[WR_MT76X3_DATA_IDLE_RETURNCODE] = 3;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == -1);
    for (n = 0; n < sizeof(p); ++n) {
        if (n != 80) assert(wr_band_decode(WR_MT76X3, p, n, &e) == -1);
        if (n != 32) assert(wr_band_decode(WR_MT76X2, p, n, &e) == -1);
    }
    p[0] = 255; before = e;
    assert(wr_band_decode(WR_MT76X3, p, 80, &e) == 0 && memcmp(&e, &before, sizeof(e)) == 0);
    assert(wr_band_decode(99, p, 80, &e) == -1);
    assert(wr_band_decode(WR_MT76X3, NULL, 80, &e) == -1);
    puts("PASS: driver payload decoding, lengths, RSSI union selection and malformed input");
    return 0;
}
