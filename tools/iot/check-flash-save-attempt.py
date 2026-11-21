#!/usr/bin/env python3
"""Execute actual child-only journal with deterministic native adapter actors."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
fields=[b'0',b'IoT test',b'password123',b'192.168.50.1',b'255.255.255.0',b'192.168.50.20',b'192.168.50.200']
record='WR-IOT-CONFIG-1:'+':'.join(v.hex() for v in fields)
source=r'''
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include "flash-save-attempt.h"
static pid_t fixture_pid=123;
static pid_t fixture_getpid(void){return fixture_pid;}
#define getpid fixture_getpid
#include "flash-save-attempt.c"
static int manual,snapshots,fail_snapshot,commits,commit_result,flash_reads;
static enum wr_iot_flash_config_result flash_first,flash_next;
int wr_iot_flash_save_snapshot(const char *record,int *out){
 assert(record&&strstr(record,"WR-IOT-CONFIG-1:")==record);snapshots++;
 if(snapshots==fail_snapshot)return 0;
 *out=manual;return 1;
}
int wr_iot_flash_save_commit_once(const char *record,size_t n,enum wr_iot_flash_save_mode mode){assert(strlen(record)==n&&(mode==1||mode==2));commits++;return commit_result;}
enum wr_iot_flash_config_result wr_iot_native_flash_compare(const char *record,size_t n){
 assert(strlen(record)==n);return ++flash_reads==1?flash_first:flash_next;
}
static const char id[]="0123456789abcdef0123456789abcdef";
static const char expected[]="RECORD";
static void reset(void){
 fixture_pid=123;manual=snapshots=fail_snapshot=commits=commit_result=flash_reads=0;
 flash_first=WR_IOT_FLASH_CONFIG_DIFFERENT;flash_next=WR_IOT_FLASH_CONFIG_MATCH;
}
static void begin(struct wr_iot_flash_save_attempt *a,int explicit){
 memset(a,0,sizeof(*a));assert(wr_iot_flash_save_begin(a,id,7,
 explicit?WR_IOT_FLASH_SAVE_EXPLICIT:WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
}
static enum wr_iot_flash_save_phase step(struct wr_iot_flash_save_attempt *a){return wr_iot_flash_save_step(a,id,7);}
int main(void){
 struct wr_iot_flash_save_attempt a={0},copy;
 reset();fixture_pid=1;assert(!wr_iot_flash_save_begin(&a,id,7,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(!a.owner&&!snapshots&&!commits);
 reset();begin(&a,0);copy=a;assert(step(&copy)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!snapshots);
 fixture_pid=124;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!snapshots);fixture_pid=123;
 assert(wr_iot_flash_save_step(&a,id,8)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!snapshots);
 reset();manual=1;begin(&a,0);assert(step(&a)==WR_IOT_FLASH_SAVE_MANUAL_PENDING&&!commits&&!flash_reads);
 manual=0;flash_next=WR_IOT_FLASH_CONFIG_DIFFERENT;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 reset();manual=1;begin(&a,1);assert(step(&a)==WR_IOT_FLASH_SAVE_OBSERVED&&commits==1&&flash_reads==2);
 reset();begin(&a,0);commit_result=-1;flash_next=WR_IOT_FLASH_CONFIG_DIFFERENT;
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1&&a.attempted);
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 flash_next=WR_IOT_FLASH_CONFIG_MATCH;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 flash_next=WR_IOT_FLASH_CONFIG_DIFFERENT;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 reset();begin(&a,0);flash_first=WR_IOT_FLASH_CONFIG_MATCH;
 assert(step(&a)==WR_IOT_FLASH_SAVE_OBSERVED&&!commits);
 flash_next=WR_IOT_FLASH_CONFIG_DIFFERENT;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 reset();begin(&a,0);flash_first=WR_IOT_FLASH_CONFIG_INVALID;
 assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 flash_next=WR_IOT_FLASH_CONFIG_DIFFERENT;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 flash_next=WR_IOT_FLASH_CONFIG_MATCH;assert(step(&a)==WR_IOT_FLASH_SAVE_OBSERVED&&commits==1);
 reset();begin(&a,0);fail_snapshot=2;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&!commits);
 fail_snapshot=0;assert(step(&a)==WR_IOT_FLASH_SAVE_OBSERVED&&!commits);
 reset();begin(&a,0);fail_snapshot=3;assert(step(&a)==WR_IOT_FLASH_SAVE_UNCERTAIN&&commits==1);
 fail_snapshot=0;assert(step(&a)==WR_IOT_FLASH_SAVE_OBSERVED&&commits==1);
 return 0;
}
'''.replace('RECORD',record)
with tempfile.TemporaryDirectory(prefix='wr-flash-attempt-') as directory:
    root=Path(directory);cfile=root/'check.c';binary=root/'check';cfile.write_text(source)
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
                    str(cfile),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual journal: non-PID1/PID/address/request binding, AUTO manual skip, explicit Save, single commit, read-only uncertainty/drift recovery and current-record checks; native adapters modeled')
