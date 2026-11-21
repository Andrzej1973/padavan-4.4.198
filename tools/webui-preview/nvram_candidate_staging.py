from pathlib import Path

def stage(production,target):
    production,target=Path(production),Path(target)
    names=['nvram.c','nvram_linux.c','Makefile']
    pending={}
    for name in names:
        source=production/name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Missing or symlinked NVRAM source: '+name)
        pending[name]=source.read_bytes()
    marker=b'#include "wr-nvram-flash-wire.h"'
    if marker in pending['nvram_linux.c']:
        if pending['nvram_linux.c'].count(marker)!=1:
            raise ValueError('Native flash wire include count changed')
        name='wr-nvram-flash-wire.h';source=production/name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Missing or symlinked native flash wire dependency')
        content=source.read_bytes()
        if content!=(Path(__file__).resolve().parents[1]/'iot/native-flash-wire.h').read_bytes():
            raise ValueError('Native flash wire dependency differs from reviewed ABI')
        pending[name]=content
    for name in pending:
        destination=target/name
        if destination.exists() or destination.is_symlink():
            raise ValueError('NVRAM staging destination already exists: '+name)
    for name,content in pending.items():
        (target/name).write_bytes(content)
    return list(pending)
