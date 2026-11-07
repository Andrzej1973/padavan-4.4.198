"""Stable bytes for legacy assets reviewed from the Windows checkout.

Git stores these text assets as LF. Preserve their historically pinned CRLF
representation in generated candidates independently of checkout settings.
This changes newline encoding only; caller source/hash checks remain intact.
"""
from pathlib import Path

CRLF_ASSETS = frozenset({
    'checked-close-host-fixture.c.in', 'interface-reference.h',
    'interface-registry.h', 'mbss-close-checked.inc',
    'mbss-open-admission.inc', 'netdev-registration.inc',
    'radio-transition.h', 'uapsd-retire-queues.inc',
    'virtual-down-checked.inc', 'wcid-fifo-retirement.h',
})


def asset_bytes(path):
    path = Path(path)
    data = path.read_bytes()
    if path.name in CRLF_ASSETS:
        return data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    return data


def copy_asset(source, destination):
    Path(destination).write_bytes(asset_bytes(source))
