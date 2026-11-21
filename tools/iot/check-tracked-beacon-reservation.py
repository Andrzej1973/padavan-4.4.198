#!/usr/bin/env python3
"""Execute actual MT submit function with injected packet/ring/HAL operations.

--archive replays the relevant existing generator fragments on pinned files.
--driver checks the final assembled CI candidate, including publication hook.
Neither mode establishes physical DMA/RF retirement.
"""
import argparse
import ast
import hashlib
import json
import resource
import runpy
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
POLICY = runpy.run_path(str(HERE / 'tracked-beacon-reservation.py'))


def literal(script, name):
    tree = ast.parse((HERE / script).read_text())
    return next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


def predecessor(root, archive):
    out = root / 'bundle'
    driver = out / 'driver'
    names = ('ap/ap_connect.c', 'include/rtmp.h', 'common/cmm_mac_pci.c', 'common/cmm_mac_sdio.c')
    originals = {}
    with tarfile.open(archive) as tar:
        for name in names:
            b = tar.extractfile('trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/' + name).read()
            originals[name] = b
            p = driver / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
    checked, fixture = root / 'checked.c', root / 'old-fixture.c'
    subprocess.run(['python3', str(HERE / 'prepare-beacon-kickout-check.py'),
                    str(driver / names[2]), str(checked), str(fixture)], check=True)
    (driver / names[2]).write_bytes(checked.read_bytes())
    generator = (HERE / 'prepare-radio-queue-candidate.py').read_text()
    tree = ast.parse(generator)
    selected = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'selected')
    env = {'out': out, 'originals': originals, 'records': [], 'hashlib': hashlib}
    exec(compile(ast.Module(body=[selected], type_ignores=[]), 'actual-selected', 'exec'), env)
    begin = generator.index('# Expose the MAC_TX_INFO reservation generation')
    end = generator.index('# The shared PCI kickout must report DMA mapping failure')
    exec(compile(generator[begin:end], 'actual-beacon-generator-fragment', 'exec'), env)
    source = (driver / names[2]).read_text()
    # Apply the exact current publication-hook replacement, without rebuilding
    # unrelated driver trees or reproducing a hand-written function body.
    tree = ast.parse((HERE / 'first-beacon-composition.py').read_text())
    hooks = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == 'one' and len(n.args) == 3
             and isinstance(n.args[0], ast.Constant) and n.args[0].value == names[2]
             and isinstance(n.args[1], ast.Constant) and 'BCN_TX_WRITE_TO_DMA' in n.args[1].value]
    assert len(hooks) == 1
    old, new = map(ast.literal_eval, hooks[0].args[1:])
    assert source.count(old) == 1
    return source.replace(old, new, 1)


def fixture_text(source):
    prefix = literal('prepare-beacon-kickout-check.py', 'prefix')
    prefix = prefix.replace('typedef void VOID;', 'typedef void VOID;\ntypedef int INT32;\ntypedef unsigned char UINT8;\ntypedef unsigned int UINT32;\ntypedef struct {UINT8 pid;UINT32 generation;} WR_BCN_TXS_RESERVATION;')
    prefix = prefix.replace('INT tx_hw_hdr_len;', 'INT tx_hw_hdr_len,hif_type;')
    prefix = prefix.replace('INT BcnRingLock;unsigned int flags;', 'INT mt,BcnRingLock;unsigned int flags;struct {unsigned int TxCpuIdx,TxSwFreeIdx;} BcnRing;')
    prefix = prefix.replace('static void HAL_KickOutMgmtTx(', 'static int HAL_KickOutMgmtTx(')
    prefix = prefix.replace('kicks++;\n}', 'kicks++;return hal_result;\n}')
    prefix = prefix.replace('if(mode==4)', 'if(mode==5){current_ad->ApCfg.BssidNum=3;}\n if(mode==4)')
    prefix = prefix.replace('static INT mode,held,locks,unlocks,kicks;', 'static INT mode,held,locks,unlocks,kicks,hal_result,cancels,cancel_result,publications;')
    prefix += r'''
#define RTMP_PCI_SUPPORT 1
#define BCN_RING_SIZE 4
#define HIF_MT 1
#define IS_MT7603(ad) ((ad)->mt)
static int CancelTxSReservation(RTMP_ADAPTER *ad,UINT8 pid,UINT32 generation){
 (void)ad;assert(pid==37&&generation==13);cancels++;return cancel_result;
}
static void wr_iot_first_beacon_published_locked(RTMP_ADAPTER *ad,INT idx){
 (void)ad;(void)idx;assert(held);publications++;
}
'''
    _, _, function = POLICY['selected'](source)
    function = function.replace('{\n', '{\n (void)UpdatePos;\n', 1)
    return prefix + function + r'''
static RTMP_ADAPTER ad;static PNDIS_PACKET pkt;
static void reset(void){
 memset(&ad,0,sizeof(ad));memset(&pkt,0,sizeof(pkt));
 ad.mt=1;ad.ApCfg.BssidNum=3;ad.chipCap.hif_type=HIF_MT;ad.chipCap.tx_hw_hdr_len=4;
 for(int i=0;i<3;i++){ad.ApCfg.MBSSID[i].running=1;
  ad.ApCfg.MBSSID[i].bcn_buf.BeaconPkt=&pkt;ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq=1;}
 current_ad=&ad;mode=held=locks=unlocks=kicks=hal_result=cancels=cancel_result=publications=0;
}
int main(void){
 WR_BCN_TXS_RESERVATION token={37,13};
 for(int mt=0;mt<2;mt++)for(int hif=0;hif<2;hif++)for(int count=3;count<=4;count++)
 for(int bss=0;bss<3;bss++)for(int valid=0;valid<2;valid++){
  int refuse=mt&&hif&&count==3&&bss==2&&!valid;
  reset();ad.mt=mt;ad.chipCap.hif_type=hif;ad.ApCfg.BssidNum=count;
  token.generation=valid?13:0;
  assert(RT28xx_UpdateBeaconToAsic(&ad,bss,8,0,token)==(refuse?-1:0));
  assert(kicks==!refuse&&publications==!refuse&&!cancels&&!held&&locks==unlocks);
  if(refuse)assert(!locks&&!pkt.len&&ad.ApCfg.MBSSID[bss].bcn_buf.bcn_state!=BCN_TX_WRITE_TO_DMA);
 }
 reset();ad.ApCfg.BssidNum=4;mode=5;token.generation=0;
 assert(RT28xx_UpdateBeaconToAsic(&ad,2,8,0,token)==-1);
 assert(!kicks&&!publications&&!cancels&&!held&&locks==1&&unlocks==1);
 assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state!=BCN_TX_WRITE_TO_DMA);
 token.generation=13;
 for(int failure=1;failure<=3;failure++){
  reset();
  if(failure==1)ad.BcnRing.TxSwFreeIdx=1;
  else hal_result=-1;
  if(failure==3)cancel_result=-1;
  assert(RT28xx_UpdateBeaconToAsic(&ad,2,8,0,token)==(failure==3?-2:-1));
  assert(cancels==1&&kicks==(failure!=1)&&!publications&&!held&&locks==unlocks);
  assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state!=BCN_TX_WRITE_TO_DMA);
 }
 puts("PASS actual tracked beacon submit: initial zero-token scope refuses before packet/ring; locked layout recheck blocks HAL/publication; other scopes and cancellation preserved; injected hardware only");
}
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--archive', type=Path)
    group.add_argument('--driver', type=Path)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    with tempfile.TemporaryDirectory(prefix='wr-iot-tracked-beacon-') as tmp:
        root = Path(tmp)
        source = predecessor(root, a.archive) if a.archive else (a.driver / 'common/cmm_mac_pci.c').read_text()
        if a.archive:
            variants = [('negative', source), ('positive', POLICY['compose'](source))]
        else:
            variants = [('positive', source)]
        for label, text in variants:
            _, _, function = POLICY['selected'](text)
            if label == 'positive':
                assert function.count(POLICY['GUARD']) == 1
                assert function.count(POLICY['LOCKED_GUARD']) == 1
                assert function.index(POLICY['GUARD']) < function.index('HAL_KickOutMgmtTx(')
                assert function.index(POLICY['GUARD']) < function.index('wr_iot_first_beacon_published_locked(')
            fixture, exe = root / (label + '.c'), root / label
            fixture.write_text(fixture_text(text))
            subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2',
                            '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                            str(fixture), '-o', str(exe)], check=True)
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            if label == 'negative':
                assert r.returncode != 0 and 'refuse?-1:0' in r.stderr, r.stderr
                print('PASS predecessor witness: zero tracked token could publish')
            else:
                assert r.returncode == 0, r.stderr
                print(r.stdout.strip())
        size = sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
    print(f'Removed tracked-beacon phase scratch: {size}B; no RF/runtime claim')


if __name__ == '__main__':
    main()
