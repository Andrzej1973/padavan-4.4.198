#define _GNU_SOURCE
#include "arp-state.h"
#include <assert.h>
static int parse(const char *rows,struct wr_iot_arp_state *out){FILE *fp=tmpfile();int result;assert(fp);assert(fputs("IP address HW type Flags HW address Mask Device\n",fp)>=0);assert(fputs(rows,fp)>=0);rewind(fp);result=wr_iot_arp_stream(fp,"br0",out);assert(!fclose(fp));return result;}
int main(void){struct wr_iot_arp_state out,before;memset(&before,0xa5,sizeof(before));out=before;
 assert(parse("192.168.1.20 0x1 0x6 02:11:22:33:44:55 * br0\n192.168.1.30 0x1 0x2 02:11:22:33:44:66 * br0\n10.0.0.2 0x1 0x6 02:11:22:33:44:77 * wan0\n",&out));assert(out.count==1&&!strcmp(out.interface,"br0")&&out.entries[0].mac[5]==0x55);
 out=before;assert(!parse("192.168.1.20 0x1 0x4 00:00:00:00:00:00 * br0\n",&out));assert(!memcmp(&out,&before,sizeof(out)));
 assert(!parse("192.168.1.20 0x1 0x6 malformed * br0\n",&out));assert(!memcmp(&out,&before,sizeof(out)));
 assert(!parse("192.168.1.20 0x1 0x6 02:11:22:33:44:55 * br0\n192.168.1.20 0x1 0x6 02:11:22:33:44:66 * br0\n",&out));
 assert(wr_iot_arp_capture("lo",&out));assert(out.count==0);
 puts("PASS permanent LAN ARP capture: dynamic/foreign interface excluded, incomplete/malformed/duplicate entries rejected, actual kernel read; restore and RC integration pending");return 0;}
