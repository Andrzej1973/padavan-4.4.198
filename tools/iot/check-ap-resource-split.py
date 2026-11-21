#!/usr/bin/env python3
"""Execute extracted AP resource body with optional feature guards on and off."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
a = p.parse_args(); text = a.source.read_text()
start = text.index('static VOID wr_iot_ap_release_resource_body(')
end = text.index('\n}', start) + 2
body = text[start:end]
assert 'NdisFreeSpinLock(&pAd->MacTabLock)' not in text
assert 'return wr_iot_ap_shutdown_body(pAd, TRUE);' in text
assert 'return wr_iot_ap_stop_body(pAd, TRUE);' in text
prefix = r'''
#include <assert.h>
typedef void VOID;
typedef struct {int WdsTabLock,pMulticastFilterTable;} RTMP_ADAPTER;
static int ft,dms,mcast,wds;
#ifdef ENABLE_FEATURES
#define DOT11R_FT_SUPPORT
#define DOT11V_WNM_SUPPORT
#define IGMP_SNOOP_SUPPORT
#define WDS_SUPPORT
#endif
#define FT_Release(p) ((void)(p),ft++)
#define DMSTable_Release(p) ((void)(p),dms++)
#define MultiCastFilterTableReset(p) ((void)(p),mcast++)
#define NdisFreeSpinLock(p) ((void)(p),wds++)
'''
suffix = r'''
int main(void){
 RTMP_ADAPTER a={0};wr_iot_ap_release_resource_body(&a);
#ifdef ENABLE_FEATURES
 assert(ft==1&&dms==2&&mcast==1&&wds==1);
#else
 assert(!ft&&!dms&&!mcast&&!wds);
#endif
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ap-resource-check-') as temporary:
    root = Path(temporary); (root/'check.c').write_text(prefix+body+suffix)
    for flags in ([], ['-DENABLE_FEATURES']):
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,
                        str(root/'check.c'),'-o',str(root/'check')],check=True)
        subprocess.run([str(root/'check')],check=True)
print('PASS extracted AP resources with feature guards on/off; retained MacTabLock; host only')
