"""Prepare cache API leases. Not installed; AP init/stop binding remains required.

The dedicated adapter lifetime lock must be initialized before publication and
freed only after all adapter callbacks stop. It is released before native cache
work, including allocation/free. No assumption that MacTabLock is unheld.
"""

GATES = '''
static BOOLEAN wr_ft_cache_api_enter(RTMP_ADAPTER *pAd,
 struct wr_ft_cache_lease *lease)
{
 BOOLEAN ok;
 if(!pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_enter(&pAd->wr_ft_cache_lifetime,lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return ok;
}
static BOOLEAN wr_ft_cache_api_leave(RTMP_ADAPTER *pAd,
 struct wr_ft_cache_lease *lease)
{
 BOOLEAN ok;
 if(!pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 ok=wr_ft_cache_leave(&pAd->wr_ft_cache_lifetime,lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return ok;
}
'''


def compose_api(source):
    if 'wr_ft_cache_api_enter(' in source:
        raise ValueError('cache API lifetime already composed')
    specs = (
        ('snapshot', 'const UCHAR *name, FT_R1HK_ENTRY *snapshot', 'name,snapshot'),
        ('store', 'const FT_R1HK_ENTRY *value', 'value'),
        ('delete', 'const UCHAR *name', 'name'),
    )
    wrappers = []
    for suffix, params, args in specs:
        name = 'wr_ft_r1kh_' + suffix
        anchor = 'BOOLEAN ' + name + '(RTMP_ADAPTER *pAd,'
        if source.count(anchor) != 1:
            raise ValueError('exact snapshot API missing: ' + name)
        source = source.replace(anchor, 'static BOOLEAN ' + name + '_native(RTMP_ADAPTER *pAd,', 1)
        clear = ' if(snapshot)NdisZeroMemory(snapshot,sizeof(*snapshot));\n' if suffix == 'snapshot' else ''
        wrappers.append('BOOLEAN ' + name + '(RTMP_ADAPTER *pAd, ' + params + ')\n{\n'
            ' struct wr_ft_cache_lease lease={0};\n BOOLEAN result;\n' + clear +
            ' if(!pAd||!wr_ft_cache_api_enter(pAd,&lease))return FALSE;\n'
            ' result=' + name + '_native(pAd,' + args + ');\n'
            ' if(!wr_ft_cache_api_leave(pAd,&lease))return FALSE;\n'
            ' return result;\n}\n')
    # Publish wrappers before store_fields, which calls the public store API.
    anchor = '/* Build a fully owned value and atomically replace/insert it. */'
    if source.count(anchor) != 1:
        raise ValueError('store-fields API anchor changed')
    return source.replace(anchor, GATES + '\n'.join(wrappers) + '\n' + anchor, 1)


def compose_maintenance(source):
    """Keep native maintenance byte-identical behind the cache lifetime gate.

    This does not fix its cache-lock-to-station/MLME ordering. It only prevents
    cache destroy while the native callback is running, including early return.
    """
    if 'wr_ft_cache_api_enter(' not in source:
        raise ValueError('maintenance lifetime requires cache API gates')
    if 'wr_ft_r1kh_maintenance_native(' in source:
        raise ValueError('maintenance lifetime already composed')
    signature = 'VOID FT_R1KHInfoMaintenance('
    if source.count(signature) != 1:
        raise ValueError('native maintenance definition changed')
    start = source.index(signature)
    # Pinned vendor top-level function ends at a column-zero closing brace.
    end = source.index('\n}', start) + 2
    native = source[start:end]
    if native.count('RTMP_SEM_LOCK(') != 1 or native.count('RTMP_SEM_UNLOCK(') != 1:
        raise ValueError('maintenance cache lock shape changed')
    wrapper = '''
VOID FT_R1KHInfoMaintenance(IN PRTMP_ADAPTER pAd)
{
 struct wr_ft_cache_lease lease={0};
 if(!pAd||!wr_ft_cache_api_enter(pAd,&lease))return;
 wr_ft_r1kh_maintenance_native(pAd);
 (void)wr_ft_cache_api_leave(pAd,&lease);
}
'''
    return (source[:start] + native.replace(signature,
        'static VOID wr_ft_r1kh_maintenance_native(', 1) + '\n' + wrapper + source[end:])
