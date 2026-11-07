#!/usr/bin/env python3
"""Execute the actual prepared RC loader with literal/unterminated inputs."""
import argparse
import subprocess
import tempfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
text = (a.source/'trunk/user/rc/common_ex.c').read_text()
start = text.index('load_user_config(FILE *fp,')
end = text.index('\nint\nis_module_loaded', start)
function = text[start:end]
assert 'fprintf(fp, line)' not in function
prefix = '''#include <stdio.h>
#include <string.h>
#include <assert.h>
static int is_param_forbidden(const char *a,const char **b){(void)a;(void)b;return 0;}
void
'''
main = '''
int main(int argc,char **argv){
 char result[2048];FILE *fp=tmpfile();assert(argc==3&&fp);
 load_user_config(fp,argv[1],"input.dat",NULL);rewind(fp);
 size_t n=fread(result,1,sizeof(result)-1,fp);result[n]=0;
 assert(!strcmp(result,argv[2]));fclose(fp);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-user-config-') as temporary:
    root = Path(temporary)
    source = root/'check.c'
    source.write_text(prefix+function+main)
    binary = root/'check'
    subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror', '-Wformat-security',
                    '-fsanitize=address,undefined', '-no-pie', str(source),
                    '-o', str(binary)], check=True)
    for value in ['Example=%s%n%%\n', 'Example=last-character', 'Long='+'x'*700]:
        (root/'input.dat').write_text(value)
        subprocess.run([str(binary), temporary, value+'\n'], check=True)
print('PASS actual prepared user-config loader: literal percent and complete final/long values')
