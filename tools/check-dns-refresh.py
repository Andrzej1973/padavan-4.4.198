#!/usr/bin/env python3
"""Execute the emitted DNS refresh function with controlled browser/AJAX state."""
from pathlib import Path
import re
import subprocess
import sys
import uuid
import shutil
from contextlib import contextmanager

repo=Path(__file__).resolve().parent.parent
@contextmanager
def fixture_directory():
    directory=repo/('wr-dns-refresh-'+uuid.uuid4().hex);directory.mkdir()
    try:yield directory
    finally:
        assert directory.resolve().parent==repo.resolve()
        shutil.rmtree(directory)
with fixture_directory() as directory:
    root=Path(directory);user=root/'trunk/user'
    assert root.resolve().is_relative_to(repo.resolve())
    (user/'httpd').mkdir(parents=True)
    (user/'httpd/web_ex.c').write_text('struct ej_handler ej_handlers[] =\n{\n\t{ "json_system_status", ej_system_status_hook},\n};\n',encoding='utf-8')
    pages=user/'www/n56u_ribbon_fixed';pages.mkdir(parents=True)
    dictionaries=user/'www/dict';dictionaries.mkdir()
    for name in ('EN.footer','UK.dict','RU.dict'):(dictionaries/name).write_text('',encoding='utf-8')
    for port,page in [('stubby','Advanced_Services_DoT.asp'),('doh','Advanced_Services_DoH.asp')]:
        (pages/page).write_bytes((repo/'overlay/padavan-4.4/ports'/port/page).read_bytes())
    subprocess.run([sys.executable,str(repo/'tools/prepare-dns-process-status.py'),str(root)],check=True)
    for page,service in [('Advanced_Services_DoT.asp','stubby'),('Advanced_Services_DoH.asp','doh')]:
        html=(pages/page).read_text(encoding='utf-8')
        function=re.search(r'var wrDNSBusy=false;[\s\S]*?(?=function initial)',html)
        assert function and html.count('window.setInterval(wrDNSRefresh,30000)')==1
        assert 'onclick="wrDNSRefresh()"' in html
        test=r'''
const assert=require('assert');
var listeners={},timers=[],now=1000;
var document={hidden:false,addEventListener:function(name,callback){listeners[name]=callback;}},requests=0,display='',handlers={},lastOptions;
var window={setTimeout:function(callback,delay){assert.strictEqual(delay,45000);timers.push(callback);}};
Date.now=function(){return now;};
var instanceDisplay='';
function $j(selector){assert(['#wr_dns_process_status','#wr_doh_instances'].includes(selector));return {text:function(value){if(selector==='#wr_dns_process_status')display=value;else instanceDisplay=value;}};}
$j.ajax=function(options){requests++;lastOptions=options;handlers={};
 return {done:function(callback){handlers.done=callback;return this;},
 fail:function(callback){handlers.fail=callback;return this;},
 always:function(callback){handlers.always=callback;return this;}};};
'''+function[0]+'\nvar service='+repr(service)+';\n'+r'''
wrDNSRefresh();assert.strictEqual(requests,1);assert.strictEqual(lastOptions.timeout,5000);
assert.strictEqual(lastOptions.data.output,service==='doh'?'wr_doh_instance_state':'wr_dns_process_state');
assert.strictEqual(lastOptions.dataType,'json');assert.strictEqual(lastOptions.cache,false);
wrDNSRefresh();assert.strictEqual(requests,1);
var present=service==='doh'?{state:1,requested:1,configuredMask:3,ownedMask:1,unknownMask:0,duplicateMask:0}:1;
handlers.done(present);assert.strictEqual(display,'<#WRDNSPresent#>');handlers.always();
if(service==='doh'){assert(instanceDisplay.includes('<#WRDNSMissingSlots#>: 2'));assert.strictEqual(lastOptions.data.arg0,undefined);}
document.hidden=true;wrDNSRefresh();assert.strictEqual(requests,1);
document.hidden=false;wrDNSRefresh();assert.strictEqual(requests,2);
handlers.fail();assert.strictEqual(display,'<#WRDNSUnknown#>');handlers.always();
wrDNSRefresh();handlers.done('1');assert.strictEqual(display,'<#WRDNSUnknown#>');handlers.always();
wrDNSRefresh();handlers.done(service==='doh'?{state:0,requested:0,configuredMask:3,ownedMask:0,unknownMask:0,duplicateMask:0}:0);assert.strictEqual(display,'<#WRDNSOff#>');handlers.always();
if(service==='stubby')assert.strictEqual(lastOptions.data.arg0,'stubby');
wrDNSRender(present);var older=timers[timers.length-1];wrDNSRender(present);older();
assert.strictEqual(display,'<#WRDNSPresent#>');
timers[timers.length-1]();assert.strictEqual(display,'<#WRDNSUnknown#>');
if(service==='doh')assert.strictEqual(instanceDisplay,'<#WRDNSUnknown#>');
wrDNSRender(present);now+=45001;listeners.visibilitychange();assert.strictEqual(display,'<#WRDNSUnknown#>');
if(service==='doh'){
 for(const invalid of [null,{},present, {...present,ownedMask:16},{...present,ownedMask:1,unknownMask:1},{...present,duplicateMask:2}]){
  if(invalid===present)continue;
  wrDNSRefresh();handlers.done(invalid);assert.strictEqual(display,'<#WRDNSUnknown#>');assert.strictEqual(instanceDisplay,'<#WRDNSUnknown#>');handlers.always();
 }
 wrDNSRefresh();handlers.done({...present,ownedMask:5,unknownMask:2,duplicateMask:2});assert(instanceDisplay.includes('<#WRDNSUnexpectedSlots#>: 3'));assert(instanceDisplay.includes('<#WRDNSDuplicateSlots#>: 2'));handlers.always();
}
'''
        script=root/(service+'-refresh.js');script.write_text(test,encoding='utf-8')
        subprocess.run(['node',str(script)],check=True)
print('PASS emitted DoT/DoH refresh: hidden page, concurrent request, errors and runtime state')
