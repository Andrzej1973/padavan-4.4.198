#!/usr/bin/env python3
"""Exercise actual generated allocator/parser; bounded host-only experiment."""
import argparse
import json
import resource
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).parent.resolve()
BODY = r'''
static unsigned callbacks;
static INT32 observed_handler(RTMP_ADAPTER *ad, char *data, UINT32 priv)
{ (void)ad;(void)data;assert(priv==42);callbacks++;return 0; }
int main(void)
{
 unsigned start,i;UINT8 ids[255];UINT32 gens[255];char data[64]={0};
 for(start=0;start<256;start++){
  RTMP_ADAPTER ad={0};TXS_CTL snapshot;UINT8 next=0;UINT32 gen=0;
  ad.TxSCtl.TxSValid=TRUE;ad.TxSCtl.TxSPid=(UINT8)(start+255);
  for(i=0;i<255;i++){
   assert(AddTxSStatus(&ad,TXS_TYPE0,1,0,0,42,42,&ids[i],&gens[i])==0);
   assert(ids[i]!=WR_IOT_NOOWNER_PID);
   for(unsigned j=0;j<i;j++)assert(ids[i]!=ids[j]);
  }
  assert(ad.TxSCtl.TxSStatus[WR_IOT_NOOWNER_PID].State==TXS_UNUSED);
  assert(AddTxSStatus(&ad,TXS_TYPE0,1,0,0,42,42,&next,&gen)==-1);
  memcpy(&snapshot,&ad.TxSCtl,sizeof(snapshot));
  for(i=0;i<32;i++){
   assert(ParseTxSPacket(&ad,WR_IOT_NOOWNER_PID,0,data)==0);
   assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
  }
  assert(ParseTxSPacket(&ad,511,0,data)==-1); /* Never truncate to P. */
  assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
  assert(CancelTxSReservation(&ad,ids[0],gens[0]+1)==-1);
  assert(CancelTxSReservation(&ad,ids[0],gens[0])==0);
  ad.TxSCtl.TxSPid=WR_IOT_NOOWNER_PID;
  assert(AddTxSStatus(&ad,TXS_TYPE0,1,0,0,42,42,&next,&gen)==0);
  assert(next==ids[0]&&next!=WR_IOT_NOOWNER_PID);
  /* Ordinary tracked reports still dispatch and complete their claim. */
  handler=(TXS_TYPE){0};handler.PktPid=1;handler.Format=0;
  handler.TxSHandler=observed_handler;use_handler=1;
  assert(ParseTxSPacket(&ad,next,0,data)==0);
  assert(ad.TxSCtl.TxSStatus[next].State==TXS_UNUSED);
  use_handler=0;
  /* Even contradictory P metadata must not be stolen by a received P.
   * This is a refusal witness, NOT permission for hot conversion. */
  ad.TxSCtl.TxSStatus[WR_IOT_NOOWNER_PID].State=TXS_USED;
  ad.TxSCtl.TxSStatus[WR_IOT_NOOWNER_PID].Generation=123;
  memcpy(&snapshot,&ad.TxSCtl,sizeof(snapshot));
  assert(ParseTxSPacket(&ad,WR_IOT_NOOWNER_PID,1,data)==0);
  assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
  ad.TxSCtl.TxSValid=FALSE;memcpy(&snapshot,&ad.TxSCtl,sizeof(snapshot));
  assert(ParseTxSPacket(&ad,WR_IOT_NOOWNER_PID,0,NULL)==0);
  assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
  ad.TxSCtl.ReservationGeneration=UINT32_MAX;
  memcpy(&snapshot,&ad.TxSCtl,sizeof(snapshot));
  assert(AddTxSStatus(&ad,TXS_TYPE0,1,0,0,42,42,&next,&gen)==-1);
  assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
 }
 assert(callbacks==256);
 puts("PASS actual no-owner allocator/parser: all256 cursors,255-slot exhaustion, duplicate P inertness, no truncation, cancellation and ordinary callback preserved; no TXD/DMA/RF proof");
 return 0;
}
'''


def run(script, *args):
    subprocess.run(['python3', str(HERE / script), *map(str, args)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', type=Path, help='preserved exact vendor Git tar')
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    with tempfile.TemporaryDirectory(prefix='wr-iot-noowner-pid-') as tmp:
        root = Path(tmp)
        pristine = root / 'pristine'
        names = ('tx_rx/txs.c', 'include/mac/mac_mt/mt_mac.h',
                 'mac/mt_mac.c', 'include/mac/mac.h')
        prefix = 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/'
        with tarfile.open(a.archive) as archive:
            for name in names:
                path = pristine / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.extractfile(prefix + name).read())
        stage = root / 'stage'
        run('prepare-txs-status-candidate.py', pristine, stage)
        for script, label in (('prepare-beacon-txs-callback-ledger.py', 'ledger'),
                              ('prepare-txs-claimed-slot.py', 'claimed')):
            overlay = root / label
            run(script, stage, overlay)
            for name in names[:2]:
                (stage / name).write_bytes((overlay / name).read_bytes())
        prototype = root / 'prototype'
        run('prepare-noowner-pid-prototype.py', stage, prototype)
        constants = [line for line in (prototype / names[1]).read_text().splitlines()
                     if line.startswith('#define WR_IOT_NOOWNER_PID ')]
        assert len(constants) == 1
        for tree, label in ((stage, 'negative'), (prototype, 'positive')):
            fixture = root / (label + '.c')
            run('prepare-beacon-txs-ledger-check.py', tree, fixture)
            text = fixture.read_text()
            marker = 'static RTMP_ADAPTER *current;'
            assert text.count(marker) == 1
            # Same extracted actual functions on both sides of the witness.
            fixture.write_text(constants[0] + '\n' +
                               text.split(marker)[0] + BODY)
            exe = root / label
            subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                            '-O2', '-fsanitize=address,undefined', '-fno-pie',
                            '-no-pie', str(fixture), '-o', str(exe)], check=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            if label == 'positive':
                assert result.returncode == 0, result.stderr
                print(result.stdout.strip())
            else:
                assert result.returncode != 0 and 'ids[i]!=WR_IOT_NOOWNER_PID' in result.stderr
                print('PASS negative witness: predecessor can allocate P')
        report = json.loads((prototype / 'noowner-pid-prototype.json').read_text())
        report['host_checks'] = ['all256 allocator cursors', '255 unique owned slots/exhaustion',
                                 'duplicate P leaves whole control state unchanged',
                                 'invalid511 not truncated to P', 'generation-safe cancellation',
                                 'ordinary tracked callback/claimed completion preserved',
                                 'invalid legacy P metadata not consumed by reports',
                                 'generation overflow fails closed',
                                 'predecessor negative witness fails as expected']
        report['asan_ubsan_passed'] = True
        scratch_bytes = sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
        report['scratch_removed_bytes'] = scratch_bytes
    if a.report:
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Removed phase-specific exact-source/overlay/fixture scratch: {scratch_bytes}B; no target or production change')


if __name__ == '__main__':
    main()
