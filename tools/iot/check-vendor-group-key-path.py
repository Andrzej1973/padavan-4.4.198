"""Execute native vendor AES key writer/address lookup with synthetic MMIO.

Read-only source investigation, not hardware readback or an installed fix.
No MCU transport implementation is supplied: adding such a call breaks linkage.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import tempfile


def extract(text, signature):
    starts = list(re.finditer(signature, text, re.M))
    if len(starts) != 1:
        raise ValueError('Unique vendor function required: ' + signature)
    start = starts[0].start()
    # This SDK has unindented inner braces and mutually exclusive #ifdef
    # branches. Match its next top-level declaration/comment boundary rather
    # than truncating at the first unindented brace or counting both branches.
    finish = re.search(r'\n}\s*\n\s*(?=/\*|INT\s)', text[starts[0].end():])
    if not finish:
        raise ValueError('Vendor function boundary changed')
    end = starts[0].end() + finish.start() + 2
    return text[start:end]


def check(root):
    names = ('hw_ctrl/cmm_asic_mt.c', 'mac/mt_mac.c', 'include/wpa_cmm.h',
             'include/rtmp_def.h', 'include/mac/mac_mt/wf_wtblon.h')
    blobs = {}
    for name in names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular vendor source required: ' + name)
        blobs[name] = path.read_bytes()
    text = {name: data.decode() for name, data in blobs.items()}
    writer = extract(text[names[0]], r'^VOID CmdProcAddRemoveKey\([^;]+?\)\s*\{')
    lookup = extract(text[names[1]], r'^INT mt_wtbl_get_entry234\([^;]+?\)\s*\{')
    header = text[names[2]]
    start = header.index('typedef struct _CMD_802_11_KEY {')
    end = header.index('} CMD_802_11_KEY, *P_CMD_802_11_KEY;', start)
    key_type = header[start:end + len('} CMD_802_11_KEY, *P_CMD_802_11_KEY;')]
    cipher_definitions = []
    for name in ('WEP64', 'WEP128', 'TKIP', 'AES', 'SMS4', 'WEP152', 'BIP'):
        rows = re.findall(r'^#define CIPHER_' + name + r'\s+\d+\s*$', text[names[3]], re.M)
        if len(rows) != 1:
            raise ValueError('Cipher definition changed: ' + name)
        cipher_definitions.append(rows[0])
    prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define IN
#define VOID void
#define FALSE 0
#define TRUE 1
#define CONFIG_AP_SUPPORT
#define OPMODE_AP 1
#define SHAREDKEYTABLE 0
#define MCAST_WCID 0
#define RT_DEBUG_OFF 0
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_INFO 0
#define DBGPRINT(level,args) do{(void)(level);}while(0)
#define NdisZeroMemory(p,n) memset((p),0,(n))
typedef unsigned char UCHAR,UINT8,*PUCHAR;
typedef unsigned int UINT32,UINT;
typedef int INT;
'''
    actors = r'''
struct wtbl_entry {
 struct { union WTBL_1_DW0 wtbl_1_d0; union WTBL_1_DW1 wtbl_1_d1;
          union WTBL_1_DW2 wtbl_1_d2; } wtbl_1;
 unsigned int wtbl_addr[4],wtbl_fid[4],wtbl_eid[4],wtbl_idx;
};
struct rtmp_mac_ctrl { unsigned int wtbl_entry_cnt[4],wtbl_base_addr[4],
 wtbl_entry_size[4],wtbl_base_fid[4],page_size; };
typedef struct { struct rtmp_mac_ctrl mac_ctrl; int OpMode; } RTMP_ADAPTER,*PRTMP_ADAPTER;
typedef struct { unsigned char Key[32],TxMic[8],RxMic[8],CipherAlg; } CIPHER_KEY,*PCIPHER_KEY;
static unsigned int registers[0x10000],addresses[32],values[32],writes,ignore_write;
static void mmio_write(unsigned int address,unsigned int value){
 assert(!(address&3)&&address/4<sizeof(registers)/sizeof(registers[0])&&writes<32);
 addresses[writes]=address;values[writes]=value;writes++;
 if(writes!=ignore_write)registers[address/4]=value;
}
static unsigned int mmio_read(unsigned int address){
 assert(!(address&3)&&address/4<sizeof(registers)/sizeof(registers[0]));
 return registers[address/4];
}
#define RTMP_IO_WRITE32(ad,address,value) do{(void)(ad);mmio_write((address),(value));}while(0)
#define RTMP_IO_READ32(ad,address,value) do{(void)(ad);*(value)=mmio_read(address);}while(0)
'''
    cases = r'''
static void reset(void){memset(registers,0,sizeof(registers));writes=ignore_write=0;}
int main(void){
 RTMP_ADAPTER ad={.OpMode=OPMODE_AP,.mac_ctrl={.wtbl_entry_cnt={8,8,8,8},
  .wtbl_base_addr={0x1000,0x2000,0x3000,0x4000},.wtbl_entry_size={32,64,32,32},.page_size=256}};
 CIPHER_KEY key={.CipherAlg=CIPHER_AES};unsigned char peer[6]={255,255,255,255,255,255};
 for(unsigned int i=0;i<16;i++)key.Key[i]=(unsigned char)(i+1);
 reset();CmdProcAddRemoveKey(&ad,0,2,1,4,SHAREDKEYTABLE,&key,peer);
 assert(writes==7);
 for(unsigned int i=0;i<4;i++){
  assert(addresses[i]==0x3080+4*i);
  assert(values[i]==(0x04030201U+0x04040404U*i));
 }
 assert(addresses[4]==0x1088&&addresses[5]==0x1084&&addresses[6]==0x1080);
 union WTBL_1_DW0 d0={.word=registers[0x1080/4]};
 union WTBL_1_DW2 d2={.word=registers[0x1088/4]};
 assert(d0.field.kid==1&&!d0.field.rv&&!d0.field.rkv&&d2.field.adm&&d2.field.cipher_suit==4);
 /* Exhaust the high-byte range, with high bits in the lower octets too. */
 for(unsigned int high=0;high<256;high++){
  peer[0]=0x80;peer[1]=0xff;peer[2]=0x81;peer[3]=(unsigned char)high;
  reset();CmdProcAddRemoveKey(&ad,0,2,1,4,SHAREDKEYTABLE,&key,peer);
  assert(writes==7&&values[5]==(0x0081ff80U|((uint32_t)high<<24)));
 }
 /* No return value reports a lost MMIO store. */
 reset();ignore_write=2;CmdProcAddRemoveKey(&ad,0,2,1,4,SHAREDKEYTABLE,&key,peer);
 assert(writes==7&&registers[0x3084/4]==0&&registers[0x3080/4]==0x04030201U);
 /* The native lookup clamps an out-of-range index, while key data uses raw WCID. */
 reset();CmdProcAddRemoveKey(&ad,0,2,1,9,SHAREDKEYTABLE,&key,peer);
 assert(writes==7&&addresses[0]==0x3120&&addresses[6]==0x10e0);
 /* BSS argument does not bind a caller-supplied WCID to that BSS. */
 reset();CmdProcAddRemoveKey(&ad,0,1,1,4,SHAREDKEYTABLE,&key,peer);
 assert(writes==7&&addresses[0]==0x3080&&addresses[6]==0x1080);
 reset();ad.mac_ctrl.wtbl_entry_cnt[0]=0;
 CmdProcAddRemoveKey(&ad,0,2,1,4,SHAREDKEYTABLE,&key,peer);assert(!writes);
 ad.mac_ctrl.wtbl_entry_cnt[0]=8;key.CipherAlg=255;
 CmdProcAddRemoveKey(&ad,0,2,1,4,SHAREDKEYTABLE,&key,peer);assert(!writes);
 puts("PASS corrected vendor AES group-key writer/native WTBL lookup: direct stores, selected-address trace, all 256 high octets, hidden failed store, WCID clamp and absent BSS binding; synthetic MMIO, no hardware/device acceptance");
}
'''
    compose = runpy.run_path(str(Path(__file__).with_name('group-key-byte-packing.py')))['compose']
    corrected_writer = compose(writer)
    for invalid in (corrected_writer, writer.replace('CmdKey.aucPeerAddr[3] << 24', 'CmdKey.aucPeerAddr[3] << 23', 1)):
        try:
            compose(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Packing source drift/repeated preparation accepted')
    with tempfile.TemporaryDirectory(prefix='wr-vendor-group-key-') as directory:
        unit = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        environment = dict(os.environ, UBSAN_OPTIONS='halt_on_error=1')
        for mode, body in [('native', writer), ('corrected', corrected_writer)]:
            unit.write_text(prefix + text[names[4]] + '\n' + '\n'.join(cipher_definitions) +
                            '\n' + key_type + '\n' + actors + lookup + '\n' + body + '\n' + cases)
            subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2',
                            '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                            str(unit), '-o', str(binary)], check=True)
            if mode == 'native':
                result = subprocess.run([str(binary)], env=environment, capture_output=True,
                                        text=True, timeout=15)
                if not result.returncode or 'left shift of 255 by 24' not in result.stderr:
                    raise AssertionError('Expected native broadcast-byte signed-shift UB not reproduced')
                print('CONFIRMED native broadcast-byte packing UB; baseline UBSan execution stopped', flush=True)
            else:
                subprocess.run([str(binary)], check=True, env=environment, timeout=15)
    return {'source_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in blobs.items()},
            'source_git_blob_sha1': {name: hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                                     for name, data in blobs.items()},
            'native_function_sha256': {name: hashlib.sha256(body.encode()).hexdigest()
                                      for name, body in [('CmdProcAddRemoveKey', writer), ('mt_wtbl_get_entry234', lookup)]},
            'native_signed_shift_ub_reproduced': True,
            'corrected_writer_sha256': hashlib.sha256(corrected_writer.encode()).hexdigest(),
            'packing_composer_sha256': hashlib.sha256(Path(__file__).with_name('group-key-byte-packing.py').read_bytes()).hexdigest(),
            'corrected_host_cases_passed': True, 'hardware_mmio_verified': False,
            'production_installed': False, 'runtime_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('New output required')
    result = check(args.driver)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
