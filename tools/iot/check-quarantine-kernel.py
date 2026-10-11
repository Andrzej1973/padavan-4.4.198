"""Observe real legacy netfilter rules in a disposable network namespace."""
import json,os,subprocess,sys
from pathlib import Path
if os.geteuid()!=0 or not os.environ.get('WR_IOT_PARENT_NETNS') or os.readlink('/proc/self/ns/net')==os.environ['WR_IOT_PARENT_NETNS']:
    raise SystemExit('Requires a new isolated network namespace')
root=Path(sys.argv[1]).resolve();checks={}
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','sysfs','sysfs','/sys'],check=True)
subprocess.run(['mount','-t','tmpfs','tmpfs','/run'],check=True)
rules=''.join(f'-A {chain} {direction} {interface} -j DROP\n' for chain,direction,interface in [
    ('INPUT','-i','br-iot'),('FORWARD','-i','br-iot'),('FORWARD','-o','br-iot'),
    ('INPUT','-i','ra2'),('FORWARD','-i','ra2'),('FORWARD','-o','ra2')])
def install(family,body):
    text='*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n'+body+'COMMIT\n'
    subprocess.run(['ip6tables-legacy-restore' if family==6 else 'iptables-legacy-restore'],input=text,text=True,check=True)
def expect(label,family,success):
    result=subprocess.run([str(root/'check-iot-quarantine-live'),str(family)],timeout=5)
    checks[label]=(result.returncode==0)==success
    if not checks[label] and str(family) in ('policy4','policy6'):
        command='iptables-legacy-save' if family=='policy4' else 'ip6tables-legacy-save'
        diagnostic=subprocess.run([command,'-t','filter'],capture_output=True,text=True,check=True).stdout
        (root/f'{label}-rules.txt').write_text(diagnostic)
        print(diagnostic,flush=True)
    assert checks[label],label
for family in (4,6):
    install(family,'');expect(f'v{family}_empty_rejected',family,False)
    install(family,rules);expect(f'v{family}_quarantine_observed',family,True)
    install(family,'-A INPUT -j ACCEPT\n'+rules);expect(f'v{family}_prior_input_accept_rejected',family,False)
    install(family,'-A FORWARD -j ACCEPT\n'+rules);expect(f'v{family}_prior_forward_accept_rejected',family,False)
    install(family,rules.replace('ra2','ra3'));expect(f'v{family}_wrong_bss_rejected',family,False)
    install(family,rules);expect(f'v{family}_restored_quarantine_observed',family,True)
expect('unguarded_observation_rejected','unguarded',False)
expect('missing_owned_bridge_rejected','owned',False)
subprocess.run(['ip','link','add','br-iot','type','bridge'],check=True)
expect('foreign_bridge_rejected','owned',False)
subprocess.run(['ip','link','set','br-iot','alias','wr1200js-iot-v1'],check=True)
subprocess.run(['ip','link','add','ra2','type','dummy'],check=True)
expect('owned_guarded_quarantine_ready','owned',True)
subprocess.run(['ip','link','set','ra2','up'],check=True)
expect('active_bss_rejected','owned',False)
subprocess.run(['ip','link','set','ra2','down'],check=True)
expect('owned_down_bss_ready','owned',True)
expect('down_bridge_can_apply','can-apply',True)
subprocess.run(['ip','link','set','br-iot','up'],check=True)
expect('active_bridge_apply_rejected','can-apply',False)
subprocess.run(['ip','link','set','br-iot','down'],check=True)
for family in (4,6):
    executable='ip6tables-legacy-restore' if family==6 else 'iptables-legacy-restore'
    policy=(root/f'iot-filter.v{family}').read_text()
    def apply(text):subprocess.run([executable],input=text,text=True,check=True)
    apply(policy);expect(f'v{family}_active_policy_observed',f'policy{family}',True)
    changed=policy.replace(':OUTPUT ACCEPT [0:0]\n',':OUTPUT ACCEPT [0:0]\n-A INPUT -j ACCEPT\n',1)
    apply(changed);expect(f'v{family}_active_prior_accept_rejected',f'policy{family}',False)
    changed=policy.replace('--dport 53','--dport 54') if family==4 else policy.replace('-A FORWARD -o br-iot -j DROP','-A FORWARD -o br-iot -j ACCEPT')
    assert changed!=policy
    apply(changed);expect(f'v{family}_active_changed_rule_rejected',f'policy{family}',False)
    if family==4:
        apply(policy.replace('eth2.2','eth2.3'));expect('v4_wrong_wan_rejected','policy4',False)
    apply(policy);expect(f'v{family}_active_policy_restored',f'policy{family}',True)
(root/'iot-quarantine-kernel.json').write_text(json.dumps({'checks':checks,'scope':'Host legacy netfilter readback; router kernel/offload/activation unverified'},indent=2)+'\n')
print('PASS live IPv4/IPv6 quarantine readback: actual kernel rules, early accepts and wrong BSS rejected')
print('PASS live active policy readback: IPv4 scoped DHCP/DNS/WAN and IPv6 drops, prior accept and changed rules/WAN rejected')
