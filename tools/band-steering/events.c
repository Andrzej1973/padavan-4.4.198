#include "events.h"
#include "protocol-layout.h"
#include <string.h>
static uint32_t read_cookie(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static int copy_interface(char *out, const uint8_t *in)
{
    size_t n;
    for (n = 0; n < 16 && in[n]; ++n) {
        uint8_t c = in[n];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.')) return -1;
    }
    if (!n || n == 16) return -1;
    memcpy(out, in, n); out[n] = 0;
    return 0;
}
static void copy_rssi(struct wr_band_event *e, const uint8_t *p, unsigned n)
{
    unsigned i;
    e->rssi_count = (uint8_t)n;
    for (i = 0; i < n; ++i) e->rssi[i] = (int8_t)(p[i] < 128 ? p[i] : (int)p[i] - 256);
}
int wr_band_decode(enum wr_band_protocol protocol, const uint8_t *p,
                   size_t length, struct wr_band_event *e)
{
    struct wr_band_event result;
    if (!p || !e) return -1;
    if ((protocol == WR_MT76X2 && length != WR_MT76X2_MESSAGE_SIZE) ||
        (protocol == WR_MT76X3 && length != WR_MT76X3_MESSAGE_SIZE) ||
        (protocol != WR_MT76X2 && protocol != WR_MT76X3)) return -1;
    memset(&result, 0, sizeof(result));
    result.action = p[0];
    if (protocol == WR_MT76X2) {
        switch (p[0]) {
        case 0x73:
            result.type = WR_EVENT_GRANT;
            result.table_index = p[WR_MT76X2_TALBEINDEX];
            result.grant_state = p[WR_MT76X2_RETURNCODE];
            memcpy(result.mac, p + WR_MT76X2_ADDR, 6);
            result.cookie = read_cookie(p + WR_MT76X2_TIME);
            if (!result.cookie || result.table_index >= 64 || result.grant_state > 2) return -1;
            break;
        case 5:
            result.type = WR_EVENT_IDLE;
            result.table_index = p[WR_MT76X2_TALBEINDEX];
            result.idle_state = p[WR_MT76X2_RETURNCODE] == 0 ? 0 :
                               (p[WR_MT76X2_RETURNCODE] == 8 ? 1 : 2);
            memcpy(result.mac, p + WR_MT76X2_ADDR, 6);
            result.cookie = read_cookie(p + WR_MT76X2_TIME);
            if (!result.cookie || result.table_index >= 64) return -1;
            break;
        case 1:
            result.type = WR_EVENT_CLIENT;
            result.band = p[WR_MT76X2_BAND];
            result.frame_type = p[WR_MT76X2_FRAMETYPE];
            memcpy(result.mac, p + WR_MT76X2_ADDR, 6);
            copy_rssi(&result, p + WR_MT76X2_RSSI, 3);
            break;
        case 3:
            result.type = WR_EVENT_DELETED;
            memcpy(result.mac, p + WR_MT76X2_ADDR, 6);
            break;
        case 7: case 8:
            result.type = WR_EVENT_READY;
            result.ready = p[p[0] == 7 ? WR_MT76X2_B2GINFREADY : WR_MT76X2_B5GINFREADY];
            if (result.ready > 1) return -1;
            break;
        case 11:
            result.type = WR_EVENT_ENABLED; result.enabled = p[WR_MT76X2_ONOFF];
            if (result.enabled > 1) return -1;
            break;
        default: return 0;
        }
    } else {
        switch (p[0]) {
        case 0x73:
            result.type = WR_EVENT_GRANT;
            result.table_index = p[WR_MT76X3_DATA_IDLE_TABLEINDEX];
            result.grant_state = p[WR_MT76X3_DATA_IDLE_RETURNCODE];
            result.cookie = read_cookie(p + WR_MT76X3_DATA_IDLE_COOKIE);
            memcpy(result.mac, p + WR_MT76X3_DATA_IDLE_ADDR, 6);
            if (!result.cookie || result.table_index >= 64 || result.grant_state > 3) return -1;
            break;
        case 0x71:
            result.type = WR_EVENT_IDLE;
            result.table_index = p[WR_MT76X3_DATA_IDLE_TABLEINDEX];
            result.idle_state = p[WR_MT76X3_DATA_IDLE_RETURNCODE];
            result.cookie = read_cookie(p + WR_MT76X3_DATA_IDLE_COOKIE);
            memcpy(result.mac, p + WR_MT76X3_DATA_IDLE_ADDR, 6);
            if (!result.cookie || result.table_index >= 64 || result.idle_state > 2) return -1;
            break;
        case 1:
            result.type = WR_EVENT_CLIENT;
            result.frame_type = p[WR_MT76X3_DATA_CLI_EVENT_FRAMETYPE];
            result.band = p[WR_MT76X3_DATA_CLI_EVENT_BAND];
            result.channel = p[WR_MT76X3_DATA_CLI_EVENT_CHANNEL];
            memcpy(result.mac, p + WR_MT76X3_DATA_CLI_EVENT_ADDR, 6);
            if (result.frame_type == 0)
                copy_rssi(&result, p + WR_MT76X3_DATA_CLI_EVENT_DATA_CLI_PROBE_RSSI, 4);
            else if (result.frame_type == 3)
                copy_rssi(&result, p + WR_MT76X3_DATA_CLI_EVENT_DATA_CLI_AUTH_RSSI, 4);
            break;
        case 9:
            result.type = WR_EVENT_READY;
            result.ready = p[WR_MT76X3_DATA_INF_STATUS_RSP_BINFREADY];
            result.channel = p[WR_MT76X3_DATA_INF_STATUS_RSP_CHANNEL];
            result.band = p[WR_MT76X3_DATA_INF_STATUS_RSP_BAND];
            if (result.ready > 1 || copy_interface(result.interface_name,
                p + WR_MT76X3_DATA_INF_STATUS_RSP_UCIFNAME) < 0) return -1;
            break;
        case 12:
            result.type = WR_EVENT_ENABLED;
            result.enabled = p[WR_MT76X3_DATA_ONOFF_ONOFF];
            result.band = p[WR_MT76X3_DATA_ONOFF_BAND];
            result.channel = p[WR_MT76X3_DATA_ONOFF_CHANNEL];
            if (result.enabled > 1 || copy_interface(result.interface_name,
                p + WR_MT76X3_DATA_ONOFF_UCIFNAME) < 0) return -1;
            break;
        case 15: {
            const uint8_t *pid = p + WR_MT76X3_DATA_REJECT_BODY_DAEMONPID;
            result.type = WR_EVENT_REJECTED;
            result.owner_pid = (uint32_t)pid[0] | ((uint32_t)pid[1] << 8) |
                ((uint32_t)pid[2] << 16) | ((uint32_t)pid[3] << 24);
            break;
        }
        default: return 0;
        }
    }
    *e = result;
    return 1;
}
