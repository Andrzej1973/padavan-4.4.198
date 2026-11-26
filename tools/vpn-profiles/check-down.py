#!/usr/bin/env python3
"""Exercise CLI down and cleanup retry with a fake ip transport, no net changes."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--wg-validator',required=True,type=Path)
parser.add_argument('--awg-validator',required=True,type=Path)
args=parser.parse_args()
here=Path(__file__).resolve().parent
key=base64.b64encode(bytes(range(1,33))).decode()
public=base64.b64encode(bytes(range(33,65))).decode()
config=(f'[Interface]\nPrivateKey = {key}\nAddress = 10.8.0.2/32, fd00::2/128\n'
        'DNS = 1.1.1.1, fd00::53\n[Peer]\n'
        f'PublicKey = {public}\nEndpoint = test.invalid:51820\n'
        'AllowedIPs = 0.0.0.0/0, ::/0\n')

IP_SCRIPT='''#!/bin/sh
calls={calls}
counter={counter}
failure={failure}
mode={mode}
case "$*" in
    *' -N rule show pref '*)
        if test -f "$mode.empty"; then exit 0; fi
        ;;
esac
case "$*" in
    *' -N rule show pref 20009')
        if test -f "$mode.foreign"; then
            printf '20009:\\tfrom 192.0.2.0/24 fwmark 0x57560005 lookup 20005\\n'
        else
            printf '20009:\\tfrom all fwmark 0x57560005 lookup 20005\\n'
        fi
        exit 0;;
    *' -N rule show pref 20011')
        printf '20011:\\tfrom all fwmark 0x57560006 lookup 20006\\n'
        exit 0;;
esac
number=0
if test -f "$counter"; then IFS= read -r number < "$counter"; fi
number=$((number + 1))
printf '%s\\n' "$number" > "$counter"
printf '%s\\n' "$*" >> "$calls"
fail_at=0
if test -f "$failure"; then IFS= read -r fail_at < "$failure"; fi
if test "$fail_at" -eq "$number"; then
    printf 'RTNETLINK answers: Operation not permitted\\n' >&2
    exit 2
fi
if test -f "$mode"; then
    case "$*" in
        'rule del '*|'-6 rule del '*) printf 'RTNETLINK answers: No such file or directory\\n' >&2; exit 2;;
        'route del '*|'-6 route del '*) printf 'RTNETLINK answers: No such process\\n' >&2; exit 2;;
        'address del '*|'-6 address del '*) printf 'RTNETLINK answers: Cannot assign requested address\\n' >&2; exit 2;;
    esac
fi
exit 0
'''

with tempfile.TemporaryDirectory(prefix='wrvpn-down-') as temporary:
    root=Path(temporary);store=root/'store';runtime=root/'runtime';store.mkdir(mode=0o700)
    (runtime).mkdir(mode=0o700)
    calls=root/'ip-calls';counter=root/'ip-counter';failure=root/'fail-at';mode=root/'absent-errors'
    ip=root/'ip';ip.write_text(IP_SCRIPT.format(calls=calls,counter=counter,failure=failure,mode=mode));ip.chmod(0o700)
    exe=root/'profilectl';seed=root/'seed-session'
    sources=[here/'profilectl.c',here/'validate-process.c',here/'store.c',here/'link-observation.c',
      here/'runtime-state.c',here/'config-transaction.c',here/'config-apply.c',here/'config-plan.c',
      here/'plan-report.c',here/'addr-apply.c',here/'route-apply.c',here/'profile-apply.c',
      here/'dns-apply.c',here/'teardown.c',here/'link-actions.c',here/'link-lifecycle.c',here/'endpoint-pin.c']
    definitions=[
      '-DWR_VPN_STORE_ROOT='+json.dumps(str(store)),
      '-DWR_VPN_RUNTIME_ROOT='+json.dumps(str(runtime)),
      '-DWR_VPN_VALIDATE_WG='+json.dumps(str(args.wg_validator.resolve())),
      '-DWR_VPN_VALIDATE_AWG='+json.dumps(str(args.awg_validator.resolve())),
      '-DWR_VPN_IP='+json.dumps(str(ip)),
      '-DWR_VPN_IP_FALLBACK='+json.dumps(str(ip))]
    subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
      *definitions,*map(str,sources),'-o',str(exe)],check=True)
    subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
      '-I'+str(here),str(here/'check-down-seed.c'),str(here/'runtime-state.c'),
      str(here/'store.c'),str(here/'validate-process.c'),'-o',str(seed)],check=True)
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:exitcode=98',UBSAN_OPTIONS='halt_on_error=1:exitcode=97')

    def create(id=5):
        result=subprocess.run([str(exe),'create',str(id),'wireguard'],input=config.encode(),
          capture_output=True,timeout=10,env=env)
        assert result.returncode==0 and result.stdout.startswith(b'saved\t'),(result.returncode,result.stdout,result.stderr)
    def seed_session(id=5):
        subprocess.run([str(seed),str(store),str(id),'1',str(runtime/str(id))],check=True,env=env,timeout=10)
    def down(id=5,expected=0):
        result=subprocess.run([str(exe),'down',str(id)],capture_output=True,timeout=10,env=env)
        assert result.returncode==expected,(id,result.returncode,result.stdout,result.stderr)
        return result.stdout.decode()
    def clear_ip():
        calls.write_text('');counter.write_text('0');failure.unlink(missing_ok=True);mode.unlink(missing_ok=True)

    create();seed_session();mode.touch()
    output=down();assert 'down\t5\tok' in output
    expected=('rule del fwmark 0x57560005/0xffffffff lookup 20005 priority 20009',
      '-6 rule del fwmark 0x57560005/0xffffffff lookup 20005 priority 20009',
      'route del 0.0.0.0/0 dev wrvpn5 table 20005','-6 route del ::/0 dev wrvpn5 table 20005',
      'address del 10.8.0.2/32 dev wrvpn5','-6 address del fd00::2/128 dev wrvpn5')
    assert tuple(calls.read_text().splitlines())==expected,calls.read_text()
    assert not (runtime/'5'/'5').exists()
    assert down()==''  # repeated down is idempotent

    seed_session();clear_ip()
    empty_listing=mode.with_suffix('.empty')
    empty_listing.touch()
    mode.touch()
    assert 'down\t5\tok' in down()
    assert tuple(calls.read_text().splitlines())==expected[2:]
    assert not (runtime/'5'/'5').exists()
    empty_listing.unlink()

    seed_session();clear_ip()
    foreign=mode.with_suffix('.foreign')
    foreign.touch()
    assert 'partial' in down(expected=9)
    assert calls.read_text()=='' and (runtime/'5'/'5').exists()
    foreign.unlink()
    mode.touch()
    assert 'down\t5\tok' in down()

    # Rule failure keeps both the owned link session and that family's route;
    # retry after the transient error completes cleanup and releases state.
    seed_session();clear_ip();failure.write_text('1')
    output=down(expected=9);assert 'down\t5\tpartial' in output and 'link=retained' in output
    assert (runtime/'5'/'5').exists()
    assert calls.read_text().splitlines()==[expected[0],expected[1],expected[3]]
    clear_ip();mode.touch();assert 'down\t5\tok' in down();assert not (runtime/'5'/'5').exists()

    # Address failure happens after both policy families are stopped. The
    # runtime session is retained until a retry removes the remaining address.
    seed_session();clear_ip();failure.write_text('5')
    output=down(expected=9);assert 'partial' in output and 'link=retained' in output
    assert (runtime/'5'/'5').exists()
    clear_ip();mode.touch();assert 'down\t5\tok' in down();assert not (runtime/'5'/'5').exists()

    # Runtime snapshot preserves the actually applied config when the stored
    # profile is damaged. If both are invalid, down removes only identity-owned
    # rules and reports UNKNOWN while retaining a present interface/session.
    seed_session();(store/'5').write_bytes(b'corrupt');clear_ip();mode.touch()
    output=down();assert 'down\t5\tok' in output and not (runtime/'5'/'5').exists()

    create(6);seed_session(6);(store/'6').write_bytes(b'corrupt')
    (runtime/'6'/'snapshot-6').write_bytes(b'corrupt');clear_ip();mode.touch()
    output=down(6,expected=12)
    assert 'unknown-config' in output and 'link-retained' not in output
    assert calls.read_text().splitlines()==[
      'rule del fwmark 0x57560006/0xffffffff lookup 20006 priority 20011',
      '-6 rule del fwmark 0x57560006/0xffffffff lookup 20006 priority 20011']
    print('PASS CLI down: idempotent absent objects, IPv4/IPv6 rule-before-route cleanup, partial retry, corrupt-store snapshot fallback and unknown-state refusal; no network objects changed')
