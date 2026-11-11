/* Isolated v1 request layout, not a published ioctl ABI yet. */
#ifndef WR_NVRAM_BATCH_WIRE_H
#define WR_NVRAM_BATCH_WIRE_H
#include <linux/types.h>
#define WR_NVRAM_WIRE_VERSION 1U
#define WR_NVRAM_WIRE_COUNT 16U
struct wr_nvram_wire_item {
 __u32 flags;
 char name[64];
 char expected[129];
 char value[129];
 unsigned char reserved[2];
};
struct wr_nvram_wire_request {
 __u32 version,count,reserved[2];
 struct wr_nvram_wire_item items[WR_NVRAM_WIRE_COUNT];
};
#endif
