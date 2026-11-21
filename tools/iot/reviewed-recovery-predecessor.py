"""Exact reviewed join normalization for independently pinned candidate stages."""
import hashlib
from pathlib import Path

def reviewed_predecessor(data,name):
 if name!='os/linux/rt_main_dev.c':return data
 marker=b'INT wr_iot_main_recovery_join_complete('
 if data.count(marker)!=1:return data
 start=data.index(marker);end=data.index(b'\n}',start)+2
 body=data[start:end]
 approved=('0d4b8abfeaf98c9f12564dc2d441c14b862796bc28f97a526e19902ef51022bb', '6dc2169771331e356b1c501c194f565b40bd5285b09a615d670ce642b4221da4')
 if hashlib.sha256(body).hexdigest() not in approved:return data
 baseline=Path(__file__).with_name('main-recovery-join-baseline.inc').read_bytes()
 if hashlib.sha256(baseline).hexdigest()!='5e24b03bc41930ea848f57991f95bd3918d472a6dc66c3906f382d71486c8c94':
  raise ValueError('changed reviewed main recovery join baseline')
 return data[:start]+baseline+data[end:]
