#!/usr/bin/env python3
"""Regression checks for the USB/IP runtime status integration."""
import subprocess
import re
import sys
import uuid
from pathlib import Path


repo = Path(__file__).resolve().parents[1]
stage = repo / ("usbip-status-check-" + uuid.uuid4().hex)
user = stage / "trunk/user"
(user / "httpd").mkdir(parents=True)
(user / "www/n56u_ribbon_fixed").mkdir(parents=True)
(user / "www/dict").mkdir(parents=True)

try:
    (user / "httpd/web_ex.c").write_text(
        '#include <errno.h>\n#include <sys/stat.h>\n'
        'struct ej_handler ej_handlers[] =\n{\n'
        '\t{ "json_system_status", ej_system_status_hook},\n};\n', encoding="utf-8"
    )
    page = '''<script>function initial(){
\tvar id_menu = 5;
}</script>
<table>
                                        <tr>
                                            <td colspan="2">
                                                <center><input class="btn btn-primary" type="button"></center>
                                            </td>
                                        </tr>
</table>'''
    (user / "www/n56u_ribbon_fixed/Advanced_Printer_others.asp").write_text(page, encoding="utf-8")
    for name in ("EN.footer", "UK.dict", "RU.dict"):
        (user / "www/dict" / name).write_text("Existing=value\n", encoding="utf-8")

    config = stage / "profile.config"
    config.write_text("# CONFIG_FIRMWARE_INCLUDE_USBIP=y\n", encoding="utf-8")
    command = [sys.executable, str(repo / "tools/prepare-usbip-status.py"), str(stage),
               "--config", str(config)]
    before = {p: p.read_bytes() for p in user.rglob("*") if p.is_file()}
    subprocess.run(command, check=True)
    assert before == {p: p.read_bytes() for p in user.rglob("*") if p.is_file()}
    config.write_text("CONFIG_FIRMWARE_INCLUDE_USBIP=y\n", encoding="utf-8")
    subprocess.run(command, check=True)
    web = (user / "httpd/web_ex.c").read_text(encoding="utf-8")
    assert '"wr_usbip_state", ej_wr_usbip_state' in web
    assert 'stat("/sys/module", &st)' in web
    assert 'access("/sys/module", R_OK | X_OK)' in web
    for marker in ("/sys/module/usbip_core", "/sys/module/usbip_host",
                   "/sys/module/vhci_hcd", 'pids("usbipd")', 'argc != 0'):
        assert marker in web
    rendered = (user / "www/n56u_ribbon_fixed/Advanced_Printer_others.asp").read_text(encoding="utf-8")
    for marker in ("wr_usbip_core", "wr_usbip_host", "wr_usbip_vhci", "wr_usbip_daemon",
                   'output:"wr_usbip_state"', "document.hidden", "timeout:5000",
                   "setInterval(wrUSBIPRefresh, 30000)"):
        assert marker in rendered
    assert "Connectivity, exported devices" in (user / "www/dict/EN.footer").read_text(encoding="utf-8")
    assert "З’єднання, експортовані пристрої" in (user / "www/dict/UK.dict").read_text(encoding="utf-8")
    assert "Соединение, экспортированные устройства" in (user / "www/dict/RU.dict").read_text(encoding="utf-8")
    emitted = re.search(r'var wrUSBIPBusy = false;[\s\S]*?(?=function initial)', rendered)
    assert emitted
    browser_check = stage / "browser-check.js"
    browser_check.write_text(r'''
const assert = require('assert');
var document = {hidden:false}, requests=0, handlers={}, options, displayed={};
function $j(selector) { return {text:function(value) { displayed[selector]=value; }}; }
$j.ajax = function(value) {
 requests++; options=value; handlers={};
 return {done:function(fn){handlers.done=fn;return this;},
         fail:function(fn){handlers.fail=fn;return this;},
         always:function(fn){handlers.always=fn;return this;}};
};
''' + emitted[0] + r'''
const fields=['core','host','vhci','daemon'];
function allUnknown() {
 fields.forEach(k=>assert.strictEqual(displayed['#wr_usbip_'+k],'<#WRUSBIPUnknown#>'));
}
wrUSBIPRender({core:1,host:0,vhci:2,daemon:1});
assert.strictEqual(displayed['#wr_usbip_core'],'<#WRUSBIPLoaded#>');
assert.strictEqual(displayed['#wr_usbip_host'],'<#WRUSBIPNotLoaded#>');
assert.strictEqual(displayed['#wr_usbip_vhci'],'<#WRUSBIPUnknown#>');
assert.strictEqual(displayed['#wr_usbip_daemon'],'<#WRUSBIPRunning#>');
wrUSBIPRender({core:0,host:0,vhci:0,daemon:0});
assert.strictEqual(displayed['#wr_usbip_daemon'],'<#WRUSBIPStopped#>');
for(const bad of [null,{},[],{error:'invalid_request'},
 {core:1,host:1,vhci:1,daemon:'1'}, {core:1,host:1,vhci:1,daemon:3},
 {core:1,host:1,vhci:1,daemon:0.5}, {core:NaN,host:1,vhci:1,daemon:1}]) {
 wrUSBIPRender(bad); allUnknown();
}
document.hidden=true; wrUSBIPRefresh(); assert.strictEqual(requests,0);
document.hidden=false; wrUSBIPRefresh(); assert.strictEqual(requests,1);
assert.strictEqual(options.data.output,'wr_usbip_state');
assert.strictEqual(options.timeout,5000); assert.strictEqual(options.cache,false);
wrUSBIPRefresh(); assert.strictEqual(requests,1);
handlers.done({core:1,host:1,vhci:0,daemon:1}); handlers.always();
wrUSBIPRefresh(); assert.strictEqual(requests,2);
handlers.fail(); allUnknown(); handlers.always();
wrUSBIPRefresh(); handlers.done({core:1}); allUnknown(); handlers.always();
wrUSBIPRefresh(); handlers.done({core:1,host:1,vhci:1,daemon:0}); handlers.always();
assert.strictEqual(displayed['#wr_usbip_daemon'],'<#WRUSBIPStopped#>');
console.log('PASS emitted USB/IP rendering, malformed responses, hidden page, single request and recovery');
''', encoding="utf-8")
    subprocess.run(["node", str(browser_check)], check=True)
    duplicate = subprocess.run(command, text=True, capture_output=True)
    assert duplicate.returncode != 0 and "already present" in (duplicate.stdout + duplicate.stderr)
finally:
    if stage.exists():
        for path in sorted(stage.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        stage.rmdir()

print("USB/IP status integration checks passed")
