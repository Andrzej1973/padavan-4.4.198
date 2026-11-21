#!/usr/bin/env python3
"""Validate full-TU KDP composition and fail-closed prerequisites; no target claim."""
import argparse,hashlib,json,runpy,tempfile,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'ft-kdp-package-composition.py'))['compose']
base={'include/rtmp.h':'BOOLEAN wr_ft_cache_lifetime_initialized;'}
changed=compose(base,a.source,here)
for invalid in ({},changed):
 try:compose(invalid,a.source,here)
 except ValueError:pass
 else:raise AssertionError('missing storage/duplicate accepted')
source=changed['ap/ap_ftkd.c'];caller=changed['ap/ap_cfg.c'];header=changed['include/ft.h']
for name in ('encrypt','decrypt'):
 symbol='wr_ft_kdp_'+name+'_checked('
 assert source.count('BOOLEAN '+symbol)==1
 assert caller.count(symbol)==1 and header.count('BOOLEAN '+symbol)==1
 assert 'FT_KDP_Data'+name.title()+'(' not in caller
assert 'FT_KDP_DataEncrypt(' not in header and 'FT_KDP_DataDecrypt(' not in header
assert header.count('BOOLEAN wr_ft_kdp_key_set_checked(')==1
assert source.count('BOOLEAN wr_ft_kdp_key_set_checked(')==1
assert caller.count('wr_ft_kdp_key_set_checked(')==1
assert 'FT_KDP_CryptKeySet(' not in header
assert source.count('VOID FT_KDP_EventGet(')==1
assert source.count('static VOID wr_ft_kdp_event_native(')==1
assert source.count('wr_ft_kdp_event_fits(')==2
assert caller.count('if(!wr_crypto_ok){FT_MEM_FREE(pAd,pBuffer);break;}')==1
assert caller.count('if(pFtKdp)FT_MEM_FREE(pAd,pFtKdp);')==1
# A newly discovered external function-pointer caller must fail composition.
with tempfile.TemporaryDirectory(prefix='kdp-reference-') as td:
    root=Path(td)
    for name in ('ap/ap_ftkd.c','ap/ap_cfg.c','include/ft.h'):
        dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(a.source/name,dest)
    injected=root/'ap/external.c'
    for symbol in ('FT_KDP_DataEncrypt','FT_KDP_DataDecrypt','FT_KDP_CryptKeySet'):
        injected.write_text('void *legacy_callback = '+symbol+';\n')
        try:compose(base,root,here)
        except ValueError as error:
            assert 'unconverted legacy crypto reference: ap/external.c' in str(error)
        else:raise AssertionError('external legacy function reference accepted: '+symbol)

# Nothing writes the pinned tree; map can feed the future target TU runner.
if a.output:
 a.output.write_text(json.dumps({'scope':'full source-map composition with synthetic cache-storage prerequisite; no full-TU compile',
 'exit_code':0,'prepared_sha256':{n:hashlib.sha256(v.encode('latin1')).hexdigest() for n,v in changed.items()},
 'producer_installed':False,'target_compiled':False,'remaining':['full cache storage/API predecessor chain','all KDP callers/release and AP arbitration','target compilation','image/device verification']},indent=2)+'\n')
print('PASS | KDP source package | full native TU map, paired checked declarations/callers, event admission/span/cleanup, missing predecessor and duplicate refusal; compilation pending')
