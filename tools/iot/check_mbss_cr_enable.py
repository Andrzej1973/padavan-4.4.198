#!/usr/bin/env python3
"""Exercise the actual guarded raw MBSS open with injected driver results."""

import argparse
from pathlib import Path
import subprocess
import tempfile

from mbss_cr_enable import guard_cr_enable


def raw_function(source: str) -> str:
    signature = 'static INT wr_iot_mbss_open_raw(PNET_DEV pDev,'
    if source.count(signature) != 1:
        raise ValueError('Expected one claimed raw MBSS open')
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 0
    for position in range(opening, len(source)):
        if source[position] == '{':
            depth += 1
        elif source[position] == '}':
            depth -= 1
            if depth == 0:
                return source[start:position + 1]
    raise ValueError('Unterminated raw MBSS open')


FIXTURE_PREFIX = r'''
#include <assert.h>
#include <stdio.h>
#include <stddef.h>
typedef void VOID;
typedef int INT;
typedef struct device { int id; } *PNET_DEV;
struct wr_iot_radio_ticket { unsigned int serial; };
static struct device dev = { 2 };
static int mode, refs, vendor_count, queued, open_calls, abort_calls, cr_calls;
#define MT_MAC 1
#define NDIS_STATUS_SUCCESS 0
#define CMD_RTPRIV_IOCTL_MBSS_OPEN 1
#define CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN 2
#define CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE 3
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 1
#define RT_MOD_INC_USE_COUNT() (++refs)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#define DBGPRINT(level,args) ((void)0)
#define RTMP_OS_NETDEV_GET_DEVNAME(d) "ra2"
#define RTMP_OS_NETDEV_GET_PRIV(d) ((VOID *)(d))
#define RTMP_OS_NETDEV_START_QUEUE(d) do { assert((d)==&dev); queued++; } while (0)
static INT RTMP_AP_IoctlHandle(VOID *ad, VOID *unused, INT command,
                              INT zero, PNET_DEV device, INT last) {
 (void)unused;
 assert(ad==(VOID *)&dev && device==&dev && !zero && !last);
 if (command==CMD_RTPRIV_IOCTL_MBSS_OPEN) {
  open_calls++;
  return mode==1 ? -1 : 0;
 }
 if (command==CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN) {
  abort_calls++;
  return mode==3 ? -1 : 0;
 }
 assert(command==CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE);
 cr_calls++;
 return mode==4 ? -1 : 0;
}
static INT VIRTUAL_IF_UP_CLAIM(VOID *ad, PNET_DEV device,
 const struct wr_iot_radio_ticket *ticket, unsigned long generation) {
 assert(ad==(VOID *)&dev && device==&dev && ticket && generation==7UL);
 if (mode==2 || mode==3) return -1;
 vendor_count++;
 return 0;
}
'''

FIXTURE_SUFFIX = r'''
int main(void) {
 struct wr_iot_radio_ticket ticket = { 11U };
 for (mode=0; mode<5; mode++) {
  refs=vendor_count=queued=open_calls=abort_calls=cr_calls=0;
  INT result=wr_iot_mbss_open_raw(&dev,&ticket,7UL);
  assert(open_calls==1);
  if (mode==0)
   assert(result==0 && refs==1 && vendor_count==1 && queued==1 &&
          !abort_calls && cr_calls==1);
  if (mode==1)
   assert(result==-1 && !refs && !vendor_count && !queued &&
          !abort_calls && !cr_calls);
  if (mode==2)
   assert(result==-1 && !refs && !vendor_count && !queued &&
          abort_calls==1 && !cr_calls);
  if (mode==3)
   assert(result==-2 && refs==1 && !vendor_count && !queued &&
          abort_calls==1 && !cr_calls);
  if (mode==4)
   assert(result==-3 && refs==1 && vendor_count==1 && !queued &&
          !abort_calls && cr_calls==1);
 }
 puts("PASS raw MBSS CR_ENABLE failure retains pin/count and skips queue");
 return 0;
}
'''


def checked_raw(raw: str) -> str:
    if 'CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE, 0, pDev, 0);' in raw:
        return guard_cr_enable(raw)
    if raw.count('CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE, 0, pDev, 0)') == 1 and \
            raw.count('return -2;') == 1 and raw.count('return -3;') == 1:
        # The assembled candidate already contains the guarded call. Compile
        # that exact raw source, so CI checks the output rather than a mirror.
        return raw
    raise ValueError('MBSS CR_ENABLE guard missing or changed')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, help='isolated v40 ap_mbss_inf.c')
    parser.add_argument('--compiler', type=Path, required=True)
    args = parser.parse_args()
    raw = raw_function(args.source.read_text(encoding='utf-8'))
    checked = checked_raw(raw)
    assert checked_raw(checked) == checked
    with tempfile.TemporaryDirectory(prefix='iot-mbss-cr-') as temporary:
        directory = Path(temporary)
        c_file = directory / 'check.c'
        executable = directory / 'check.exe'
        c_file.write_text(FIXTURE_PREFIX + checked + FIXTURE_SUFFIX, encoding='utf-8')
        subprocess.run([str(args.compiler), '-std=c11', '-Wall', '-Wextra',
                        '-Werror', str(c_file), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == '__main__':
    main()
