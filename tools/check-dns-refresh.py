#!/usr/bin/env python3
"""Execute the emitted DNS refresh function with controlled browser/AJAX state."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='wr-dns-refresh-',dir=repo) as directory:
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
var document={hidden:false},requests=0,display='',handlers={},lastOptions;
function $j(selector){assert.strictEqual(selector,'#wr_dns_process_status');return {text:function(value){display=value;}};}
$j.ajax=function(options){requests++;lastOptions=options;handlers={};
 return {done:function(callback){handlers.done=callback;return this;},
 fail:function(callback){handlers.fail=callback;return this;},
 always:function(callback){handlers.always=callback;return this;}};};
'''+function[0]+r'''
wrDNSRefresh();assert.strictEqual(requests,1);assert.strictEqual(lastOptions.timeout,5000);
assert.strictEqual(lastOptions.data.output,'wr_dns_process_state');
assert.strictEqual(lastOptions.dataType,'json');assert.strictEqual(lastOptions.cache,false);
wrDNSRefresh();assert.strictEqual(requests,1);
handlers.done(1);assert.strictEqual(display,'<#WRDNSPresent#>');handlers.always();
document.hidden=true;wrDNSRefresh();assert.strictEqual(requests,1);
document.hidden=false;wrDNSRefresh();assert.strictEqual(requests,2);
handlers.fail();assert.strictEqual(display,'<#WRDNSUnknown#>');handlers.always();
wrDNSRefresh();handlers.done('1');assert.strictEqual(display,'<#WRDNSUnknown#>');handlers.always();
wrDNSRefresh();handlers.done(0);assert.strictEqual(display,'<#WRDNSOff#>');handlers.always();
'''+"\nassert.strictEqual(lastOptions.data.arg0,"+repr(service)+");\n"
        script=root/(service+'-refresh.js');script.write_text(test,encoding='utf-8')
        subprocess.run(['node',str(script)],check=True)
print('PASS emitted DoT/DoH refresh: hidden page, concurrent request, errors and runtime state')
