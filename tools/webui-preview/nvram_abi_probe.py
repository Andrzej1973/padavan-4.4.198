"""Native/target compile-time ABI evidence without executing target code."""
import struct
import subprocess

def client_source():
    return '''#include "nvram-batch-client.h"
#include "guest-batch.h"
WR_NVRAM_ABI_RECORD(wr_nvram_client_abi);
int wr_nvram_client_probe(int fd,const struct wr_nvram_wire_request *request,unsigned int *changed)
{return wr_nvram_submit_batch(fd,request,changed);}
int wr_nvram_guest_probe(struct wr_nvram_wire_request *out,wr_modern_guest_read cgi,
                        wr_modern_guest_read nv,void *context,enum wr_modern_guest_error *reason)
{(void)wr_modern_guest_persist_value;return wr_modern_guest_build_batch(out,cgi,nv,context,reason);}
'''

def read_record(objcopy, binary, destination):
    subprocess.run([str(objcopy), '-O', 'binary', '-j', '.wr_nvram_abi', str(binary), str(destination)], check=True)
    raw = destination.read_bytes()
    if len(raw) != 16:
        raise ValueError('NVRAM ABI section must contain exactly four u32 fields')
    # Both this board and the native host checks use little-endian ELF.
    request_size, item_size, command, version = struct.unpack('<4I', raw)
    if (request_size, item_size, version) != (5264, 328, 1):
        raise ValueError('NVRAM compiled ABI layout/version mismatch')
    return {'request_bytes': request_size, 'item_bytes': item_size,
            'ioctl_command': command, 'version': version}
