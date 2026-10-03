#!/usr/bin/env python3
"""Install pinned HTTP/3 recipes into a separate target tree."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('target', type=Path)
p.add_argument('source', type=Path)
a = p.parse_args()
libs = a.target / 'trunk/libs'
src = a.source / 'trunk/libs'
root_make = libs / 'Makefile'
text = root_make.read_text()
anchor = 'dir_$(LIBS_INCLUDE_LIBCURL)'
if text.count(anchor) != 1 or 'libngtcp2_only' in text:
    raise SystemExit('Unexpected library build rules')
curl = (src / 'libcurl/Makefile').read_text()
if 'SRC_NAME = curl-8.20.0' not in curl:
    raise SystemExit('Unexpected pinned curl recipe')
# Use the CA bundle already installed by the target, preserving trust behavior.
curl = curl.replace('/etc/ssl/cert.pem', '/etc/ssl/certs/ca-certificates.crt')
curl = curl.replace('\t./configure \\', '\tPKG_CONFIG_PATH= PKG_CONFIG_LIBDIR="$(STAGEDIR)/lib/pkgconfig:$(STAGEDIR)/share/pkgconfig" PKG_CONFIG_SYSROOT_DIR="$(STAGEDIR)" CURL_TRACE_PKG_CONFIG=1 ./configure \\')
curl = '''ifneq (,$(filter y,$(CONFIG_FIRMWARE_INCLUDE_OPENSSL_35) $(CONFIG_FIRMWARE_INCLUDE_QUIC)))
SSL_VER = 3.5
else
SSL_VER = 1.1
endif
''' + curl
names = ('libngtcp2', 'libnghttp3', 'libnghttp2')
for name in names:
    if not (src / name / 'Makefile').is_file() or (libs / name).exists():
        raise SystemExit('Missing source or existing destination: ' + name)
if (a.target / 'trunk/include/cross-mipsel-linux.cmake').exists():
    raise SystemExit('Existing CMake toolchain requires review')
for name in names:
    shutil.copytree(src / name, libs / name)
# Preserve source curl archives and patches, replacing the vendor directory
# only by copying files into it; no deletion of an existing source tree.
shutil.copytree(src / 'libcurl', libs / 'libcurl', dirs_exist_ok=True)
(libs / 'libcurl/Makefile').write_text(curl)
toolchain = a.target / 'trunk/include/cross-mipsel-linux.cmake'
toolchain.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(Path(__file__).with_name('cross-mipsel-linux.cmake'), toolchain)
pos = text.index(anchor)
start = text.rfind('\n', 0, pos) + 1
text = text[:start] + '''ifeq ($(CONFIG_FIRMWARE_INCLUDE_QUIC),y)
dir_$(LIBS_INCLUDE_LIBCURL) += libngtcp2 libnghttp3
endif
dir_$(LIBS_INCLUDE_LIBCURL) += libnghttp2
''' + text[start:]
text += '''
# Explicit prerequisites also protect parallel library builds.
libcurl_only: libssl_only libnghttp2_only
ifeq ($(CONFIG_FIRMWARE_INCLUDE_QUIC),y)
libngtcp2_only: libssl_only
libcurl_only: libngtcp2_only libnghttp3_only
endif
'''
root_make.write_text(text)
print('HTTP/3 recipes prepared; compilation and feature verification required')
