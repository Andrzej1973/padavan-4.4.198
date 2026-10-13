#!/usr/bin/env python3
"""Exercise emitted ZRAM refresh with browser and capability fixtures."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

repo=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='wr-zram-refresh-',dir=repo) as directory:
    root=Path(directory);assert root.resolve().is_relative_to(repo.resolve())
    user=root/'trunk/user';(user/'httpd').mkdir(parents=True)
    (user/'httpd/web_ex.c').write_text('struct ej_handler ej_handlers[] =\n{\n\t{ "json_system_status", ej_system_status_hook},\n};\n',encoding='utf-8')
    www=user/'www/n56u_ribbon_fixed';www.mkdir(parents=True)
    page=www/'Advanced_System_Content.asp'
    page.write_text('function initial(){\n\tif (!found_support_zram()) showhide_div("row_zram", 0);\n}\n<select name="zram_enable" class="input">',encoding='utf-8')
    dictionaries=user/'www/dict';dictionaries.mkdir()
    for name in ('EN.footer','UK.dict','RU.dict'):(dictionaries/name).write_text('',encoding='utf-8')
    subprocess.run([sys.executable,str(repo/'tools/prepare-zram-status-web.py'),str(root)],check=True)
    html=page.read_text(encoding='utf-8')
    function=re.search(r'var wrZramBusy=false;[\s\S]*?(?=function initial)',html)
    assert function and html.count('window.setInterval(wrZramRefresh,30000)')==1
    assert 'onclick="wrZramRefresh()"' in html
    test=r'''
const assert=require('assert');
var document={hidden:false},supported=true,requests=0,display='',handlers={},options;
function found_support_zram(){return supported;}
function $j(selector){assert.strictEqual(selector,'#wr_zram_status');return {text:function(value){display=value;}};}
$j.ajax=function(value){requests++;options=value;handlers={};return {
 done:function(callback){handlers.done=callback;return this;},
 fail:function(callback){handlers.fail=callback;return this;},
 always:function(callback){handlers.always=callback;return this;}};};
'''+function[0]+r'''
supported=false;wrZramRefresh();assert.strictEqual(requests,0);
supported=true;document.hidden=true;wrZramRefresh();assert.strictEqual(requests,0);
document.hidden=false;wrZramRefresh();assert.strictEqual(requests,1);
assert.strictEqual(options.data.output,'wr_zram_state');assert.strictEqual(options.timeout,5000);
assert.strictEqual(options.dataType,'json');assert.strictEqual(options.cache,false);
wrZramRefresh();assert.strictEqual(requests,1);
handlers.done(1);assert.strictEqual(display,'<#WRZramActive#>');handlers.always();
wrZramRefresh();handlers.fail();assert.strictEqual(display,'<#WRZramUnknown#>');handlers.always();
wrZramRefresh();handlers.done(4);assert.strictEqual(display,'<#WRZramStillActive#>');handlers.always();
wrZramRefresh();handlers.done('1');assert.strictEqual(display,'<#WRZramUnknown#>');handlers.always();
'''
    script=root/'refresh.js';script.write_text(test,encoding='utf-8')
    subprocess.run(['node',str(script)],check=True)
print('PASS emitted ZRAM refresh: capability, hidden page, concurrent requests and unknown state')
