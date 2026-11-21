#!/usr/bin/env python3
"""Pass actual generated Modern request bytes through native IoT HTTP readers."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#include <string.h>
#include "http-edit-request.h"
#include "http-view-request.h"
int main(int argc,char **argv){
 struct wr_iot_config_edit_record record={0};enum wr_iot_config_edit_mode mode;
 if(argc!=5)return 2;
 if(!strcmp(argv[1],"/wr_iot_view.cgi"))return
  !wr_iot_http_view_request_read(1,"POST",argv[2],argv[4],argv[3],strlen(argv[3]));
 if(!strcmp(argv[1],"/wr_iot_edit_ram.cgi"))mode=WR_IOT_EDIT_RAM;
 else if(!strcmp(argv[1],"/wr_iot_edit_auto.cgi"))mode=WR_IOT_EDIT_AUTO;
 else if(!strcmp(argv[1],"/wr_iot_edit_save.cgi"))mode=WR_IOT_EDIT_EXPLICIT;
 else if(!strcmp(argv[1],"/wr_iot_edit_runtime.cgi"))mode=WR_IOT_EDIT_RUNTIME;
 else return 3;
 return !wr_iot_http_edit_request_read(&record,1,"POST",argv[2],argv[4],argv[3],strlen(argv[3]),mode);
}
'''
with tempfile.TemporaryDirectory(prefix='modern-iot-native-') as td:
 root=Path(td);c=root/'check.c';exe=root/'check';js=root/'modern-iot.js'
 c.write_text(body);js.write_text(runpy.run_path(str(here/'prepare-modern-iot.py'))['asset']())
 subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here.parent/'iot'),str(c),'-o',str(exe)],check=True)
 token='a'*32;form='token='+token
 assert subprocess.run([str(exe),'/wr_iot_view.cgi','application/x-www-form-urlencoded;charset=UTF-8',form,token]).returncode==1
 assert subprocess.run([str(exe),'/wr_iot_view.cgi','application/x-www-form-urlencoded',form,'b'*32]).returncode==1
 subprocess.run(['node',str(here/'check_modern_iot.js'),str(js),str(exe)],check=True)
print('PASS generated Modern IoT -> native HTTP readers: actual content-type and encoded body for view and four edit routes; RC result/persistence remains simulated')
