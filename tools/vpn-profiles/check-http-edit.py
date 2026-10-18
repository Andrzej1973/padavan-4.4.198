#!/usr/bin/env python3
"""Exercise authenticated revision-bound edit with a stdin-only fake manager."""
import argparse
import ast
import os
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-http-export.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets))
tests=r'''
static void submit(const char *token,const char *revision)
{
 char body[256];FILE *input=tmpfile();assert(input);
 int size=snprintf(body,sizeof(body),"%s\n2\n%s\nfixture\n",token,revision);
 assert(fwrite(body,1,(size_t)size,input)==(size_t)size);rewind(input);
 wr_vpn_edit_input("",input,size,NULL);fclose(input);wr_vpn_edit_output("",NULL);
 assert(!wr_vpn_edit_size);
 for(size_t i=0;i<sizeof(wr_vpn_edit_body);i++)assert(!wr_vpn_edit_body[i]);
}
int main(void)
{
 const char *token="0123456789abcdef0123456789abcdef";
 safe=0;post=1;submit(token,"1");assert(strstr(reply,"unsafe_request"));
 safe=1;post=0;submit(token,"1");assert(strstr(reply,"unsafe_request"));
 post=1;strcpy(wr_vpn_csrf,token);
 submit("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","1");assert(strstr(reply,"invalid_request"));
 submit(token,"01");assert(strstr(reply,"invalid_request"));
 submit(token,"1");assert(strstr(reply,"\"saved\":true,\"started\":false"));
 submit(token,"2");assert(strstr(reply,"edit_unconfirmed"));
 puts("PASS HTTP edit auth, CSRF, canonical revision, stale refusal, stdin-only config and buffer clearing");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wrvpn-http-edit-') as temporary:
 root=Path(temporary);fake=root/'manager'
 fake.write_text('''#!/bin/sh
test "$#" = 3 && test "$1" = edit && test "$2" = 2 || exit 9
test "$3" = 1 || exit 7
text=$(cat)
test "$text" = fixture || exit 2
printf 'saved\\t2\\t2\\n'
''');fake.chmod(0o700)
 source=root/'check.c'
 source.write_text(prefix+'#include "vpn-profiles.inc"\n#include "vpn-profiles-action.inc"\n#include "vpn-profiles-edit.inc"\n'+tests)
 exe=root/'check'
 subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-unused-function',
                 '-fsanitize=address,undefined','-I'+str(here/'web'),
                 '-DWR_VPN_PROFILE_BIN="%s"'%fake,str(source),'-o',str(exe)],check=True)
 result=subprocess.run([str(exe)],capture_output=True,timeout=20,
                       env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:exitcode=98',UBSAN_OPTIONS='halt_on_error=1:exitcode=97'))
 assert result.returncode==0,(result.returncode,result.stderr)
 print(result.stdout.decode().strip())
