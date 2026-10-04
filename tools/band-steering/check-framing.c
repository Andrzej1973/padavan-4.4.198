#include "framing.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static int calls;
static void put16(uint8_t *p, unsigned n) { p[0] = (uint8_t)n; p[1] = (uint8_t)(n >> 8); }
static void put32(uint8_t *p, unsigned n) { put16(p, n); put16(p + 2, n >> 16); }
static size_t packet(uint8_t *p, unsigned index, int modern)
{
    size_t payload = modern ? 80 : 32, size = 40 + 4 + 8 + payload;
    memset(p, 0, size);
    put32(p, (unsigned)size); put16(p + 4, 16); put32(p + 20, index);
    put16(p + 32, 8); put16(p + 34, 3); memcpy(p + 36, "ra0", 4);
    put16(p + 40, (unsigned)(12 + payload)); put16(p + 42, 11);
    put16(p + 44, (unsigned)(8 + payload)); put16(p + 46, 0x8c02);
    put16(p + 48, (unsigned)payload); put16(p + 50, 0x0950);
    p[52] = modern ? 15 : 11;
    if (!modern) p[55] = 1;
    return size;
}
static void event_callback(size_t radio, const struct wr_band_event *e, void *ctx)
{
    assert(ctx == &calls);
    if (radio == 0) assert(e->type == WR_EVENT_ENABLED && e->enabled == 1);
    else assert(radio == 1 && e->type == WR_EVENT_REJECTED);
    ++calls;
}
int main(void)
{
    uint8_t bytes[512], unaligned[513];
    struct wr_band_route routes[2] = {{5, WR_MT76X2}, {6, WR_MT76X3}};
    size_t a = packet(bytes, 5, 0), b, n;
    unsigned seed = 123, i;
    assert(wr_band_parse_netlink(bytes, a, routes, 2, event_callback, &calls) == 1 && calls == 1);
    memcpy(unaligned + 1, bytes, a);
    assert(wr_band_parse_netlink(unaligned + 1, a, routes, 2, 0, 0) == 1);
    for (n = 1; n < a; ++n) assert(wr_band_parse_netlink(bytes, n, routes, 2, 0, 0) == -1);
    b = packet(bytes + a, 6, 1);
    calls = 0;
    assert(wr_band_parse_netlink(bytes, a + b, routes, 2, event_callback, &calls) == 2 && calls == 2);
    calls = 0; put16(bytes + a + 48, 79);
    assert(wr_band_parse_netlink(bytes, a + b, routes, 2, event_callback, &calls) == -1 && calls == 0);
    a = packet(bytes, 7, 0);
    assert(wr_band_parse_netlink(bytes, a, routes, 2, 0, 0) == 0);
    a = packet(bytes, 5, 0); put16(bytes + 50, 0x1234);
    assert(wr_band_parse_netlink(bytes, a, routes, 2, 0, 0) == 0);
    a = packet(bytes, 5, 0); put32(bytes + 12, 1);
    assert(wr_band_parse_netlink(bytes, a, routes, 2, 0, 0) == -1);
    a = packet(bytes, 5, 0); put16(bytes + 40, 0);
    assert(wr_band_parse_netlink(bytes, a, routes, 2, 0, 0) == -1);
    routes[1].ifindex = 5;
    assert(wr_band_parse_netlink(bytes, a, routes, 2, 0, 0) == -1);
    routes[1].ifindex = 6;
    for (i = 0; i < 10000; ++i) {
        for (n = 0; n < sizeof(bytes); ++n) { seed = seed * 1664525u + 1013904223u; bytes[n] = (uint8_t)(seed >> 24); }
        (void)wr_band_parse_netlink(bytes, i % sizeof(bytes), routes, 2, 0, 0);
    }
    puts("PASS: MIPS32 rtnetlink framing, radio mapping, whole-datagram validation and bounded malformed inputs");
    return 0;
}
