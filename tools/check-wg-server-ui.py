#!/usr/bin/env python3
"""Check AWG server settings, validation and QR/export UI preparation."""
import argparse
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = args.source / "trunk/user"
page = (root / "www/n56u_ribbon_fixed/vpnsrv.asp").read_text()
defaults = (root / "shared/defaults.c").read_text()
variables = (root / "httpd/variables.c").read_text()
fields = ["jc", "jmin", "jmax", "s1", "s2", "h1", "h2", "h3", "h4"]

assert 'name="vpns_wg_protocol"' in page
assert "document.form.vpns_wg_protocol.value != 'wireguard' && found_app_awg() && !wrValidateAwgServer()" in page
for field in fields:
    name = "vpns_awg_" + field
    assert 'name="' + name + '"' in page, name + " input missing"
    assert '{ "' + name + '", "" }' in defaults, name + " default missing"
    assert '{"' + name + '", "", NULL, EVM_RESTART_VPNSVR}' in variables, name + " Apply event missing"
for lang in ("EN.footer", "UK.dict", "RU.dict"):
    dictionary = (root / "www/dict" / lang).read_text()
    assert len(re.findall(r"^WRWGServerInvalid=.+$", dictionary, re.M)) == 1

match = re.search(r"function wrValidateAwgServer\(\)\{.*?\n\}", page, re.S)
assert match, "AmneziaWG server validation missing"
node = ['const assert=require("assert");']
node.append("const validate=Function('document','alert'," + json.dumps("return (" + match.group(0) + ")()") + ");")
node.append('''function run(values){let message="";const document={form:{}};for(const key of ["jc","jmin","jmax","s1","s2","h1","h2","h3","h4"]){document.form["vpns_awg_"+key]={value:values[key]===undefined?"":String(values[key]),focus(){},select(){}};}return {ok:validate(document,x=>message=x),message};}
assert.strictEqual(run({}).ok,true);
assert.strictEqual(run({jc:4,jmin:16,jmax:64,s1:10,s2:20,h1:1,h2:2,h3:3,h4:4}).ok,true);
for(const values of [{jc:129},{jc:0},{jmin:16},{jmin:64,jmax:64},{s1:10,s2:66},{h1:7,h2:7},{jmax:1281}]){const result=run(values);assert.strictEqual(result.ok,false,JSON.stringify(values));assert.notStrictEqual(result.message,"");}
''')
subprocess.run(["node"], input="\n".join(node), text=True, check=True, timeout=15)

print("PASS AWG server fields/defaults/Apply, numeric and cross-field validation; host UI fixture only")
