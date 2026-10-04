#!/usr/bin/env python3
"""Stage explicit WebUI-managed ZeroTier network join/leave semantics.

Run after harden-zerotier-lifecycle.py. Service stop preserves memberships.
Only changing/clearing the configured Network ID removes a managed membership;
manually joined networks remain untouched. Not yet integrated into CI.
"""
import argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('source',type=Path)
args=parser.parse_args()
script=args.source/'trunk/user/zerotier/zerotier.sh'
text=script.read_text(encoding='utf-8')
old='''add_join() {
	# A blank Network ID is allowed for an enabled, not-yet-joined node.
	[ -z "$1" ] && return 0
	[ "${#1}" -eq 16 ] || return 1
	case "$1" in *[!0-9a-fA-F]*) return 1 ;; esac
	touch "$config_path/networks.d/$1.conf"
}'''
new='''valid_network_id() {
	[ "${#1}" -eq 16 ] || return 1
	case "$1" in *[!0-9a-fA-F]*) return 1 ;; esac
}
add_join() {
	desired_network="$1"
	if [ -n "$desired_network" ]; then
		valid_network_id "$desired_network" || return 1
		desired_network=$(printf '%s' "$desired_network" | tr 'A-F' 'a-f')
	fi
	managed_file="$config_path/web-managed-network"
	previous_network=""
	if [ -s "$managed_file" ]; then
		previous_network=$(cat "$managed_file")
		valid_network_id "$previous_network" || return 1
	fi
	if [ -n "$desired_network" ]; then
		touch "$config_path/networks.d/$desired_network.conf" || return 1
	fi
	if [ -n "$previous_network" ] && [ "$previous_network" != "$desired_network" ]; then
		# The service is stopped before this function: file removal is explicit leave.
		rm -f "$config_path/networks.d/$previous_network.conf" || return 1
	fi
	if [ -n "$desired_network" ]; then
		printf '%s\\n' "$desired_network" > "$managed_file.tmp" || return 1
		mv -f "$managed_file.tmp" "$managed_file"
	else
		rm -f "$managed_file"
	fi
}'''
if text.count(old)!=1:
    raise SystemExit('Managed network lifecycle anchor mismatch')
text=text.replace(old,new)
with script.open('w',encoding='utf-8',newline='\n') as out:
    out.write(text)
page=args.source/'trunk/user/www/n56u_ribbon_fixed/Advanced_zerotier.asp'
web=page.read_text(encoding='utf-8')
anchor='function applyRule(){\n//\tif(validForm()){'
replacement='''function leaveManagedNetwork() {
	if (!confirm('Leave the network configured on this page? Other manually joined networks will be preserved.')) return;
	document.form.zerotier_id.value = '';
	applyRule();
}
function applyRule(){
	var network = document.form.zerotier_id.value.replace(/^\\s+|\\s+$/g, '');
	if (network && !/^[0-9a-fA-F]{16}$/.test(network)) {
		alert('Network ID must contain exactly 16 hexadecimal characters.');
		document.form.zerotier_id.focus();
		return;
	}
	document.form.zerotier_id.value = network.toLowerCase();
'''
if web.count(anchor)!=1:
    raise SystemExit('WebUI apply anchor mismatch')
web=web.replace(anchor,replacement)
anchor='name="zerotier_id" id="zerotier_id" style="width: 200px"'
if web.count(anchor)!=1:
    raise SystemExit('Network ID input anchor mismatch')
web=web.replace(anchor,anchor+' maxlength="16"')
anchor='<% nvram_get_x("","zerotier_id"); %>" />'
if web.count(anchor)!=1:
    raise SystemExit('Network ID control anchor mismatch')
web=web.replace(anchor,anchor+'''<button type="button" class="btn" onclick="leaveManagedNetwork()">Leave network</button>
<p>Enter a Network ID and Apply to join. Authorize the router in ZeroTier Central. Disabling the service preserves membership.</p>''')
# Backend restart descriptors and reset defaults for separate permissions.
defaults_path=args.source/'trunk/user/shared/defaults.c'
defaults=defaults_path.read_text(encoding='utf-8')
anchor='\t{ "zerotier_nat", "1" },\n'
if defaults.count(anchor)!=1:
    raise SystemExit('ZeroTier default anchor mismatch')
defaults=defaults.replace(anchor,anchor+'\t{ "zerotier_router_access", "0" },\n\t{ "zerotier_lan_access", "0" },\n')
variables_path=args.source/'trunk/user/httpd/variables.c'
variables=variables_path.read_text(encoding='utf-8')
anchor='\t\t\t{"zerotier_nat", "", NULL, EVM_RESTART_ZEROTIER},\n'
if variables.count(anchor)!=1:
    raise SystemExit('ZeroTier HTTP variable anchor mismatch')
variables=variables.replace(anchor,anchor+'\t\t\t{"zerotier_router_access", "", NULL, EVM_RESTART_ZEROTIER},\n\t\t\t{"zerotier_lan_access", "", NULL, EVM_RESTART_ZEROTIER},\n')
rows=[]
for key,label,help_text in [
    ('zerotier_router_access','Allow access to this router','Allow ZeroTier members to reach router services, including its web interface and SSH.'),
    ('zerotier_lan_access','Allow access to LAN','Allow forwarding between ZeroTier members and LAN devices. Configure the LAN route in ZeroTier Central; this does not grant access to WAN or other VPNs.'),
]:
    rows.append('<tr><th>'+label+'</th><td><select name="'+key+'">'
        '<option value="0" <% nvram_match_x("","'+key+'","0","selected"); %>>Off</option>'
        '<option value="1" <% nvram_match_x("","'+key+'","1","selected"); %>>On</option>'
        '</select><p>'+help_text+'</p></td></tr>')
anchor='<tr> <th width="30%" style="border-top: 0 none;">允许客户端NAT</th>'
if web.count(anchor)!=1:
    raise SystemExit('ZeroTier permission table anchor mismatch')
web=web.replace(anchor,'\n'.join(rows)+'\n'+anchor)
for target,content in [(defaults_path,defaults),(variables_path,variables)]:
    with target.open('w',encoding='utf-8',newline='\n') as out:
        out.write(content)
with page.open('w',encoding='utf-8',newline='\n') as out:
    out.write(web)
print('Staged managed join/leave lifecycle and WebUI controls.')
