#!/usr/bin/env python3
"""Check exact reviewed asset bytes for LF and CRLF source checkouts."""
import hashlib
from pathlib import Path
import tempfile
from candidate_assets import CRLF_ASSETS, asset_bytes, copy_asset

PINS = {
    'checked-close-host-fixture.c.in': 'eb72013c5c94bd6f2565ab21a0b94035bba47cd404b7939f9503cf651736ea20',
    'interface-reference.h': '2871a1b90c4a381cb9c64106beccaf9bf6cb934fc1f73a8349d9a6fd421a944a',
    'interface-registry.h': 'e90b709fe492b7f886b4278d46480a7b32a3deab5651620f6018801534a32f82',
    'mbss-close-checked.inc': 'e0a8a276816e672286bd142ce545329d9c1fc7d8bd757bf821cd2e074d23157b',
    'mbss-open-admission.inc': '60dddc29753cdbdd6a582a7c05c1ae931e0605d2177ef7cdfcfa8cceafc9c8f7',
    'netdev-registration.inc': 'b3e4c41f1d2e29b130a1fa838c09dd39e240ea2cc2ceee0af25435dbe4af2ad6',
    'radio-transition.h': 'd589d6b19414592cbace12bd33b9cafa038431b10b6b2918f3c8215a70f39634',
    'uapsd-retire-queues.inc': '3309ce6c2cbb398d9fa3a90d0d27aa0dff3902b9d403b5e6962434f7b2257855',
    'virtual-down-checked.inc': 'f7fdf857c7886f2517d67346e7ff8fc57efdc5292653aea213ab3da63fe6edf3',
    'wcid-fifo-retirement.h': 'b5acd241b1079da057517e1b3a690d02fe254658adffb87f04608aae9e856683',
}


def main():
    assert set(PINS) == CRLF_ASSETS
    here = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='wr-iot-asset-check-') as directory:
        root = Path(directory)
        for name, expected in PINS.items():
            lf = (here / name).read_bytes().replace(b'\r\n', b'\n')
            path = root / name
            for data in (lf, lf.replace(b'\n', b'\r\n')):
                path.write_bytes(data)
                actual = asset_bytes(path)
                assert hashlib.sha256(actual).hexdigest() == expected, name
                copy_asset(path, root / 'copy')
                assert (root / 'copy').read_bytes() == actual
            path.write_bytes(lf + b'\n/* altered code */\n')
            assert hashlib.sha256(asset_bytes(path)).hexdigest() != expected, name
        binary = root / 'unlisted.bin'
        binary.write_bytes(b'\x00\n\r\n\xff')
        assert asset_bytes(binary) == binary.read_bytes()
    print('PASS 10 reviewed assets: LF/CRLF copies retain exact pins, changed content differs, unlisted bytes unchanged')


if __name__ == '__main__':
    main()
