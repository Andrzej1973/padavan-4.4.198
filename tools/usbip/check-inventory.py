#!/usr/bin/env python3
"""Generate a native fixture for the actual HTTP inventory implementation."""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.parent.mkdir(parents=True,exist_ok=True)
sysfs=a.output.parent/'usbip-sysfs'
sysfs.mkdir(exist_ok=True)
for bus,klass in [('1-1','00'),('1-2','09'),('1-3.2','ff')]:
    device=sysfs/bus
    device.mkdir(exist_ok=True)
    for attr,value in [('idVendor','1234'),('idProduct','abcd'),('bDeviceClass',klass)]:
        (device/attr).write_text(value+'\n')
driver=sysfs/'1-1/driver'
(sysfs/'1-1/serial').write_text('unit-test-only\n')
(sysfs/'1-3.2/serial').write_text('x'*300+'\n')
if not driver.is_symlink():driver.symlink_to('/sys/bus/usb/drivers/usbip-host')
(sysfs/'usb1').mkdir(exist_ok=True)
(sysfs/'1-1:1.0').mkdir(exist_ok=True)
prefix=r'''
#include <assert.h>
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
typedef void *webs_t;
static char reply[32768];
static int websWrite(webs_t wp,const char *format,...) {
 va_list ap;int n;size_t remaining=sizeof(reply)-strlen(reply);(void)wp;
 va_start(ap,format);n=vsnprintf(reply+strlen(reply),remaining,format,ap);va_end(ap);
 assert(n>=0 && (size_t)n<remaining);return n;
}
'''
tests=r'''
int main(void) {
 assert(wr_usbip_busid("1-1") && wr_usbip_busid("12-1.2.3"));
 { char serial[513];
   wr_usbip_serial_hex("1-1",serial);assert(!strcmp(serial,"756e69742d746573742d6f6e6c79"));
   wr_usbip_serial_hex("1-3.2",serial);assert(!serial[0]);
   wr_usbip_serial_hex("99-99",serial);assert(!serial[0]);
 }
 assert(!wr_usbip_busid("") && !wr_usbip_busid("../1-1") && !wr_usbip_busid("1-1:1.0"));
 assert(!wr_usbip_busid("1-") && !wr_usbip_busid("1-1.") && !wr_usbip_busid("usb1"));
 ej_wr_usbip_inventory(0,NULL,0,NULL);
 assert(strstr(reply,"\"busid\":\"1-1\",\"vendor\":\"1234\",\"product\":\"abcd\",\"class\":\"00\",\"exported\":1"));
 assert(strstr(reply,"\"busid\":\"1-3.2\"") && strstr(reply,"\"exported\":0"));
 assert(!strstr(reply,"1-2") && !strstr(reply,"1-1:1.0") && strstr(reply,"\"truncated\":false"));
 reply[0]=0;ej_wr_usbip_inventory(0,NULL,1,NULL);assert(strstr(reply,"invalid_request"));
 assert(rename(WR_USBIP_SYSFS, WR_USBIP_SYSFS "-offline")==0);
 reply[0]=0;ej_wr_usbip_inventory(0,NULL,0,NULL);assert(strstr(reply,"source_unavailable"));
 assert(rename(WR_USBIP_SYSFS "-offline",WR_USBIP_SYSFS)==0);
 puts("PASS USB/IP sysfs inventory: IDs, hubs, export binding, invalid request, unavailable source");
 return 0;
}
'''
a.output.write_text(prefix+'\n#define WR_USBIP_SYSFS '+json.dumps(str(sysfs.resolve()))+'\n'+Path(__file__).with_name('inventory.inc').read_text()+tests)
