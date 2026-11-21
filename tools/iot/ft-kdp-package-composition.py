"""Compose prepared KDP fragments in memory only. Does not install a build.

Prerequisite cache storage/admission and full KDP/AP retirement are external.
"""
import runpy

def replace_one(text,old,new):
    if text.count(old)!=1:raise ValueError('KDP package native anchor changed')
    return text.replace(old,new,1)

def function(text,signature):
    if text.count(signature)!=1:raise ValueError('KDP function definition changed')
    start=text.index(signature);end=text.index('\n}',start)+2
    return text[start:end]

def compose(changes,src,local):
    result=dict(changes)
    def get(name):return result.get(name,(src/name).read_text(encoding='latin1'))
    source=get('ap/ap_ftkd.c');caller=get('ap/ap_cfg.c');header=get('include/ft.h')
    adapter=result.get('include/rtmp.h','')
    if 'wr_ft_cache_lifetime_initialized;' not in adapter:
        raise ValueError('KDP package requires prepared cache storage')
    if 'wr_ft_kdp_encrypt_checked(' in source or 'wr_ft_kdp_encrypt_checked(' in header:
        raise ValueError('KDP package already prepared')
    event=runpy.run_path(str(local/'ft-kdp-event-output-composition.py'))
    start=caller.index('FT_KDP_SIGNAL *pFtKdp;')
    end=caller.index('\n\t\t\t}',caller.index('/* no event is queued */',start))
    fragment=caller[start:end]
    initialized,output=event['compose'](source,fragment)
    original=function(source,'VOID TYPE_FUNC FT_KDP_EventGet(')
    source=replace_one(source,original,event['compose_admission'](initialized))
    caller=replace_one(caller,fragment,output)
    start=caller.index('\t\tcase RT_FT_DATA_ENCRYPT:')
    end=caller.index('\n\t\tcase RT_OID_802_11R_INFO:',start)
    fragment=caller[start:end]
    crypto,output=runpy.run_path(str(local/'ft-kdp-crypto-composition.py'))['compose'](source,fragment)
    for name in ('Encrypt','Decrypt'):
        original=function(source,'VOID TYPE_FUNC FT_KDP_Data'+name+'(')
        source=replace_one(source,original,'')
    source+='\n#ifdef DOT11R_FT_SUPPORT\n'+crypto+'\n#endif\n'
    caller=replace_one(caller,fragment,output)
    source=runpy.run_path(str(local/'ft-kdp-event-span-composition.py'))['compose'](source)
    source,caller,header=runpy.run_path(str(local/'ft-kdp-key-writer-composition.py'))['compose'](source,caller,header)
    source=replace_one(source,'#include "rt_config.h"',
        '#include "rt_config.h"\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-kdp-event-span.h"\n#endif')
    declarations='''BOOLEAN wr_ft_kdp_encrypt_checked(RTMP_ADAPTER *,UCHAR *,UINT32 *);
BOOLEAN wr_ft_kdp_decrypt_checked(RTMP_ADAPTER *,UCHAR *,UINT32 *);
'''
    for operation in ('Encrypt','Decrypt'):
        signature='VOID FT_KDP_Data'+operation+'('
        if header.count(signature)!=1:raise ValueError('legacy crypto prototype changed')
        start=header.index(signature);end=header.index(';',start)+1
        header=header[:start]+(declarations if operation=='Encrypt' else '')+header[end:]
    # Any unconverted reference would link to a removed void API. Inspect all
    # native C/header files, overlaying this exact prepared source map.
    import re
    prepared=dict(result,**{'ap/ap_ftkd.c':source,'ap/ap_cfg.c':caller,'include/ft.h':header})
    for path in src.rglob('*'):
        if not path.is_file() or path.suffix not in ('.c','.h'):continue
        name=str(path.relative_to(src))
        text=prepared.get(name)
        if text is None:text=path.read_text(encoding='latin1')
        # Reject identifier references, including function-pointer uses. Comments
        # may mention the old name without creating a native dependency.
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
        if re.search(r'\bFT_KDP_(?:Data(?:Encrypt|Decrypt)|CryptKeySet)\b',text):
            raise ValueError('unconverted legacy crypto reference: '+name)
    result.update({'ap/ap_ftkd.c':source,'ap/ap_cfg.c':caller,'include/ft.h':header,
                   'include/ft-kdp-event-span.h':(local/'ft-kdp-event-span.h').read_text()})
    return result
