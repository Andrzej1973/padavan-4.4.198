#!/usr/bin/env python3
"""Exercise actual allocator/parser and selected TXD branch; host experiment."""
import argparse
import json
import resource
import runpy
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).parent.resolve()
BODY = r'''
static unsigned callbacks;
static INT32 observed_handler(RTMP_ADAPTER *ad, char *data, UINT32 priv)
{ (void)ad;(void)data;assert(priv==42);callbacks++;return 0; }
static UINT32 late_report_priv;
static INT32 old_report_handler(RTMP_ADAPTER *ad,char *data,UINT32 priv)
{ (void)ad;(void)data;late_report_priv=priv;return 0; }
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
 /* Conditional transition counterexample: a duplicate old tracked ra2
  * report is injected after its PID was completed and reused by Main.
  * This does not assert that silicon actually generates duplicates. */
 {
  RTMP_ADAPTER ad={0};UINT8 old_pid,new_pid;UINT32 old_gen,new_gen;
  ad.TxSCtl.TxSValid=TRUE;ad.TxSCtl.TxSPid=7;
  assert(AddTxSStatus(&ad,TXS_TYPE1,0,FC_TYPE_MGMT,SUBTYPE_BEACON,42,2,&old_pid,&old_gen)==0);
  assert(old_pid!=WR_IOT_NOOWNER_PID);
  handler=(TXS_TYPE){0};handler.PktType=FC_TYPE_MGMT;
  handler.PktSubType=SUBTYPE_BEACON;handler.Format=0;
  handler.TxSHandler=old_report_handler;use_handler=1;
  assert(ParseTxSPacket(&ad,old_pid,0,data)==0&&late_report_priv==2);
  ad.TxSCtl.TxSPid=old_pid;
  assert(AddTxSStatus(&ad,TXS_TYPE1,0,FC_TYPE_MGMT,SUBTYPE_BEACON,42,0,&new_pid,&new_gen)==0);
  assert(new_pid==old_pid&&new_gen!=old_gen);
  assert(ParseTxSPacket(&ad,old_pid,0,data)==0&&late_report_priv==0);
  assert(ad.TxSCtl.TxSStatus[new_pid].State==TXS_UNUSED);
  use_handler=0;
  puts("CONFIRMED conditional old-nonP counterexample: new P invariant does not protect a reused tracked Main PID from an injected old ra2 report; no measured firmware duplicate claimed");
 }
 puts("PASS actual no-owner allocator/parser: all256 cursors,255-slot exhaustion, duplicate P inertness, no truncation, cancellation and ordinary callback preserved; no TXD/DMA/RF proof");
 return 0;
}
'''

ROUTE_MODELS = r'''
#define HIF_MT 1
#define Q_IDX_BCN 2
#define IS_MT7603(ad) ((ad)->mt)
struct mac_info {unsigned bss_idx,TxSPriv,q_idx,WCID,PID;
 UINT32 TxSReservationGeneration;UINT8 TxSReservationPid;};
struct word2 {unsigned frm_type,sub_type;};
struct word5 {unsigned pid,tx_status_2_host;};
struct word6 {unsigned tx_rate;};
static void route(RTMP_ADAPTER *pAd,struct mac_info *info,
 struct word2 *txd_2,struct word5 *txd_5,struct word6 *txd_6){
 UINT8 status_pid;UINT32 status_generation;
'''
ROUTE_MAIN = r'''
}
int main(void){
 for(unsigned mask=0;mask<512;mask++)for(unsigned bss=0;bss<3;bss++)
 for(unsigned full=0;full<2;full++){
  RTMP_ADAPTER ad={0};TXS_CTL snapshot;struct mac_info info={0};
  struct word2 d2={0};struct word5 d5={0};struct word6 d6={42};
  ad.mt=!!(mask&1);ad.chipCap.hif_type=!!(mask&2);
  ad.ApCfg.BssidNum=mask&4?3:4;info.bss_idx=bss;
  info.q_idx=mask&8?Q_IDX_BCN:99;info.TxSPriv=mask&16?2:1;
  info.WCID=mask&32?0:1;info.PID=mask&64?0:1;
  d2.frm_type=mask&128?FC_TYPE_MGMT:2;
  d2.sub_type=mask&256?SUBTYPE_BEACON:9;
  if(full)for(unsigned i=0;i<256;i++)if(i!=WR_IOT_NOOWNER_PID)
   ad.TxSCtl.TxSStatus[i].State=TXS_USED;
  memcpy(&snapshot,&ad.TxSCtl,sizeof(snapshot));
  route(&ad,&info,&d2,&d5,&d6);
  if(mask==511&&bss==2){
   assert(d5.pid==WR_IOT_NOOWNER_PID&&d5.tx_status_2_host==1);
   assert(info.TxSReservationPid==WR_IOT_NOOWNER_PID&&!info.TxSReservationGeneration);
   assert(memcmp(&snapshot,&ad.TxSCtl,sizeof(snapshot))==0);
  }else if(!full){
   assert(d5.pid!=WR_IOT_NOOWNER_PID&&d5.tx_status_2_host==1);
   assert(info.TxSReservationPid==d5.pid&&info.TxSReservationGeneration==1);
   assert(ad.TxSCtl.ReservationGeneration==1);
  }else{
   assert(!d5.tx_status_2_host&&!info.TxSReservationGeneration);
   assert(ad.TxSCtl.TxSFailCount==snapshot.TxSFailCount+1);
  }
 }
 puts("PASS actual long-TXD branch:3072 scope/pool cases, only exact ra2 beacon selects non-owning PID without allocation; tracked alternatives preserved; submit/DMA/RF unbound");
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
            extracted = constants[0] + '\n' + text.split(marker)[0]
            fixture.write_text(extracted + BODY)
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
        # Exercise the newly generated actual checked-callsite branch with
        # the actual allocator functions, not a mirrored selection predicate.
        model = 'typedef struct adapter {TXS_CTL TxSCtl;} RTMP_ADAPTER;'
        assert extracted.count(model) == 1
        extracted = extracted.replace(model, 'typedef struct adapter {TXS_CTL TxSCtl;int mt;'
                                      'struct {unsigned hif_type;} chipCap;'
                                      'struct {unsigned BssidNum;} ApCfg;} RTMP_ADAPTER;')
        policy = runpy.run_path(str(HERE / 'prepare-noowner-pid-prototype.py'))
        mac = (prototype / names[2]).read_text()
        branch = mac[mac.index(policy['ROUTE_START']):mac.index(policy['ROUTE_END'])]
        fixture, exe = root / 'route.c', root / 'route'
        fixture.write_text(extracted + ROUTE_MODELS + branch + ROUTE_MAIN)
        subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2',
                        '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                        str(fixture), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
        report = json.loads((prototype / 'noowner-pid-prototype.json').read_text())
        report['host_checks'] = ['all256 allocator cursors', '255 unique owned slots/exhaustion',
                                 'duplicate P leaves whole control state unchanged',
                                 'invalid511 not truncated to P', 'generation-safe cancellation',
                                 'ordinary tracked callback/claimed completion preserved',
                                 'invalid legacy P metadata not consumed by reports',
                                 'generation overflow fails closed',
                                 'predecessor negative witness fails as expected',
                                 'actual long-TXD branch:3072 scope/pool cases',
                                 'conditional old non-P ra2 report can consume reused Main PID']
        report['old_tracked_ra2_reports_retired'] = False
        report['asan_ubsan_passed'] = True
        scratch_bytes = sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
        report['scratch_removed_bytes'] = scratch_bytes
    if a.report:
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Removed phase-specific exact-source/overlay/fixture scratch: {scratch_bytes}B; no target or production change')


if __name__ == '__main__':
    main()
