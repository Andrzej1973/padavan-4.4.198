#!/usr/bin/env python3
"""Extract the patched RC implementation for isolated failure-path execution."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
patch = Path(__file__).resolve().parent.parent / 'overlay/padavan-4.4/patches/zram-service.diff'
lines = patch.read_text().splitlines()
start = lines.index('+#if defined(SUPPORT_ZRAM)')
end = lines.index('+#endif', start)
code = '\n'.join(line[1:] for line in lines[start + 1:end] if line.startswith('+'))
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/sysinfo.h>
static int active, loaded, mode, fail_read, fail_off, fail_unload;
static int fail_load, fail_write, fail_mkswap, fail_swapon, false_success;
static int formats, starts, unloads, logs;
static unsigned long long device_size;
static int mock_nvram(const char *name) { assert(!strcmp(name,"zram_enable")); return mode; }
static int mock_loaded(const char *name) { assert(!strcmp(name,"zram")); return loaded; }
static int mock_info(struct sysinfo *info) { memset(info,0,sizeof(*info)); info->totalram=128*1024*1024; info->mem_unit=1; return 0; }
static FILE *mock_open(const char *path,const char *access_mode) {
    FILE *fp;
    assert(!strcmp(access_mode,"r"));
    if (!strcmp(path,"/proc/swaps")) {
        if (fail_read) return NULL;
        fp=tmpfile(); assert(fp);
        fputs("Filename Type Size Used Priority\n",fp);
        if (active) fputs("/dev/zram0 partition 32768 0 32767\n",fp);
    } else {
        assert(!strcmp(path,"/sys/block/zram0/disksize"));
        fp=tmpfile(); assert(fp); fprintf(fp,"%llu\n",device_size);
    }
    rewind(fp); return fp;
}
static int mock_command(const char *command) {
    if (!strcmp(command,"swapoff /dev/zram0")) { if(fail_off)return 1; active=0; return 0; }
    if (!strcmp(command,"mkswap /dev/zram0")) { assert(!active); formats++; return fail_mkswap; }
    assert(!strcmp(command,"swapon -p 32767 -d /dev/zram0"));
    starts++; if(fail_swapon)return 1; if(!false_success)active=1; return 0;
}
static int mock_load(const char *name,const char *args) { assert(!strcmp(name,"zram")); assert(!strcmp(args,"num_devices=1")); if(!fail_load)loaded=1; return fail_load; }
static int mock_unload(const char *name,int recurse) { assert(!strcmp(name,"zram")); assert(recurse==1); assert(!active); unloads++; if(!fail_unload){loaded=0;device_size=0;} return fail_unload; }
static int mock_write(const char *path,int size) { assert(!strcmp(path,"/sys/block/zram0/disksize")); if(fail_write)return 1; device_size=size; return 0; }
static int mock_access(const char *path,int flags) { assert(!strcmp(path,"/sys/block/zram0/disksize")); assert(flags==W_OK); return loaded?0:-1; }
static unsigned mock_sleep(unsigned seconds) { (void)seconds; return 0; }
static void mock_log(const char *tag,const char *message) { assert(!strcmp(tag,"ZRAM")); assert(message && *message); logs++; }
#define nvram_get_int mock_nvram
#define sysinfo mock_info
/* Preserve the structure tag while replacing only the function call. */
#undef sysinfo
#define sysinfo(x) mock_info(x)
#define fopen mock_open
#define doSystem mock_command
#define is_module_loaded mock_loaded
#define module_smart_load mock_load
#define module_smart_unload mock_unload
#define fput_int mock_write
#define access mock_access
#define sleep mock_sleep
#define logmessage mock_log
'''
suffix = r'''
static void reset(void) {
    active=loaded=fail_read=fail_off=fail_unload=fail_load=fail_write=0;
    fail_mkswap=fail_swapon=false_success=formats=starts=unloads=logs=0;
    device_size=0; mode=1;
}
int main(void) {
    reset(); start_zram(); assert(active && formats==1 && starts==1);
    start_zram(); assert(formats==1 && starts==1);
    stop_zram(); assert(!active && !loaded);
    reset(); active=loaded=1; fail_off=1; restart_zram(); assert(active && !unloads && !formats && !starts);
    reset(); loaded=1; fail_unload=1; restart_zram(); assert(loaded && !formats && !starts);
    reset(); fail_read=1; start_zram(); assert(!loaded && !formats && !starts);
    reset(); fail_load=1; start_zram(); assert(!formats && !starts);
    reset(); fail_write=1; start_zram(); assert(!formats && !starts && !loaded);
    reset(); fail_mkswap=1; start_zram(); assert(formats==1 && !starts && !active && !loaded);
    reset(); fail_swapon=1; start_zram(); assert(starts==1 && !active && !loaded);
    reset(); false_success=1; start_zram(); assert(starts==1 && !active && !loaded && logs);
    reset(); mode=0; start_zram(); assert(!loaded && !formats);
    reset(); mode=2; start_zram(); assert(active && device_size==64*1024*1024);
    puts("PASS ZRAM lifecycle failure paths; mocked runtime, router activation unverified");
    return 0;
}
'''
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(prefix + code + suffix, encoding='utf-8')
