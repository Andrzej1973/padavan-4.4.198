#!/usr/bin/env python3
"""Compile actual RC mode adapter against injected existing RC query functions."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-rc-mode-') as d:
 root=Path(d)
 (root/'rc.h').write_text('int get_ap_mode(void);\nint get_enabled_radio_rt(void);\nint is_radio_on_rt(void);\nint get_mode_radio_rt(void);\n')
 fixture=root/'check.c'
 fixture.write_text(r'''
#include <assert.h>
#include <fcntl.h>
#include <string.h>
#include "rc-backend.h"
static int held=1,ap,enabled=1,on=1,mode,queries;
int wr_iot_service_guard_dup(void){return held?open("/dev/null",O_RDONLY):-1;}
int get_ap_mode(void){queries++;return ap;}
int get_enabled_radio_rt(void){queries++;return enabled;}
int is_radio_on_rt(void){queries++;return on;}
int get_mode_radio_rt(void){queries++;return mode;}
int main(void){
 struct wr_iot_rc_mode result={9,9,9},before=result;
 held=0;assert(!wr_iot_rc_mode_read(&result)&&!queries&&!memcmp(&before,&result,sizeof(result)));
 held=1;assert(wr_iot_rc_mode_read(&result)&&result.router==1&&result.radio==1&&result.mode==0);
 ap=1;assert(wr_iot_rc_mode_read(&result)&&result.router==0);ap=0;
 enabled=0;assert(wr_iot_rc_mode_read(&result)&&result.radio==0);enabled=1;
 on=0;assert(wr_iot_rc_mode_read(&result)&&result.radio==0);on=1;
 for(mode=0;mode<=4;mode++)assert(wr_iot_rc_mode_read(&result)&&result.mode==mode);
 assert(!wr_iot_rc_mode_read(0));
 return 0;
}
''')
 binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(fixture),str(here/'rc-mode.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
print('PASS actual RC mode reader: held guard, unchanged output on refusal, AP/radio disabled and mode0..4; RC queries injected, no radio mutation')
