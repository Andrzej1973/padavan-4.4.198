"""Observe real legacy netfilter rules in a disposable network namespace."""
import json,os,subprocess,sys
from pathlib import Path
if os.geteuid()!=0 or not os.environ.get('WR_IOT_PARENT_NETNS') or os.readlink('/proc/self/ns/net')==os.environ['WR_IOT_PARENT_NETNS']:
    raise SystemExit('Requires a new isolated network namespace')
root=Path(sys.argv[1]).resolve();checks={}
rules=''.join(f'-A {chain} {direction} {interface} -j DROP\n' for chain,direction,interface in [
    ('INPUT','-i','br-iot'),('FORWARD','-i','br-iot'),('FORWARD','-o','br-iot'),
    ('INPUT','-i','ra2'),('FORWARD','-i','ra2'),('FORWARD','-o','ra2')])
def install(family,body):
    text='*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n'+body+'COMMIT\n'
    subprocess.run(['ip6tables-legacy-restore' if family==6 else 'iptables-legacy-restore'],input=text,text=True,check=True)
def expect(label,family,success):
    result=subprocess.run([str(root/'check-iot-quarantine-live'),str(family)],timeout=5)
    checks[label]=(result.returncode==0)==success
    assert checks[label],label
for family in (4,6):
    install(family,'');expect(f'v{family}_empty_rejected',family,False)
    install(family,rules);expect(f'v{family}_quarantine_observed',family,True)
    install(family,'-A INPUT -j ACCEPT\n'+rules);expect(f'v{family}_prior_input_accept_rejected',family,False)
    install(family,'-A FORWARD -j ACCEPT\n'+rules);expect(f'v{family}_prior_forward_accept_rejected',family,False)
    install(family,rules.replace('ra2','ra3'));expect(f'v{family}_wrong_bss_rejected',family,False)
    install(family,rules);expect(f'v{family}_restored_quarantine_observed',family,True)
(root/'iot-quarantine-kernel.json').write_text(json.dumps({'checks':checks,'scope':'Host legacy netfilter readback; router kernel/offload/activation unverified'},indent=2)+'\n')
print('PASS live IPv4/IPv6 quarantine readback: actual kernel rules, early accepts and wrong BSS rejected')
