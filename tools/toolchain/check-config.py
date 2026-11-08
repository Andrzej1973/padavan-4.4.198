#!/usr/bin/env python3
"""Reject normalized crosstool-NG profiles that drift from the reviewed ABI."""
from pathlib import Path
import sys

def check(text):
 values={}
 for line in text.splitlines():
  if line.startswith('CT_') and '=' in line:
   key,value=line.split('=',1)
   if key in values:raise ValueError('Duplicate setting '+key)
   values[key]=value
 expected={'CT_ARCH_MIPS':'y','CT_ARCH_LE':'y','CT_ARCH_FLOAT_HW':'y','CT_ARCH_TUNE':'"mips32r2"','CT_OMIT_TARGET_VENDOR':'y','CT_GCC_VERSION':'"10.5.0"','CT_LIBC_UCLIBC_NG':'y','CT_UCLIBC_NG_SRC_CUSTOM':'y','CT_LINUX_SRC_CUSTOM':'y','CT_VERIFY_DOWNLOAD_DIGEST':'y','CT_VERIFY_DOWNLOAD_DIGEST_SHA256':'y','CT_CC_LANG_CXX':'y','CT_INSTALL_LICENSES':'y'}
 for key,value in expected.items():
  if values.get(key)!=value:raise ValueError('Unexpected or missing '+key)
 for key,suffix in [('CT_LINUX_CUSTOM_LOCATION','/source/trunk/linux-4.4.x"'),('CT_LIBC_UCLIBC_CONFIG_FILE','/source/trunk/configs/boards/uclibc-mipsel.config"'),('CT_UCLIBC_NG_CUSTOM_LOCATION','/uClibc-ng-1.0.48.tar.xz"')]:
  if not values.get(key,'').endswith(suffix):raise ValueError('Wrong source path '+key)
 return values
if __name__=='__main__':
 check(Path(sys.argv[1]).read_text());print('PASS normalized GCC10.5 MIPSel/uClibc profile, source paths, licenses and SHA256 enforcement')
