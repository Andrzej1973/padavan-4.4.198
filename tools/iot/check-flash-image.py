#!/usr/bin/env python3
"""Compare pure image validator with actual pinned vendor CRC implementation."""
import ctypes
import hashlib
import pathlib
import random
import re
import struct
import subprocess
import sys
import tempfile

vendor = pathlib.Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(vendor).hexdigest() == 'eb8ec04cf2c454dc9bc469f7f89a2540724bcb2cda2d76e310e1e29ab7c20487'
text = vendor.decode()
table = re.search(r'static uint8_t crc8_table\[256\] = \{.*?\};', text, re.S).group()
function = re.search(r'uint8_t\s+_hndcrc8\(.*?\n\}', text, re.S).group()
root = pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-iot-flash-') as tmp:
    source = pathlib.Path(tmp) / 'check.c'
    library = pathlib.Path(tmp) / 'check.so'
    source.write_text('#include <stdint.h>\ntypedef unsigned int uint;\n' + table + '\n' + function +
                      '\n#include "saved-config-flash.h"\nint validate(void *p,size_t n,size_t c)'
                      '{return wr_iot_flash_image_valid(p,n,c);}\n'
                      'int lookup(void *p,size_t n,size_t c,const char *k,char *o,size_t z)'
                      '{return wr_iot_flash_image_get(p,n,c,k,o,z); }\n'
                      'int compare(void *p,size_t n,size_t c,const char *r,size_t z)'
                      '{return wr_iot_saved_flash_compare(p,n,c,r,z); }\n')
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    '-I', str(root), str(source), '-o', str(library)], check=True)
    lib = ctypes.CDLL(str(library))
    lib._hndcrc8.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_ubyte]
    lib._hndcrc8.restype = ctypes.c_ubyte
    lib.validate.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
    lib.lookup.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t,
                           ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t]
    def lookup(data, key, capacity=32):
        buf = ctypes.create_string_buffer(bytes(data))
        out = ctypes.create_string_buffer(b'UNCHANGED', 32)
        before = out.raw
        result = lib.lookup(buf, len(data), 61440, key, out, capacity)
        if result != 1:
            assert out.raw == before
        return result, out.value
    lib.compare.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t,
                            ctypes.c_char_p, ctypes.c_size_t]
    def compare(data, record):
        buf = ctypes.create_string_buffer(bytes(data))
        return lib.compare(buf, len(data), 61440, record, len(record))
    def crc(data):
        return lib._hndcrc8(ctypes.create_string_buffer(data), len(data), 255)
    def image(payload):
        n = (20 + len(payload) + 3) & ~3
        data = bytearray(struct.pack('<IIIII', 0x48534c46, n, 256, 0, 0) + payload)
        data += bytes(n - len(data))
        data[8] = crc(bytes(data[9:]))
        return data
    def valid(data, size=None, capacity=61440):
        # Deliberately unaligned input.
        buf = ctypes.create_string_buffer(b'x' + bytes(data))
        return lib.validate(ctypes.byref(buf, 1), len(data) if size is None else size, capacity)
    rng = random.Random(7603)
    for index in range(1000):
        payload = b'a=' + rng.randbytes(rng.randrange(128)).hex().encode() + b'\0b==\0\0'
        data = image(payload)
        assert valid(data)
        assert not valid(data, 19)
        assert not valid(data, len(data)-1)
        assert not valid(data, capacity=20)
        changed = bytearray(data)
        changed[rng.randrange(9, len(changed))] ^= 1
        assert not valid(changed)
    for payload in [b'a=1\0a=2\0\0', b'=empty\0\0', b'noequals\0\0', b'a=1\0\0junk\0']:
        assert not valid(image(payload))
    for payload in [b'\0\0', b'a=\0\0', b'a==value\0\0']:
        assert valid(image(payload))
    data = image(b'a=1\0\0')
    for offset in (0, 4, 9):
        changed = bytearray(data)
        changed[offset] ^= 1
        assert not valid(changed)
    assert not lib.validate(None, 100, 61440)
    data = image(b'wr_iot_config_v1=record==value\0empty=\0\0')
    assert lookup(data, b'wr_iot_config_v1') == (1, b'record==value')
    assert lookup(data, b'empty') == (1, b'')
    assert lookup(data, b'missing')[0] == 0
    assert lookup(data, b'wr_iot_config')[0] == 0
    assert lookup(data, b'wr_iot_config_v1', 2)[0] == -1
    for key in (b'', b'bad=key', None):
        assert lookup(data, key)[0] == -1
    assert lookup(image(b'a=1\0a=2\0\0'), b'a')[0] == -1
    assert lookup(bytes(24), b'a')[0] == -1
    fields = [b'0', b'IoT test', b'password123', b'192.168.50.1',
              b'255.255.255.0', b'192.168.50.20', b'192.168.50.200']
    off = b'WR-IOT-CONFIG-1:' + b':'.join(v.hex().encode() for v in fields)
    fields[0] = b'1'
    on = b'WR-IOT-CONFIG-1:' + b':'.join(v.hex().encode() for v in fields)
    def with_record(record):
        return image(b'wr_iot_config_v1=' + record + b'\0other=keep\0\0')
    assert compare(with_record(off), off) == 2
    assert compare(with_record(on), on) == 2
    assert compare(with_record(off), on) == 1
    assert compare(image(b'other=keep\0\0'), off) == 0
    assert compare(with_record(b'malformed'), off) == -1
    assert compare(with_record(off), b'malformed') == -1
    assert compare(with_record(b''), off) == -1
    assert compare(image(b'wr_iot_config_v1=' + off + b'\0wr_iot_config_v1=' + off + b'\0\0'), off) == -1
    assert compare(bytes(24), off) == -1
    # Exercise bounded reads under address/undefined sanitizers in a process;
    # loading an ASan DSO into the Python interpreter is not sufficient.
    sanitize = pathlib.Path(tmp) / 'sanitize.c'
    executable = pathlib.Path(tmp) / 'sanitize'
    sanitize.write_text(source.read_text() + r"""
#include <stdlib.h>
#include <assert.h>
int main(void) {
 size_t n,i; unsigned int state=7603;
 for(n=0;n<256;n++) {
  unsigned char *p=malloc(n?n:1); char out[8]="keep";
  assert(p);
  for(i=0;i<n;i++){state=state*1664525u+1013904223u;p[i]=(unsigned char)(state>>24);}
  assert(!validate(p,n,61440));
  assert(lookup(p,n,61440,"wr_iot_config_v1",out,sizeof(out))==-1);
  assert(!strcmp(out,"keep"));
  free(p);
 }
 return 0;
}
""")
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    '-I', str(root), str(sanitize), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)

print('PASS vendor CRC cross-check, 1000 valid/corrupt images, bounds, alignment, tuple ambiguity, exact lookup/output preservation, typed ON/OFF revision comparison')
