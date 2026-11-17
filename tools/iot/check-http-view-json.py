from pathlib import Path
import json
import subprocess
import tempfile
here=Path(__file__).resolve().parent
body=r'''
#include "config-view-json.h"
#include "http-view-request.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 struct wr_iot_config_view view={.enabled=0,.key_present=1,.gateway="192.168.50.1",
 .mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};
 const char revision[33]="ffffffffffffffffffffffffffffffff";
 const char token[33]="0123456789abcdef0123456789abcdef";
 const char request[]="token=0123456789abcdef0123456789abcdef";
 char output[WR_IOT_VIEW_JSON_MAX],small[2]={'x','y'};
 strcpy(view.ssid,"IoT \"</script>&\\");
 assert(wr_iot_config_view_json(output,sizeof(output),&view,revision)>0);puts(output);
 memset(view.ssid,0,sizeof(view.ssid));strcpy(view.ssid,"Мережа IoT");
 assert(wr_iot_config_view_json(output,sizeof(output),&view,revision)>0);puts(output);
 memset(view.ssid,'<',32);view.ssid[32]=0;
 assert(wr_iot_config_view_json(output,sizeof(output),&view,revision)>0);puts(output);
 assert(!wr_iot_config_view_json(small,sizeof(small),&view,revision)&&small[0]=='x'&&small[1]=='y');
 memset(&view,0,sizeof(view));
 assert(wr_iot_config_view_json(output,sizeof(output),&view,revision)>0);puts(output);
 view.enabled=1;assert(!wr_iot_config_view_json(small,sizeof(small),&view,revision)&&small[0]=='x');
 assert(wr_iot_http_view_request_read(1,"POST","application/x-www-form-urlencoded",token,request,sizeof(request)-1));
 for(size_t length=0;length<sizeof(request)-1;length++)assert(!wr_iot_http_view_request_read(1,"POST","application/x-www-form-urlencoded",token,request,length));
 assert(!wr_iot_http_view_request_read(0,"POST","application/x-www-form-urlencoded",token,request,sizeof(request)-1));
 assert(!wr_iot_http_view_request_read(1,"GET","application/x-www-form-urlencoded",token,request,sizeof(request)-1));
 assert(!wr_iot_http_view_request_read(1,"POST","application/json",token,request,sizeof(request)-1));
 assert(!wr_iot_http_view_request_read(1,"POST","application/x-www-form-urlencoded",revision,request,sizeof(request)-1));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-view-json-') as directory:
 root=Path(directory);source=root/'check.c';source.write_text(body);binary=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(source),'-o',str(binary)],check=True)
 result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=10)
 records=[json.loads(line) for line in result.stdout.splitlines()]
 assert [record['ssid'] for record in records]==['IoT "</script>&\\','Мережа IoT','<'*32,'']
 expected={'revision','configured','enabled','key_present','ssid','gateway','mask','first','last'}
 assert all(set(record)==expected for record in records)
 assert all(not record['enabled'] for record in records)
 assert [record['configured'] for record in records]==[True,True,True,False]
 assert '<' not in result.stdout and '&' not in result.stdout
print('PASS view JSON parsed independently: escaped metacharacters, UTF-8, maximum SSID, absent profile, exact public schema and guarded token-only POST; no credentials')
