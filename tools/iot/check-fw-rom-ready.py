#!/usr/bin/env python3
"""Execute the generated Method1 ROM timeout branch; host control-flow only."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('driver', type=Path)
args = parser.parse_args()
source = (args.driver / 'mcu/andes_mt.c').read_text()
start = source.index('static NDIS_STATUS AndesMTLoadFwMethod1(')
end = source.index('static NDIS_STATUS AndesMTLoadFwMethod2(', start)
body = source[start:end]
start = body.index('\tif (loop > 500) {')
end = body.index('\n\t}', start) + len('\n\t}')
branch = body[start:end]
fixture = r'''
#include <assert.h>
#define NDIS_STATUS_FAILURE 1
#define FW_NO_INIT 0
#define DBGPRINT(level, args) ((void)0)
static int run(unsigned int loop, int ret, int *stage, int *cleanup) {
 struct { int Stage; } storage = {*stage}, *Ctl = &storage;
''' + branch + r'''
done:
 ++*cleanup;
 *stage = Ctl->Stage;
 return ret;
}
int main(void) {
 int stage, cleanup;
 stage=9; cleanup=0;
 assert(run(501,0,&stage,&cleanup)==NDIS_STATUS_FAILURE);
 assert(stage==FW_NO_INIT && cleanup==1);
 stage=9; cleanup=0;
 assert(run(501,7,&stage,&cleanup)==NDIS_STATUS_FAILURE);
 assert(stage==FW_NO_INIT && cleanup==1);
 stage=9; cleanup=0;
 assert(run(500,0,&stage,&cleanup)==0 && stage==9 && cleanup==1);
 stage=9; cleanup=0;
 assert(run(0,7,&stage,&cleanup)==7 && stage==9 && cleanup==1);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rom-ready-') as temporary:
    root = Path(temporary)
    (root / 'check.c').write_text(fixture)
    subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    str(root / 'check.c'), '-o', str(root / 'check')], check=True)
    subprocess.run([str(root / 'check')], check=True)
print('PASS generated ROM timeout: failure, stage invalidation, done path; non-timeout unchanged')
