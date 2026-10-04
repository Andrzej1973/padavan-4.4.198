#include <stddef.h>
#include <sys/socket.h>
#include <linux/wireless.h>
#include <linux/rtnetlink.h>
_Static_assert(sizeof(void *) == 4, "MIPS32 pointer required");
_Static_assert(IW_EV_LCP_LEN == 4 && IW_EV_POINT_LEN == 8, "Unexpected kernel Wireless Extensions framing");
_Static_assert(IW_EV_POINT_OFF == 4, "Unexpected iw_point pointer offset");
_Static_assert(sizeof(struct nlmsghdr) == 16 && sizeof(struct ifinfomsg) == 16,
               "Unexpected rtnetlink framing");
_Static_assert(sizeof(struct rtattr) == 4 && IFLA_WIRELESS == 11 && RTM_NEWLINK == 16,
               "Unexpected rtnetlink constants");
_Static_assert(IWEVCUSTOM == 0x8c02, "Unexpected Wireless Extensions event");
const unsigned int wr_wext_abi_verified = 1;
