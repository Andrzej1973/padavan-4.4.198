#!/usr/bin/env python3
"""Exercise the inherited EN/UK/RU dictionary transform and image gate."""
import runpy
from pathlib import Path


transform = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                               'overlay/padavan-4.4/scripts/localize-inherited-dicts.py'))
entries = transform['ENTRIES']
help_entries = transform['HELP_ENTRIES']
translate = transform['transform_dictionaries']
verify = transform['verify_image_dictionaries']
source_values = {
    'AP_Relay': '【Click to open the configuration wireless relay enhancement script】',
    'AP_Relay_1': 'Wireless repeater enhancements:【It can automatically search and switch the relay signals and channels preconfigured in the script for automatic bridging】',
    'LANHostConfig_x_LDNSServer6_itemdesc': 'This field indicates the IP Address of DNSv6 to provide to clients that request IP Address from DHCP Server. You can leave it blank, then the DNS request will be processed by ZVMODELVZ.',
    'LANHostConfig_DHCPProxyDNSSEC_itemname': 'Enable DNSSEC support?',
    'LANHostConfig_DHCPProxyDNSSEC_itemdesc': 'Enabling this will protect DNS by introducing authentication for DNS servers. This prevents DNS hacking and poisoning. If the authoritative DNS server has DNSSEC, enabling DNSSEC ensures your DNS queries are answered by that DNS server, and not an imposter.',
    'WIFILDPC_itemdesc': 'Enable support for LDPC encoding allows the use of a more modern error correction standard used to ensure high coding reliability and improve coding efficiency. This thing is mandatory for 11ac, optional for 11n. Required for PMF (802.11w).',
}
english = ''.join(f'{entry[0]}={source_values.get(entry[0], "【继承的中文值】")}\n'
                  for entry in entries)
english += ''.join(f'{entry[0]}={source_values.get(entry[0], entry[1])}\n'
                   for entry in help_entries)
stale_help = ''.join(f'{entry[0]}=stale translation\n' for entry in help_entries[::3])
ukrainian, russian = stale_help, stale_help
unrelated = 'LANHostConfig_ForceDNS_itemname_extra=unrelated text must survive\n'
english += unrelated
ukrainian += unrelated
russian += unrelated

source_english, source_ukrainian, source_russian = english, ukrainian, russian
english, ukrainian, russian = translate(english, ukrainian, russian)
verify({'EN.dict': english, 'UK.dict': ukrainian, 'RU.dict': russian})
for content in (english, ukrainian, russian):
    assert 'ZVMODELVZ' not in content and 'WR1200JS' not in content
    assert content.count(unrelated) == 1

try:
    translate(source_english.replace('LANHostConfig_ForceDNS_itemname=',
        'LANHostConfig_ForceDNS_changed='), source_ukrainian, source_russian)
except ValueError as error:
    assert str(error) == 'Inherited help anchor mismatch: LANHostConfig_ForceDNS_itemname'
else:
    raise SystemExit('FAIL changed inherited dictionary anchor was accepted')

try:
    translate(source_english, source_ukrainian + stale_help, source_russian)
except ValueError as error:
    assert 'Duplicate localized help key: UK.dict/' in str(error)
else:
    raise SystemExit('FAIL duplicate source locale help was accepted')

try:
    verify({'EN.dict': english + 'LANHostConfig_ForceDNS_itemname=duplicate\n',
            'UK.dict': ukrainian, 'RU.dict': russian})
except ValueError:
    pass
else:
    raise SystemExit('FAIL duplicate final-image dictionary key was accepted')

try:
    verify({'EN.dict': english, 'UK.dict': ukrainian})
except ValueError:
    pass
else:
    raise SystemExit('FAIL incomplete final-image locale set was accepted')

print(f'PASS inherited dictionaries: {len(entries)} inherited values and '
      f'{len(help_entries)} contextual help keys transform and verify in EN/UK/RU; '
      'changed anchors, duplicate keys and missing locales are rejected')
