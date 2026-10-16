#!/usr/bin/env python3
"""Execute the generated status JS with bounded transport mocks."""
import ast
from pathlib import Path
import subprocess

source = Path('overlay/padavan-4.4/ports/zerotier/localize-ui-page.py')
tree = ast.parse(source.read_text(encoding='utf-8'))
values = {node.targets[0].id: ast.literal_eval(node.value)
          for node in tree.body if isinstance(node, ast.Assign)
          and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in ('JS_BLOCK', 'BACKEND_CODE')}
assert 'status.st_mtime > now' in values['BACKEND_CODE']
assert '!S_ISREG(status.st_mode)' in values['BACKEND_CODE']
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
 response=result;wrZerotierRefresh();assert.ok(output['#zerotier_status'].includes('<#'+label+'#>'));
 assert.ok(!output['#zerotier_status'].includes('<#Running#>'));assert.equal(wrZerotierBusy,false);
}
failure=true;wrZerotierRefresh();assert.ok(output['#zerotier_status'].includes('ZT_Unknown'));
const previous=requests;document.hidden=true;wrZerotierRefresh();assert.equal(requests,previous);
document.hidden=false;wrZerotierBusy=true;wrZerotierRefresh();assert.equal(requests,previous);
console.log('PASS ZeroTier cache labels, schema, failure, hidden-tab and single-flight behavior');
'''
subprocess.run(['node', '-'], input=harness + values['JS_BLOCK'] + cases,
               text=True, check=True)
