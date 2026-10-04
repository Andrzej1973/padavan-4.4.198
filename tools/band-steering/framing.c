#include "framing.h"
static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static size_t align4(size_t n) { return (n + 3) & ~(size_t)3; }
static int scan_wireless(const uint8_t *p, size_t length,
    const struct wr_band_route *routes, size_t count, uint32_t index,
    wr_band_event_callback cb, void *ctx)
{
    size_t offset = 0, radio;
    int events = 0;
    for (radio = 0; radio < count && routes[radio].ifindex != index; ++radio) {}
    while (offset < length) {
        size_t size;
        uint16_t command;
        if (length - offset < 4) return -1;
        size = le16(p + offset); command = le16(p + offset + 2);
        if (size < 4 || size > length - offset) return -1;
        if (command == 0x8c02) { /* IWEVCUSTOM */
            struct wr_band_event event;
            int decoded;
            if (size < 8 || le16(p + offset + 4) != size - 8) return -1;
            if (le16(p + offset + 6) == 0x0950 && radio < count) {
                decoded = wr_band_decode(routes[radio].protocol, p + offset + 8, size - 8, &event);
                if (decoded < 0) return -1;
                if (decoded) { ++events; if (cb) cb(radio, &event, ctx); }
            }
        }
        offset += size; /* Wireless events are not individually aligned. */
    }
    return events;
}
static int scan(const uint8_t *data, size_t length, const struct wr_band_route *routes,
    size_t count, wr_band_event_callback cb, void *ctx)
{
    size_t offset = 0;
    int events = 0;
    while (offset < length) {
        size_t size, step;
        if (length - offset < 16) return -1;
        size = le32(data + offset); step = align4(size);
        if (size < 16 || size > length - offset || step > length - offset) return -1;
        if (le32(data + offset + 12) != 0) return -1;
        if (le16(data + offset + 4) == 2 || le16(data + offset + 4) == 4) return -1;
        if (le16(data + offset + 4) == 16) { /* RTM_NEWLINK */
            size_t attr;
            uint32_t index;
            if (size < 32) return -1;
            index = le32(data + offset + 20);
            for (attr = 32; attr < size;) {
                size_t attr_size, attr_step;
                int n;
                if (size - attr < 4) return -1;
                attr_size = le16(data + offset + attr);
                attr_step = align4(attr_size);
                if (attr_size < 4 || attr_size > size - attr || attr_step > size - attr) return -1;
                if (le16(data + offset + attr + 2) == 11) { /* IFLA_WIRELESS */
                    n = scan_wireless(data + offset + attr + 4, attr_size - 4,
                                      routes, count, index, cb, ctx);
                    if (n < 0) return -1;
                    events += n;
                }
                attr += attr_step;
            }
        }
        offset += step;
    }
    return events;
}
int wr_band_parse_netlink(const uint8_t *data, size_t length,
    const struct wr_band_route *routes, size_t count, wr_band_event_callback cb, void *ctx)
{
    size_t n;
    int events;
    if (!data || !routes || !count || count > 2 || length > 65536) return -1;
    for (n = 0; n < count; ++n) {
        if (!routes[n].ifindex || (routes[n].protocol != WR_MT76X2 && routes[n].protocol != WR_MT76X3)) return -1;
        if (n && routes[n].ifindex == routes[0].ifindex) return -1;
    }
    events = scan(data, length, routes, count, 0, 0);
    if (events < 0 || !cb) return events;
    return scan(data, length, routes, count, cb, ctx);
}
