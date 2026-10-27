#!/usr/bin/env python3
"""First BusyBox audit gate: exact-image identity, shell syntax and applet probes.

Does not run service lifecycle scripts or establish hardware/runtime acceptance.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
from target_busybox_service_map import (
    active_service_entrypoint_map_status,
    qos_image_gate_status,
    sfe_image_gate_status,
)
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('tree',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();trunk=a.tree/'trunk';root=(trunk/'romfs').resolve()
binary=root/'bin/busybox';config=trunk/'user/busybox/busybox-1.24.x/.config'
qemu=shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
if not qemu:raise SystemExit('Target QEMU is required')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,**options):
    return subprocess.run([qemu,'-L',str(root),str(binary),*args],
        capture_output=True,timeout=10,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},**options)
source=subprocess.run(['git','-C',str(a.tree.resolve()),'rev-parse','HEAD'],
    capture_output=True,text=True,env=dict(os.environ,LC_ALL='C'))
source_revision=source.stdout.strip() if source.returncode==0 else None
effective_busybox_config=[line for line in config.read_text().splitlines()
    if line.startswith('CONFIG_') or line.startswith('# CONFIG_')]
effective_firmware_config=[line for line in (trunk/'.config').read_text().splitlines()
    if line.startswith('CONFIG_FIRMWARE_INCLUDE_') or line.startswith('# CONFIG_FIRMWARE_INCLUDE_')]
report={'schema':2,'runtime_verified':False,'whole_service_audit_complete':False,
        'image_identity':{'model':'WR1200JS','firmware_source_revision':source_revision,
            'build_commit':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),
            'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'run_number':os.environ.get('GITHUB_RUN_NUMBER')},
        'busybox_sha256':digest(binary),'config_sha256':digest(config),
        'effective_busybox_config':effective_busybox_config,
        'effective_firmware_service_selectors':effective_firmware_config,
        'scope':'exact image BusyBox identity/config/applet links/ELF closure, shell syntax and bounded probes; selected invalid-action dispatch only; service interactions unverified',
        'scripts':[],'other_interpreters':[],'applet_links':[],'checks':{}}
report['checks']['firmware_source_revision_identified']=source_revision is not None
listing=run(['--list']);applets=listing.stdout.decode(errors='replace').splitlines()
report['applets']=applets;report['checks']['applet_inventory']=listing.returncode==0
version_output=run(['--help'])
version_text=(version_output.stdout+version_output.stderr).decode(errors='replace')
version=re.search(r'^BusyBox v([^\s]+)',version_text,re.MULTILINE)
report['busybox_version']=version.group(1) if version else None
report['checks']['busybox_version_identified']=version is not None
report['checks']['shell_type_builtin']=run(['sh','-c','type type >/dev/null 2>&1']).returncode==0
report['checks']['mwan_shell_arithmetic']=run(['sh','-c','i=1; count=$((i-1)); last=$i; j=$((i-1)); test "$count:$last:$j" = "0:1:0"']).returncode==0
report['command_builtin_available']=run(['sh','-c','type command >/dev/null 2>&1']).returncode==0
image_paths=set()
for directory,dirs,files in os.walk(root,followlinks=False):
    dirs[:]=sorted(name for name in dirs if not (Path(directory)/name).is_symlink())
    for name in sorted(files):
        path=Path(directory)/name
        image_paths.add(path.relative_to(root).as_posix())
        if path.is_symlink():
            target=os.readlink(path)
            resolved=Path(os.path.normpath(str(root/target.lstrip('/')) if target.startswith('/') else str(path.parent/target)))
            if resolved==binary:
                report['applet_links'].append({'path':path.relative_to(root).as_posix(),'target':target})
            continue
        if not path.is_file():continue
        with path.open('rb') as f:first=f.read(256).split(b'\n',1)[0]
        words=first.split()
        shell=bool(words) and (words[0] in (b'#!/bin/sh',b'#!/bin/ash') or words[:2]==[b'#!/usr/bin/env',b'sh'])
        if first.startswith(b'#!') and not shell:
            report['other_interpreters'].append(str(path.relative_to(root)));continue
        if not shell and path.suffix!='.sh':continue
        if len(report['scripts'])>=512:raise SystemExit('Shell inventory limit exceeded; audit incomplete')
        data=path.read_bytes()
        item={'path':str(path.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest(),
              'command_v_requires_review':b'command -v' in data and not report['command_builtin_available']}
        try:item['syntax_exit']=run(['sh','-n',str(path)]).returncode
        except subprocess.TimeoutExpired:item['syntax_exit']=None
        report['scripts'].append(item)
report['checks']['all_discovered_shell_syntax']=bool(report['scripts']) and all(
    item['syntax_exit']==0 for item in report['scripts'])
report['checks']['command_v_supported_or_avoided']=not any(
    item['command_v_requires_review'] for item in report['scripts'])
report['checks']['busybox_applet_links_recorded']=bool(report['applet_links'])
report['checks']['od_compact_config']=('CONFIG_OD=y' in effective_busybox_config and
    '# CONFIG_DESKTOP is not set' in effective_busybox_config)
report['checks']['od_applet_and_link']=('od' in applets and
    any(link['path']=='usr/bin/od' for link in report['applet_links']))
closure=None
try:
    readelf=shutil.which('readelf')
    if not readelf:raise RuntimeError('readelf is required to inspect the BusyBox loader/library closure')
    spec=importlib.util.spec_from_file_location('busybox_image_closure',Path(__file__).parent/'band-steering/verify-package-closure.py')
    closure=importlib.util.module_from_spec(spec);spec.loader.exec_module(closure)
    report['busybox_elf_dependency_closure']=closure.verify(root,root,readelf,['bin/busybox'])
    report['checks']['busybox_elf_dependency_closure']=True
except (OSError,RuntimeError,ValueError,subprocess.CalledProcessError) as error:
    closure=None
    report['busybox_elf_dependency_closure_error']=str(error)
    report['busybox_elf_dependency_closure']={}
    report['checks']['busybox_elf_dependency_closure']=False
# Non-shell Lua utilities have their own interpreter/module execution gate.
if 'CONFIG_FIRMWARE_INCLUDE_LUA=y' in effective_firmware_config:
    from target_lua_audit import audit_lua
    if closure is None:
        report['lua_audit']={'passed':False,'error':'ELF dependency checker unavailable'}
    else:
        report['lua_audit']=audit_lua(root,qemu,closure,readelf)
    report['checks']['image_lua_utilities']=report['lua_audit']['passed']

effective_config=(trunk/'.config').read_text().splitlines()
kernel_config_lines=(trunk/'linux-4.4.x/.config').read_text().splitlines()
kernel_config={}
for line in kernel_config_lines:
    if line.startswith('CONFIG_') and '=' in line:
        key,value=line.split('=',1)
        kernel_config[key]=value.strip('"')
    elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
        kernel_config[line[2:-11]]='n'
report['selected_service_entrypoints']=[]
report['feature_image_gates']={}
report['entrypoint_gaps']=[]
zapret2_enabled='CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y' in effective_config
zapret2_hashes={
    'usr/share/zapret2/zapret-lib.lua':'6bf528fef1f0fc3c65e189216fc8a06bb873f6e25d1c29d2bfa4695a09b73440',
    'usr/share/zapret2/zapret-antidpi.lua':'6d1fa9168e5de1682fef91fd174f68b58c50f6739ef00f42ca7db2b940b6246d',
    'usr/share/zapret2/zapret-auto.lua':'23a9b99a776d868d92f4cc0ee5110f5c1f12fe746620d9c0337022dbc2f52df0',
    'usr/share/licenses/zapret2/LICENSE.txt':'d089978dd77d53cb6aa5dff51cfdbff617e52dd44af1ac44a6df02c6644f17d5',
}
if zapret2_enabled:
    zapret2_actual={path:digest(root/path) for path in zapret2_hashes
                    if (root/path).is_file()}
    report['zapret2_pinned_assets']={
        'expected':zapret2_hashes,
        'actual':zapret2_actual,
        'scope':'packaged Lua scripts and upstream notice only; strategy execution unverified',
    }
    report['checks']['zapret2_pinned_lua_and_license']=(zapret2_actual==zapret2_hashes)
    zapret2_service_path=root/'usr/sbin/zapret2'
    zapret2_service=(zapret2_service_path.read_text(encoding='utf-8')
                     if zapret2_service_path.is_file() else '')
    report['checks']['zapret2_service_fail_open_and_lua_init']=all(marker in zapret2_service for marker in (
        '--queue-bypass',
        '--lua-init="@$LUA_DIR/zapret-lib.lua"',
        '--lua-init="@$LUA_DIR/zapret-antidpi.lua"',
        '--lua-init="@$LUA_DIR/zapret-auto.lua"',
    )) and '-j LOG' not in zapret2_service
    zapret2_page_path=root/'www/Advanced_Services_Content.asp'
    zapret2_page=(zapret2_page_path.read_text(encoding='utf-8')
                  if zapret2_page_path.is_file() else '')
    zapret2_web_markers=(
        'id="zapret2_enable_on_of"',
        'name="scripts.zapret2.args"',
        'id="wr_zapret2_status"',
        'function validZapret2()',
        'window.setInterval(wrZapret2Refresh, 30000)',
    )
    zapret2_httpd_path=root/'usr/sbin/httpd'
    zapret2_httpd=(zapret2_httpd_path.read_bytes()
                   if zapret2_httpd_path.is_file() else b'')
    zapret2_httpd_markers=(b'found_app_zapret2',b'wr_zapret2_status',
                           b'zapret2_enable',b'nfqws2',
                           b'/etc/storage/zapret2.args')
    zapret2_dicts={name:(root/f'www/{name}').read_text(encoding='utf-8')
                   for name in ('EN.dict','UK.dict','RU.dict')
                   if (root/f'www/{name}').is_file()}
    report['zapret2_webui']={
        'page_markers':list(zapret2_web_markers),
        'httpd_markers':[item.decode() for item in zapret2_httpd_markers],
        'dict_files':sorted(zapret2_dicts),
        'page_marker_checks':{marker:marker in zapret2_page
                              for marker in zapret2_web_markers},
        'httpd_marker_checks':{item.decode():item in zapret2_httpd
                               for item in zapret2_httpd_markers},
        'dict_marker_checks':{name:'WRZapret2StrategyRequired=' in text
                              for name,text in zapret2_dicts.items()},
        'scope':'shipped controls, localized state labels and compiled restart/status routes only; browser and traffic effect unverified',
    }
    report['checks']['zapret2_webui_image']=(
        all(report['zapret2_webui']['page_marker_checks'].values()) and
        all(report['zapret2_webui']['httpd_marker_checks'].values()) and
        set(zapret2_dicts)=={'EN.dict','UK.dict','RU.dict'} and
        all(report['zapret2_webui']['dict_marker_checks'].values()))
    if closure is not None:
        report['zapret2_elf_dependency_closure']=closure.verify(
            root,root,readelf,['usr/sbin/nfqws2'])
        report['checks']['zapret2_elf_dependency_closure']=True
    else:
        report['zapret2_elf_dependency_closure_error']='ELF dependency checker unavailable'
        report['checks']['zapret2_elf_dependency_closure']=False
qos_enabled='CONFIG_FIRMWARE_INCLUDE_QOS=y' in effective_config
qos_gate=qos_image_gate_status(qos_enabled,image_paths,kernel_config)
if qos_enabled:
    qos_gate['scope']='selected-image kernel modules/config and tc MIPS ELF/library closure/version under QEMU; QoS rules, activation and throughput unverified'
    try:
        tc=root/'bin/tc'
        if not tc.is_file() or not tc.stat().st_mode & 0o111:
            raise ValueError('/bin/tc is absent, unresolved or not executable')
        if closure is None or not readelf:
            raise RuntimeError('ELF dependency checker is unavailable')
        qos_gate['tc_sha256']=digest(tc)
        qos_gate['tc_elf_dependency_closure']=closure.verify(root,root,readelf,['bin/tc'])
        probe=subprocess.run([qemu,'-L',str(root),str(tc),'-V'],
            capture_output=True,timeout=10,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
        version=(probe.stdout+probe.stderr).decode(errors='replace').strip()
        qos_gate['tc_version_output']=version
        qos_gate['tc_qemu_version_passed']=probe.returncode==0 and 'tc utility' in version
    except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as error:
        qos_gate['tc_probe_error']=str(error)
        qos_gate['tc_qemu_version_passed']=False
    qos_gate['passed']=qos_gate['passed'] and qos_gate['tc_qemu_version_passed']
report['feature_image_gates']['qos']=qos_gate
report['checks']['qos_exact_romfs_gate']=qos_gate['passed']
if qos_enabled and not qos_gate['passed']:
    report['entrypoint_gaps'].append({'group':'qos',
        'reason':'selected image lacks QoS dependencies/core config, or /bin/tc ELF/target version probe failed'})
zram_enabled='CONFIG_FIRMWARE_INCLUDE_ZRAM=y' in effective_config
if zram_enabled:
    zram_report_path=Path('zram-image-checks.txt')
    zram_expected='PASS zram dependencies, rc command and image BusyBox priority/discard help under QEMU; activation unverified'
    try:
        zram_pass=zram_report_path.read_text(encoding='utf-8').strip()==zram_expected
    except OSError:
        zram_pass=False
    report['feature_image_gates']['zram']={'report':str(zram_report_path),
        'scope':'final ROMFS dependencies, rc command and exact-image BusyBox help; activation unverified',
        'passed':zram_pass}
    report['checks']['zram_exact_romfs_busybox_gate']=zram_pass
    if not zram_pass:
        report['entrypoint_gaps'].append({'group':'zram',
            'reason':'dedicated exact-image ZRAM report missing or incomplete'})
else:
    report['feature_image_gates']['zram']={'status':'not selected'}
    report['checks']['zram_exact_romfs_busybox_gate']=True
wpad_enabled='CONFIG_FIRMWARE_INCLUDE_WPAD=y' in effective_config
if wpad_enabled:
    wpad_report_path=Path('wpad-image-checks.json')
    try:
        wpad_report=json.loads(wpad_report_path.read_text(encoding='utf-8'))
        wpad_checks=wpad_report.get('checks',{})
        required_wpad_checks=('effective_selector','link_wpad.dat','link_wpad.da',
            'link_proxy.pac','editor','capability_guard','login_guard','httpd_capability',
            'httpd_mime','httpd_field','default_direct','preserve_existing')
        wpad_pass=(wpad_report.get('scope')=='WPAD ROMFS packaging only; runtime unverified'
                   and all(wpad_checks.get(key) is True for key in required_wpad_checks))
    except (OSError,ValueError):
        wpad_checks={}
        required_wpad_checks=()
        wpad_pass=False
    report['feature_image_gates']['wpad']={'report':str(wpad_report_path),
        'scope':'final ROMFS editor, HTTP field, PAC links and preservation checks; runtime unverified',
        'passed':wpad_pass,'required_checks':list(required_wpad_checks)}
    report['checks']['wpad_exact_romfs_gate']=wpad_pass
    if not wpad_pass:
        report['entrypoint_gaps'].append({'group':'wpad',
            'reason':'dedicated exact-image WPAD ROMFS report missing or incomplete'})
else:
    report['feature_image_gates']['wpad']={'status':'not selected'}
    report['checks']['wpad_exact_romfs_gate']=True
sfe_enabled='CONFIG_FIRMWARE_INCLUDE_SFE=y' in effective_config
sfe_gate=sfe_image_gate_status(sfe_enabled,image_paths,applets)
report['feature_image_gates']['sfe']=sfe_gate
report['checks']['sfe_exact_romfs_gate']=sfe_gate['passed']
if sfe_enabled and not sfe_gate['passed']:
    report['entrypoint_gaps'].append({'group':'sfe',
        'reason':'exact-image rc, Shortcut FE modules or BusyBox modprobe applet missing'})
# Active selectors are fully classified as service groups, image components,
# or pending investigation. This is selector accounting only; it does not claim
# that lifecycle interactions or every package payload have been audited.
selector_classes={
    'CONFIG_FIRMWARE_INCLUDE_DROPBEAR':('service','dropbear_ssh'),
    'CONFIG_FIRMWARE_INCLUDE_STUBBY':('service','stubby'),
    'CONFIG_FIRMWARE_INCLUDE_DOH':('service','doh'),
    'CONFIG_FIRMWARE_INCLUDE_PRIVOXY':('service','privoxy'),
    'CONFIG_FIRMWARE_INCLUDE_IPERF3':('service','iperf3'),
        'CONFIG_FIRMWARE_INCLUDE_ZAPRET2':('service','zapret2'),
    'CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS':('service','shadowsocks_clients'),
    'CONFIG_FIRMWARE_INCLUDE_SSREDIR':('service','shadowsocks_clients'),
    'CONFIG_FIRMWARE_INCLUDE_SSLOCAL':('service','shadowsocks_clients'),
    'CONFIG_FIRMWARE_INCLUDE_WIREGUARD':('service','wireguard_amneziawg'),
    'CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG':('service','wireguard_amneziawg'),
    'CONFIG_FIRMWARE_INCLUDE_ZEROTIER':('service','zerotier'),
    'CONFIG_FIRMWARE_INCLUDE_USBIP':('service','usbip'),
    'CONFIG_FIRMWARE_INCLUDE_VLMCSD':('service','vlmcsd'),
    'CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING':('service','wr_band_steering'),
    'CONFIG_FIRMWARE_INCLUDE_ZRAM':('runtime_feature','zram'),
    'CONFIG_FIRMWARE_INCLUDE_QOS':('runtime_feature','qos'),
    'CONFIG_FIRMWARE_INCLUDE_SFE':('runtime_feature','sfe'),
    'CONFIG_FIRMWARE_INCLUDE_U2EC':('service','u2ec'),
    'CONFIG_FIRMWARE_INCLUDE_WPAD':('web_feature','wpad'),
    'CONFIG_FIRMWARE_INCLUDE_FS_TOOLS':('component','filesystem_tools'),
    'CONFIG_FIRMWARE_INCLUDE_HID':('component','usb_hid'),
    'CONFIG_FIRMWARE_INCLUDE_XFRM':('component','ipsec_xfrm'),
    'CONFIG_FIRMWARE_INCLUDE_IMQ':('component','qos'),
    'CONFIG_FIRMWARE_INCLUDE_IFB':('component','qos'),
    'CONFIG_FIRMWARE_INCLUDE_IPSET':('component','firewall'),
    'CONFIG_FIRMWARE_INCLUDE_LANG_RU':('component','language_ru'),
    'CONFIG_FIRMWARE_INCLUDE_LANG_UK':('component','language_uk'),
    'CONFIG_FIRMWARE_INCLUDE_VENDOR_LOGO':('component','vendor_branding'),
    'CONFIG_FIRMWARE_INCLUDE_NTFS_3G':('component','ntfs'),
    'CONFIG_FIRMWARE_INCLUDE_TCPDUMP':('component','diagnostics'),
    'CONFIG_FIRMWARE_INCLUDE_SOCAT':('component','network_utilities'),
    'CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6':('component','ipv6_diagnostics'),
    'CONFIG_FIRMWARE_INCLUDE_EAP_PEAP':('component','wifi_auth'),
    'CONFIG_FIRMWARE_INCLUDE_DDNS_SSL':('component','https_ddns'),
    'CONFIG_FIRMWARE_INCLUDE_HTTPS':('component','https_ddns'),
    'CONFIG_FIRMWARE_INCLUDE_DROPBEAR_FAST_CODE':('component','dropbear_ssh'),
    'CONFIG_FIRMWARE_INCLUDE_OPENSSL_EC':('component','crypto'),
    'CONFIG_FIRMWARE_INCLUDE_OPENSSL_EXE':('component','crypto'),
    'CONFIG_FIRMWARE_INCLUDE_CURL':('component','network_utilities'),
    'CONFIG_FIRMWARE_INCLUDE_QUIC':('component','network_utilities'),
    'CONFIG_FIRMWARE_INCLUDE_OPENSSL_35':('component','crypto'),
    'CONFIG_FIRMWARE_INCLUDE_LUA':('component','runtime'),
    'CONFIG_FIRMWARE_INCLUDE_TPROXY':('component','transparent_proxy'),
    'CONFIG_FIRMWARE_INCLUDE_QRENCODE':('component','vpn_qr'),
}
service_entrypoints=(
    ('dropbear_ssh',('CONFIG_FIRMWARE_INCLUDE_DROPBEAR',),('usr/bin/sshd.sh',)),
    ('stubby',('CONFIG_FIRMWARE_INCLUDE_STUBBY',),('usr/bin/stubby.sh',)),
    ('doh',('CONFIG_FIRMWARE_INCLUDE_DOH',),('usr/bin/doh_proxy.sh',)),
    ('privoxy',('CONFIG_FIRMWARE_INCLUDE_PRIVOXY',),('usr/bin/privoxy.sh',)),
    ('iperf3',('CONFIG_FIRMWARE_INCLUDE_IPERF3',),('usr/bin/iperf3.sh',)),
    ('zapret2',('CONFIG_FIRMWARE_INCLUDE_ZAPRET2',),
        ('usr/sbin/nfqws2','usr/sbin/zapret2',
         'usr/share/zapret2/zapret-lib.lua',
         'usr/share/zapret2/zapret-antidpi.lua',
         'usr/share/zapret2/zapret-auto.lua',
         'usr/share/licenses/zapret2/LICENSE.txt')),
    ('shadowsocks_clients',('CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS',
                            'CONFIG_FIRMWARE_INCLUDE_SSREDIR','CONFIG_FIRMWARE_INCLUDE_SSLOCAL'),
        ('usr/bin/ss-local','usr/bin/ss-redir','usr/bin/shadowsocks.sh',
         'usr/bin/ss-monitor','usr/bin/ss-rules')),
    ('wireguard_amneziawg',('CONFIG_FIRMWARE_INCLUDE_WIREGUARD',
                            'CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG'),
        ('usr/bin/wireguard.sh','usr/bin/wgc.sh','usr/bin/wgs.sh','usr/sbin/wr-vpn-profiles-service')),
    ('zerotier',('CONFIG_FIRMWARE_INCLUDE_ZEROTIER',),
        ('usr/bin/zerotier.sh','usr/bin/zerotier-monitor.sh','usr/bin/zerotier-policy.sh')),
    ('usbip',('CONFIG_FIRMWARE_INCLUDE_USBIP',),
        ('usr/libexec/wr-usbip/device-action.sh','usr/libexec/wr-usbip/device-policy.sh',
         'usr/libexec/wr-usbip/firewall-policy.sh','usr/libexec/wr-usbip/restore.sh','usr/sbin/wr-usbip')),
    ('vlmcsd',('CONFIG_FIRMWARE_INCLUDE_VLMCSD',),('usr/bin/vlmcsd.sh',)),
    ('u2ec',('CONFIG_FIRMWARE_INCLUDE_U2EC',),('usr/sbin/u2ec',)),
    ('wr_band_steering',('CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING',),
        ('usr/sbin/wr-band-steering','usr/sbin/wr-band-steering-ctl','sbin/rc')),
)
shell_inventory={item['path']:item for item in report['scripts']}
for service,selectors,paths in service_entrypoints:
    active=[selector for selector in selectors if selector+'=y' in effective_config]
    if not active:continue
    entries=[]
    for relative in paths:
        path=root/relative
        present=path.is_file()
        shell=shell_inventory.get(relative)
        entries.append({'path':relative,'present':present,
            'sha256':digest(path) if present else None,
            'shell_syntax_exit':shell['syntax_exit'] if shell else None,
            'covered_by_shell_inventory':shell is not None})
    passed=all(item['present'] and
        (item['shell_syntax_exit']==0 if item['covered_by_shell_inventory'] else True)
        for item in entries)
    report['checks'][service+'_selected_entrypoints_present_and_syntax_checked']=passed
    report['selected_service_entrypoints'].append({'service':service,'selectors':active,
        'scope':'selected image entrypoint presence and shell syntax only; lifecycle/persistence/status chains unverified',
        'entries':entries,'passed':passed})
active_include_selectors=sorted(line.split('=',1)[0] for line in effective_config
                                  if line.startswith('CONFIG_FIRMWARE_INCLUDE_') and line.endswith('=y'))
unclassified_include_selectors=sorted(set(active_include_selectors)-set(selector_classes))
report['active_include_selector_classification']=[
    {'selector':selector,'class':selector_classes[selector][0],
     'group':selector_classes[selector][1]} for selector in active_include_selectors
     if selector in selector_classes]
report['unclassified_active_include_selectors']=unclassified_include_selectors
classification_complete=not unclassified_include_selectors
report['checks']['all_active_include_selectors_classified']=classification_complete
service_map=active_service_entrypoint_map_status(active_include_selectors,
    selector_classes,service_entrypoints,report['checks'])
report['active_service_groups']=service_map['active_service_groups']
report['unmapped_active_service_groups']=service_map['unmapped_active_service_groups']
report['unmapped_active_service_selectors']=service_map['unmapped_active_service_selectors']
report['active_service_entrypoint_checks']=service_map['active_service_entrypoint_checks']
report['checks']['all_active_service_entrypoint_maps_checked']=service_map['complete']
report['selected_service_entrypoint_map_complete']=service_map['complete']
report['service_dispatch_probes']=[]
for service, selector, script_name in (
        ('stubby','CONFIG_FIRMWARE_INCLUDE_STUBBY','stubby.sh'),
        ('doh','CONFIG_FIRMWARE_INCLUDE_DOH','doh_proxy.sh'),
        ('privoxy','CONFIG_FIRMWARE_INCLUDE_PRIVOXY','privoxy.sh'),
        ('vlmcsd','CONFIG_FIRMWARE_INCLUDE_VLMCSD','vlmcsd.sh')):
    if selector+'=y' not in effective_config:continue
    script=root/'usr/bin'/script_name
    if not script.is_file():
        report['checks'][service+'_dispatcher_present']=False
        report['service_dispatch_probes'].append({
            'service':service,'script':str(script.relative_to(root)),
            'scope':'required by effective selector; image dispatcher missing',
            'passed':False,
        })
        continue
    report['checks'][service+'_dispatcher_present']=True
    # These shipped dispatchers reject unknown actions before opening a lock
    # or invoking any external lifecycle command. Run the original image
    # script under its actual shell, rather than source it in the host shell.
    probe=run(['sh',str(script),'__wr_audit_invalid_action__'])
    refusal_output=probe.stdout+probe.stderr
    passed=probe.returncode==1 and b'Usage:' in refusal_output
    report['checks'][service+'_invalid_action_refused']=passed
    report['service_dispatch_probes'].append({
        'service':service,'script':str(script.relative_to(root)),
        'script_sha256':digest(script),'exit':probe.returncode,
        'refusal_text_found':b'Usage:' in refusal_output,
        'scope':'unknown action only; lock, configuration and daemon lifecycle are not entered',
        'passed':passed,
    })
with tempfile.TemporaryDirectory(prefix='target-busybox-') as tmp:
    # Exercise the shipped helper's shell decisions, then its external applet
    # separately. QEMU is not a chroot: an unqualified external chmod here
    # could otherwise accidentally validate the host utility.
    helper_tree=ast.parse((Path(__file__).parent/'vpn-profiles/prepare-storage-permissions.py').read_text())
    helper=next(ast.literal_eval(n.value) for n in helper_tree.body
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HELPER' for t in n.targets))
    storage=Path(tmp)/'storage';storage.mkdir()
    private=storage/'wrvpn';private.mkdir(mode=0o755);private.chmod(0o755)
    command=helper+'\nchmod() { printf "%s\\n" "$@"; }\nfunc_wrvpn_private "$1"\n'
    probe=run(['sh','-c',command,'storage-probe',str(storage)])
    report['checks']['vpn_storage_helper_directory']=probe.returncode==0 and probe.stdout==('700\n'+str(private)+'\n').encode()
    probe=run(['chmod','700',str(private)])
    report['checks']['vpn_storage_chmod_private']=probe.returncode==0 and private.stat().st_mode&0o777==0o700
    missing=Path(tmp)/'missing';missing.mkdir()
    probe=run(['sh','-c',command,'storage-probe',str(missing)])
    report['checks']['vpn_storage_helper_absent_noop']=probe.returncode==0 and not probe.stdout
    linked=Path(tmp)/'linked';linked.mkdir();(linked/'wrvpn').symlink_to(private)
    probe=run(['sh','-c',command,'storage-probe',str(linked)])
    report['checks']['vpn_storage_helper_symlink_refused']=probe.returncode!=0 and not probe.stdout
    invalid=Path(tmp)/'invalid';invalid.mkdir();(invalid/'wrvpn').write_text('fixture')
    probe=run(['sh','-c',command,'storage-probe',str(invalid)])
    report['checks']['vpn_storage_helper_file_refused']=probe.returncode!=0 and not probe.stdout
    target=Path(tmp)/'canonical';target.mkdir()
    alias=Path(tmp)/'alias';alias.symlink_to(target,target_is_directory=True)
    probe=run(['readlink','-f',str(alias)])
    report['checks']['readlink_follow_exact_options']=probe.returncode==0 and probe.stdout.decode().strip()==str(target.resolve())
    report['checks']['readlink_follow_config']=all(key+'=y' in config.read_text().splitlines() for key in ('CONFIG_READLINK','CONFIG_FEATURE_READLINK_FOLLOW'))
    sample=Path(tmp)/'serial';sample.write_bytes(b'unit-test-only\n')
    probe=run(['hexdump','-v','-n','258','-e','1/1 "%02x"',str(sample)])
    report['checks']['usbip_hexdump_exact_options']=probe.returncode==0 and probe.stdout==sample.read_bytes().hex().encode()
    od_sample=Path(tmp)/'od-sample';od_sample.write_bytes(bytes((0,1,127,255)))
    probe=run(['od','-b',str(od_sample)])
    report['checks']['od_octal_bytes']=probe.returncode==0 and bool(
        re.search(rb'\b000\s+001\s+177\s+377\b',probe.stdout))
    import fcntl
    lock=Path(tmp)/'lock'
    with lock.open('w+') as held:
        fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with lock.open('r+') as competing:
            probe=run(['flock','-x','-n',str(competing.fileno())],pass_fds=(competing.fileno(),))
            report['checks']['flock_contention_refused']=probe.returncode!=0
        fcntl.flock(held,fcntl.LOCK_UN)
        probe=run(['flock','-x','-n',str(held.fileno())],pass_fds=(held.fileno(),))
        report['checks']['flock_descriptor_options']=probe.returncode==0
report['success']=all(report['checks'].values())
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(('PASS' if report['success'] else 'FAIL')+' target BusyBox audit gate; full service/runtime audit remains open')
raise SystemExit(0 if report['success'] else 1)
