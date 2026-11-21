"""Verify exact kernel readback source independently of native RAM capability."""
import hashlib
from pathlib import Path

PREPARED_SOURCE = '78b0613f63221b9bb1d65631d130b8dd34a865a1776985bcd4cd582a3c242d0d'


def verify(trunk):
    root = Path(trunk)/'linux-4.4.x/drivers/nvram'
    source, header = root/'nvram_linux.c', root/'wr-nvram-flash-wire.h'
    for path in (source, header):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or linked native readback input: '+str(path))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != PREPARED_SOURCE:
        raise ValueError('Native readback source is not the exact prepared SDK file')
    expected = (Path(__file__).resolve().parent/'native-flash-wire.h').read_bytes()
    if header.read_bytes() != expected:
        raise ValueError('Native readback wire header differs from client')
    return {'verified':True,'source_sha256':digest,
            'wire_sha256':hashlib.sha256(expected).hexdigest()}


def marker(evidence):
    return ('#ifndef WR_IOT_NATIVE_FLASH_READBACK_PREPARED\n'
            '#define WR_IOT_NATIVE_FLASH_READBACK_PREPARED '+str(int(evidence['verified']))+
            '\n#endif\n')
