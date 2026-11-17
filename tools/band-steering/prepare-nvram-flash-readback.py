"""Install fixed privileged native flash readback after verified commit ordering."""
import argparse
import hashlib
from pathlib import Path


def prepare(text):
    if hashlib.sha256(text.encode()).hexdigest() != '9a0a858b842e7a3751a991db0b91cebec6c2ee82d30d0af364139872e873fcaf':
        raise ValueError('Pinned commit-ordered native NVRAM source changed; no files written')
    local = Path(__file__).resolve().parent.parent / 'iot'
    body = (local / 'native-flash-readback.inc').read_text()
    text = text.replace('#include <linux/fs.h>\n',
                        '#include <linux/fs.h>\n#include <linux/capability.h>\n'
                        '#include "wr-nvram-flash-wire.h"\n', 1)
    text = text.replace('static long\ndev_nvram_ioctl(', body + '\nstatic long\ndev_nvram_ioctl(', 1)
    text = text.replace('\tcase NVRAM_IOCTL_COMMIT:',
                        '\tcase WR_NVRAM_IOCTL_READ_FLASH:\n'
                        '\t\treturn wr_nvram_user_read_flash((anvram_ioctl_t __user *)arg);\n'
                        '\tcase NVRAM_IOCTL_COMMIT:', 1)
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    path = args.source / 'trunk/linux-4.4.x/drivers/nvram/nvram_linux.c'
    updated = prepare(path.read_text())
    header = path.parent / 'wr-nvram-flash-wire.h'
    if header.exists() or header.is_symlink():
        raise ValueError('Readback header already exists; no files written')
    local = Path(__file__).resolve().parent.parent / 'iot'
    header.write_bytes((local / 'native-flash-wire.h').read_bytes())
    path.write_text(updated)
    print('Privileged fixed Config flash readback staged; native GET/SET/COMMIT unchanged')
