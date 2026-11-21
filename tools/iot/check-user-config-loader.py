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
filter_start = text.index('static int\nis_param_forbidden(')
filter_end = text.index('\nvoid\nload_user_config(', filter_start)
filter_function = text[filter_start:filter_end]
assert 'fprintf(fp, line)' not in function
prefix = '''#include <stdio.h>
#include <string.h>
#include <assert.h>
'''
main = '''
int main(int argc,char **argv){
 char result[2048];FILE *fp=tmpfile();assert(argc==3&&fp);
 const char *forbidden[]={"Protected=",NULL};
 load_user_config(fp,argv[1],"input.dat",forbidden);rewind(fp);
 size_t n=fread(result,1,sizeof(result)-1,fp);result[n]=0;
 assert(!strcmp(result,argv[2]));fclose(fp);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-user-config-') as temporary:
    root = Path(temporary)
    source = root/'check.c'
    source.write_text(prefix+filter_function+'\nvoid\n'+function+main)
    binary = root/'check'
    subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror', '-Wformat-security',
                    '-fsanitize=address,undefined', '-no-pie', str(source),
                    '-o', str(binary)], check=True)
    cases=[(value,value+'\n') for value in
           ['Example=%s%n%%\n','Example=last-character','Long='+'x'*700]]
    cases += [
        (marker+'x'*700+'\nAllowed=yes\n','Allowed=yes\n\n')
        for marker in ['#',';','Protected=']
    ]
    # Continuations that happen to begin like comments/forbidden keys remain
    # part of a permitted value, including at exact fgets chunk boundaries.
    for tail in ['#tail',';tail','Protected=tail']:
        value='Allowed='+'x'*(255-len('Allowed='))+tail+'\nNext=yes\n'
        cases.append((value,value+'\n'))
    cases += [('Protected='+'x'*700,'\n'),
              ('#'+'x'*254+'\nAllowed=yes','Allowed=yes\n')]
    for value,expected in cases:
        (root/'input.dat').write_text(value)
        subprocess.run([str(binary), temporary, expected], check=True)
print('PASS actual prepared user-config loader: literal/final/long values, whole-line comment and forbidden filtering, chunk-boundary continuations')
