import os,subprocess,sys,json
from pathlib import Path
if os.geteuid()!=0 or not os.environ.get('WR_IOT_PARENT_NETNS') or os.readlink('/proc/self/ns/net')==os.environ['WR_IOT_PARENT_NETNS']:
 raise SystemExit('Requires new isolated network namespace')
r=Path(sys.argv[1]).resolve();binary=str(r/'check-iot-bridge');checks={}
def run(*a):return subprocess.run(a,check=True,capture_output=True,text=True)
def expect(key,operation,success):
 p=subprocess.run([binary,operation]);checks[key]=(p.returncode==0)==success;assert checks[key],key
run('mount','--make-rprivate','/');run('mount','-t','sysfs','sysfs','/sys')
expect('missing_remove_noop','remove',True)
expect('missing_down_noop','down',True)
expect('missing_up_rejected','up',False)
expect('missing_bss_down_noop','bss-down',True)
expect('missing_bss_observed_down','bss-is-down',True)
expect('missing_bss_up_rejected','bss-up',False)
expect('missing_active_observation_rejected','bss-active',False)
run('ip','link','add','br-iot','type','bridge')
expect('foreign_bridge_up_rejected','up',False);expect('foreign_bridge_down_rejected','down',False)
expect('foreign_bridge_prepare_rejected','prepare',False);expect('foreign_bridge_remove_rejected','remove',False)
assert Path('/sys/class/net/br-iot').exists();run('ip','link','delete','br-iot')
expect('owned_create_prepare','prepare',True)
info=json.loads(run('ip','-j','address','show','dev','br-iot').stdout)[0]
checks['created_down']='UP' not in info['flags'];assert checks['created_down']
checks['address_mask']=any(x.get('local')=='192.168.50.1' and x.get('prefixlen')==24 for x in info['addr_info']);assert checks['address_mask']
assert Path('/sys/class/net/br-iot/ifalias').read_text().strip()=='wr1200js-iot-v1'
for alias in ('wr1200js-iot-v1-extra','wr1200js-iot-v1\nforeign'):
 run('ip','link','set','dev','br-iot','alias',alias)
 expect('invalid_alias_prepare_'+repr(alias),'prepare',False)
 expect('invalid_alias_remove_'+repr(alias),'remove',False)
 assert Path('/sys/class/net/br-iot').exists()
run('ip','link','set','dev','br-iot','alias','wr1200js-iot-v1')
if Path('/proc/sys/net/ipv6/conf/all/disable_ipv6').exists():
 checks['ipv6_disabled']=Path('/proc/sys/net/ipv6/conf/br-iot/disable_ipv6').read_text().strip()=='1';assert checks['ipv6_disabled']
run('ip','link','set','br-iot','up');expect('active_bridge_remove_rejected','remove',False);expect('active_bridge_prepare_rejected','prepare',False)
run('ip','link','set','br-iot','down');run('ip','link','add','test-port','type','dummy');run('ip','link','set','test-port','master','br-iot')
expect('foreign_member_up_rejected','up',False);expect('foreign_member_down_rejected','down',False)
expect('attached_bridge_remove_rejected','remove',False);expect('attached_bridge_prepare_rejected','prepare',False)
run('ip','link','set','test-port','nomaster');run('ip','link','delete','test-port')
expect('missing_bss_attach_rejected','attach',False);expect('missing_bss_detach_noop','detach',True)
run('ip','link','add','ra2','type','dummy');run('ip','link','set','ra2','up')
expect('active_bss_attach_rejected','attach',False);expect('detached_bss_down','bss-down',True)
expect('detached_bss_observed_down','bss-is-down',True)
assert 'UP' not in json.loads(run('ip','-j','link','show','dev','ra2').stdout)[0]['flags']
run('ip','link','add','other-br','type','bridge');run('ip','link','set','ra2','master','other-br')
expect('foreign_master_attach_rejected','attach',False);expect('foreign_master_detach_rejected','detach',False)
expect('foreign_master_bss_up_rejected','bss-up',False)
expect('foreign_master_down_observation_rejected','bss-is-down',False)
run('ip','link','set','ra2','up');expect('foreign_master_bss_down_rejected','bss-down',False)
assert 'UP' in json.loads(run('ip','-j','link','show','dev','ra2').stdout)[0]['flags']
run('ip','link','set','ra2','down')
run('ip','link','set','ra2','nomaster');run('ip','link','delete','other-br')
expect('empty_bridge_up_rejected','up',False)
expect('down_bss_attach_owned','attach',True)
expect('down_owned_attach_retry','attach',True)
run('ip','link','add','attach-foreign','type','dummy')
run('ip','link','set','attach-foreign','master','br-iot')
expect('attach_retry_foreign_member_refused','attach',False)
run('ip','link','set','attach-foreign','nomaster');run('ip','link','delete','attach-foreign')
expect('owned_attached_up','up',True)
expect('attach_retry_active_bridge_refused','attach',False)
assert Path('/sys/class/net/ra2/master').resolve().name=='br-iot'
assert 'UP' in json.loads(run('ip','-j','link','show','dev','br-iot').stdout)[0]['flags']
run('ip','link','add','foreign-port','type','dummy')
run('ip','link','set','foreign-port','master','br-iot')
expect('foreign_member_bss_up_rejected','bss-up',False)
assert 'UP' not in json.loads(run('ip','-j','link','show','dev','ra2').stdout)[0]['flags']
run('ip','link','set','foreign-port','nomaster');run('ip','link','delete','foreign-port')
expect('owned_bss_up','bss-up',True)
expect('owned_active_bss_observed','bss-active',True)
ipv6_gate=Path('/proc/sys/net/ipv6/conf/br-iot/disable_ipv6')
if ipv6_gate.exists():
 ipv6_gate.write_text('0')
 expect('reenabled_ipv6_active_observation_refused','bss-active',False)
 expect('reenabled_ipv6_bss_open_refused','bss-up',False)
 ipv6_gate.write_text('1')
 expect('restored_ipv6_gate_active_observed','bss-active',True)
expect('owned_active_not_down','bss-is-down',False)
run('ip','link','add','obs-foreign','type','dummy')
run('ip','link','set','obs-foreign','master','br-iot')
expect('active_foreign_member_observation_rejected','bss-active',False)
run('ip','link','set','obs-foreign','nomaster');run('ip','link','delete','obs-foreign')
assert 'UP' in json.loads(run('ip','-j','link','show','dev','ra2').stdout)[0]['flags']
expect('owned_bss_up_idempotent','bss-up',True)
expect('owned_bss_down_after_up','bss-down',True)
expect('owned_bss_observed_down','bss-is-down',True)
expect('down_bss_observation_rejected','bss-active',False)
expect('owned_attached_down','down',True)
expect('down_bridge_bss_up_rejected','bss-up',False)
assert 'UP' not in json.loads(run('ip','-j','link','show','dev','br-iot').stdout)[0]['flags']
expect('attached_owned_remove_rejected','remove',False)
run('ip','link','set','ra2','up');expect('active_bss_bridge_up_rejected','up',False);expect('active_bss_bridge_down_rejected','down',False);expect('active_bss_detach_rejected','detach',False)
expect('owned_bss_checked_down','bss-down',True);expect('down_owned_bss_detach','detach',True)
expect('detached_bss_detach_retry','detach',True)
assert not Path('/sys/class/net/ra2/master').exists()
run('ip','link','delete','ra2');expect('owned_empty_down_remove','remove',True)
assert not Path('/sys/class/net/br-iot').exists()
expect('removed_bridge_down_retry_noop','down',True)
(r/'iot-bridge-kernel.json').write_text(json.dumps({'checks':checks,'scope':'Host-kernel owned bridge ioctl lifecycle; target Wi-Fi and production RC integration unverified','runtime_verified':False},indent=2)+'\n')
print('PASS owned IoT bridge creation stays down, conflict and active/attached guards, safe removal')
