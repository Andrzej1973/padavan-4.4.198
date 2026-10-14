#!/usr/bin/env python3
"""Exercise emitted guard against null, ERR_PTR and valid file handles."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='mt76x2-read-') as directory:
    root = Path(directory)
    target = root/'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/os/linux/rt_linux.c'
    target.parent.mkdir(parents=True)
    fixture = '''int RtmpOSFileRead(RTMP_OS_FD osfd, char *pDataPtr, int readLen)
{
 if (osfd->f_mode & FMODE_CAN_READ)
  return __vfs_read(osfd, pDataPtr, readLen, &osfd->f_pos);
 return -1;
}
'''
    target.write_text(fixture)
    command = [sys.executable,str(repo/'prepare-mt76x2-file-read.py'),str(root)]
    subprocess.run(command,check=True)
    patched = target.read_text().replace('#include <linux/err.h>','')
    result = subprocess.run(command,capture_output=True)
    assert result.returncode != 0
    assert target.read_text().count('wr_mt76x2_file_read_guard') == 1
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#define FMODE_CAN_READ 1
#define IS_ERR_OR_NULL(p) (!(p) || (uintptr_t)(p) >= (uintptr_t)-4095)
typedef struct wr_test_file {int f_mode;long f_pos;} *RTMP_OS_FD;
static int calls;
static int __vfs_read(RTMP_OS_FD fd,char *buffer,int size,long *pos) {
 assert(fd && buffer && size==4 && pos==&fd->f_pos);calls++;return size;
}
''' + patched + r'''
int main(void) {
 struct wr_test_file storage={1,0};
 RTMP_OS_FD fd=&storage;char buf[4];
 assert(RtmpOSFileRead(NULL,buf,4)==-1);
 assert(RtmpOSFileRead((RTMP_OS_FD)(intptr_t)-2,buf,4)==-1);
 assert(RtmpOSFileRead((RTMP_OS_FD)(intptr_t)-4095,buf,4)==-1);
 assert(calls==0);assert(RtmpOSFileRead(fd,buf,4)==4);assert(calls==1);
 fd->f_mode=0;assert(RtmpOSFileRead(fd,buf,4)==-1);assert(calls==1);
 puts("PASS MT76x2 emitted guard: null, ERR_PTR, valid and unreadable handles");
 return 0;
}
''')
