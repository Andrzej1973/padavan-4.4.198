#include "subnet.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void) {
 struct wr_iot_subnet out,sentinel;struct wr_iot_range used={0xc0a80100,0xc0a801ff};
 memset(&sentinel,0xa5,sizeof(sentinel));out=sentinel;
 assert(wr_iot_subnet_plan(&out,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&used,1));
 assert(out.network==0xc0a83200&&out.broadcast==0xc0a832ff);
#define BAD(g,m,s,e,r,n) do {out=sentinel;assert(!wr_iot_subnet_plan(&out,g,m,s,e,r,n));assert(!memcmp(&out,&sentinel,sizeof(out)));} while(0)
 BAD("192.168.1.1","255.255.255.0","192.168.1.20","192.168.1.200",&used,1);
 BAD("192.168.50.1","255.0.255.0","192.168.50.20","192.168.50.200",NULL,0);
 BAD("192.168.50.1","255.255.255.254","192.168.50.20","192.168.50.200",NULL,0);
 BAD("192.168.50.0","255.255.255.0","192.168.50.20","192.168.50.200",NULL,0);
 BAD("192.168.50.30","255.255.255.0","192.168.50.20","192.168.50.200",NULL,0);
 BAD("192.168.50.1","255.255.255.0","192.168.49.20","192.168.50.200",NULL,0);
 BAD("192.168.50.1","255.255.255.0","192.168.50.200","192.168.50.20",NULL,0);
 BAD("8.8.8.1","255.255.255.0","8.8.8.20","8.8.8.200",NULL,0);
 BAD("192.168.050.1","255.255.255.0","192.168.50.20","192.168.50.200",NULL,0);
 BAD("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",NULL,1);
 used.first=0xc0a80000;used.last=0xc0a8ffff;
 BAD("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&used,1);
 puts("PASS IoT subnet candidate: private contiguous subnet, host and DHCP bounds, gateway exclusion, reserved overlap, untouched output on rejection");return 0;
}
