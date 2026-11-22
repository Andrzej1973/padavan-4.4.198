#!/usr/bin/env python3
"""Compile actual literal RC startup fragment; verify registration/boot order."""
from pathlib import Path
import ast
import subprocess
import tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'prepare-runtime.py').read_text())
values=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='save_startup' for t in n.targets)]
assert len(values)==1
fragment=values[0]
with tempfile.TemporaryDirectory(prefix='wr-save-startup-') as directory:
 root=Path(directory)
 for board in (0,1):
  for boot in (0,1):
   for failure in (0,1,2) if board else (0,):
    source=root/'check.c';binary=root/'check'
    source.write_text('''#include <assert.h>
#include <string.h>
static int stage;
static void init_router(void){assert(stage==0);stage=1;}
#if defined(BOARD_WR1200JS)
static int wr_iot_rc_save_backend_install(void){assert(stage==1);stage=2;return 0;}
static int wr_iot_rc_edit_backend_install(void){assert(stage==2);stage=3;return FAILURE!=1;}
static int wr_iot_rc_view_runtime_install(void){assert(stage==3&&FAILURE!=1);stage=4;return FAILURE!=2;}
static int logged;
static void logmessage(const char *tag,const char *message){
 assert(!strcmp(tag,"IoT")&&!logged);
 assert(!strcmp(message,FAILURE==1?"Settings backend registration failed":
                                  "Settings read endpoint registration failed"));
 logged++;
}
#if WR_IOT_IAPP_POLICY_PREPARED
static void wr_iot_rc_boot_arm(void){assert(stage==(FAILURE==1?3:4));stage=5;}
#endif
#endif
int main(void){
'''+fragment+f'\nassert(stage=={5 if board and boot else (3 if failure==1 else 4) if board else 1});\n#if defined(BOARD_WR1200JS)\nassert(logged==(FAILURE!=0));\n#endif\nreturn 0;}}\n')
    flags=['-DFAILURE='+str(failure),'-DWR_IOT_IAPP_POLICY_PREPARED='+str(boot)]+(['-DBOARD_WR1200JS'] if board else [])
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=5)
print('PASS actual generated startup: init then Save/edit/view registration then optional boot arm; non-WR unchanged, unavailable registration does not block boot')
