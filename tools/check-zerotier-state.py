#!/usr/bin/env python3
"""Execute the generated status JS with bounded transport mocks."""
import ast
from pathlib import Path
import subprocess
import argparse
import json
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', help='Also compile and execute the generated C hook')
args = parser.parse_args()

source = Path('overlay/padavan-4.4/ports/zerotier/localize-ui-page.py')
tree = ast.parse(source.read_text(encoding='utf-8'))
values = {node.targets[0].id: ast.literal_eval(node.value)
          for node in tree.body if isinstance(node, ast.Assign)
          and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in ('JS_BLOCK', 'BACKEND_CODE')}
assert 'status.st_mtime > now' in values['BACKEND_CODE']
assert '!S_ISREG(status.st_mode)' in values['BACKEND_CODE']
assert 'fstat(fileno(cache)' in values['BACKEND_CODE']
assert 'count < 4096' in values['BACKEND_CODE']
harness = r'''
const assert = require('node:assert/strict');
const output = {};
let response, failure=false, requests=0;
const document={hidden:false};
function $j(selector){return {
 html(value){output[selector]=value;}, text(value){output[selector]=value;}
};}
$j.ajax=function(){requests++;return {
 done(fn){if(!failure)fn(response);return this;},
 fail(fn){if(failure)fn();return this;},always(fn){fn();return this;}
};};
'''
cases = r'''
for(const [result,label] of [
 [{state:0,age:-1},'ZT_Disabled'],[{state:1,age:0},'ZT_Updated'],
 [{state:1,age:60},'ZT_Updated'],[{state:2,age:61},'ZT_Stale'],
 [{state:3,age:-1},'ZT_Unknown'],[{state:1,age:61},'ZT_Unknown'],
 [{state:2,age:0},'ZT_Unknown'],[{state:1,age:'0'},'ZT_Unknown'],
 [{state:1.5,age:0},'ZT_Unknown'],[{state:4,age:0},'ZT_Unknown'],
 [{state:1,age:Infinity},'ZT_Unknown'],[null,'ZT_Unknown']]){
 response=result && Object.assign({text:'node snapshot <script>'},result);
 wrZerotierRefresh();assert.ok(output['#zerotier_status'].includes('<#'+label+'#>'));
 if(label==='ZT_Updated'||label==='ZT_Stale') assert.equal(output['#zerotier_cached_text'],'node snapshot <script>');
 else assert.equal(output['#zerotier_cached_text'],'<#ZT_Unavailable#>');
 assert.ok(!output['#zerotier_status'].includes('<#Running#>'));assert.equal(wrZerotierBusy,false);
}
failure=true;wrZerotierRefresh();assert.ok(output['#zerotier_status'].includes('ZT_Unknown'));
assert.equal(output['#zerotier_cached_text'],'<#ZT_Unavailable#>');
failure=false;response={state:1,age:0,text:'x'.repeat(4097)};wrZerotierRefresh();
assert.ok(output['#zerotier_status'].includes('ZT_Unknown'));
const previous=requests;document.hidden=true;wrZerotierRefresh();assert.equal(requests,previous);
document.hidden=false;wrZerotierBusy=true;wrZerotierRefresh();assert.equal(requests,previous);
console.log('PASS ZeroTier cache labels, schema, failure, hidden-tab and single-flight behavior');
'''
subprocess.run(['node', '-'], input=harness + values['JS_BLOCK'] + cases,
               text=True, check=True)

if args.cc:
    c = r'''
#include <stdio.h>
#include <stdarg.h>
#include <time.h>
#include <sys/stat.h>
#include <string.h>
typedef void *webs_t;
static int enabled=1, missing=0;
static time_t stamp=1000;
static const char *payload="node \"quoted\" \\ slash\nnext\tline";
static int nvram_get_int(const char *key){(void)key;return enabled;}
static time_t test_time(time_t *p){(void)p;return 1000;}
static FILE *test_open(const char *path,const char *mode){
 FILE *f;(void)path;(void)mode;if(missing)return NULL;
 f=tmpfile();if(!f)return NULL;fputs(payload,f);rewind(f);return f;
}
static int test_stat(int fd,struct stat *s){(void)fd;memset(s,0,sizeof(*s));s->st_mode=S_IFREG;s->st_mtime=stamp;return 0;}
static int websWrite(webs_t wp,const char *fmt,...){int n;va_list ap;(void)wp;va_start(ap,fmt);n=vprintf(fmt,ap);va_end(ap);return n;}
#define time test_time
#define fopen test_open
#define fstat test_stat
'''+values['BACKEND_CODE']+r'''
static void emit(void){ej_zerotier_state(0,NULL,0,NULL);putchar('\n');}
int main(void){
 char large[5001];
 emit();stamp=939;emit();stamp=1001;emit();missing=1;emit();
 enabled=0;emit();enabled=1;missing=0;stamp=1000;
 memset(large,'a',5000);large[5000]=0;payload=large;emit();return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='zt-state-') as tmp:
        source = Path(tmp)/'state.c'; binary = Path(tmp)/'state'
        source.write_text(c, encoding='utf-8')
        subprocess.run([args.cc,'-std=gnu99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True)
        rows = [json.loads(row) for row in subprocess.check_output([str(binary)],text=True).splitlines()]
    assert [row['state'] for row in rows] == [1,2,3,3,0,1]
    assert rows[0]['text'] == 'node "quoted" \\ slash\nnext\tline'
    assert all(rows[index]['text'] == '' for index in [2,3,4])
    assert len(rows[5]['text']) == 4096
    print('PASS generated C hook JSON escaping, freshness, unavailable, disabled and 4096-byte limit')
