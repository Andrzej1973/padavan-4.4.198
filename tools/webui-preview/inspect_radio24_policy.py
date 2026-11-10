#!/usr/bin/env python3
"""Extract pinned RC/MT7603 channel policy evidence; never establish live regulatory acceptance."""
import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
paths={'rc':'trunk/user/rc/ralink.c',
       'driver':'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/common/rt_channel.c',
       'ioctl':'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/os/linux/ap_ioctl.c',
       'classic':'trunk/user/www/n56u_ribbon_fixed/wireless_2g.js'}
with tarfile.open(args.archive) as archive:
    raw={name:archive.extractfile(path).read() for name,path in paths.items()}
source={name:data.decode(errors='strict') for name,data in raw.items()}
rc=source['rc'].split('ralink_cc_table[] = {',1)[1].split('};',1)[0]
countries={code:int(region) for code,region in re.findall(r'\{\s*"([A-Z]{2})"\s*,\s*(\d+)\s*,',rc)}
regions={}
for region,body in re.findall(r'CH_DESC Country_Region(\d+)_ChDesc_2GHZ\[\]\s*=\s*\{(.*?)\n\};',source['driver'],re.S):
    entries=re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_]+)\s*\}',body)
    if not entries:raise ValueError('No parsed channel descriptors for region '+region)
    regions[region]=[{'first':int(first),'count':int(count),'property':prop} for first,count,prop in entries]
def channels(country):
    region=str(countries[country])
    return [channel for entry in regions[region] for channel in range(entry['first'],entry['first']+entry['count'])]
assert channels('US')==list(range(1,12))
assert channels('GB')==channels('UA')==channels('JP')==list(range(1,14))
assert 14 in channels('DB')
block=source['ioctl'].split('case SIOCGIWRANGE:',1)[1].split('case RT_PRIV_IOCTL:',1)[0]
assert 'memset(prange, 0' in block and 'copy_to_user' in block
assert 'num_frequency' not in block and 'num_channels' not in block and 'prange->freq' not in block
result={'source_sha':'c25283e915a2a00a763774dd255b14aff997285e',
        'source_files':{name:{'path':paths[name],'sha256':hashlib.sha256(data).hexdigest()} for name,data in raw.items()},
        'country_to_region':countries,'driver_region_descriptors':regions,
        'examples':{code:channels(code) for code in ('US','GB','UA','JP','DB')},
        'SIOCGIWRANGE_has_channel_list':False,
        'limits':['Source RC and driver descriptors only; EEPROM/SKU/runtime effective channel list unverified',
                  'Unknown-country RC fallback is not admission evidence',
                  'Debug DB and channel14 must not be exposed by Modern',
                  'Do not infer active channel list from SIOCGIWRANGE; vendor handler leaves it zeroed'],
        'runtime_verified':False,'radio_apply_enabled':False}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print('PASS pinned source extraction: country/region descriptors and empty range-channel reply; live radio admission unverified')
