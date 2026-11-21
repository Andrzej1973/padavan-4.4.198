#!/usr/bin/env python3
"""Execute the real candidate probe with injected platform resources, not hardware."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
source = (root / 'mi-mini-port-bundle/new-files/os/linux/mi_mini_platform.c').read_text()
start = source.index('static int mi_mini_probe(')
probe = source[start:source.index('\n}', start) + 2]
prefix = r'''
#include <assert.h>
#include <stddef.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#define __iomem
#define IORESOURCE_MEM 1
struct resource {uint64_t start,end;};
struct platform_device {int dev;};
static struct platform_device *mi_mini_owner;
static struct resource aperture;
static unsigned absent,mapped,attached;
static int irq_value,map_error,attach_error;
static struct resource *platform_get_resource(struct platform_device *p,int type,int n){
 (void)p;assert(type==IORESOURCE_MEM&&!n);return absent?NULL:&aperture;
}
static int platform_get_irq(struct platform_device *p,int n){(void)p;assert(!n);return irq_value;}
static void *devm_ioremap_resource(int *dev,struct resource *r){
 assert(dev&&r==&aperture);mapped++;return map_error?(void *)(intptr_t)-EIO:(void *)1;
}
#define IS_ERR(p) ((intptr_t)(p)<0)
#define PTR_ERR(p) ((int)(intptr_t)(p))
static int mi_mini_radio_attach(void *base,unsigned irq){
 assert(base==(void *)1&&irq==(unsigned)irq_value);attached++;return attach_error;
}
'''
tail = r'''
int main(void){
 struct platform_device dev={0};
 for(unsigned fault=0;fault<9;fault++){
  aperture=(struct resource){0x10180000ULL,0x101bffffULL};
  absent=mapped=attached=0;irq_value=6;map_error=attach_error=0;mi_mini_owner=NULL;
  switch(fault){
   case 1:absent=1;break;
   case 2:aperture.start++;break;
   case 3:aperture.end--;break;
   case 4:aperture.end++;break;
   case 5:irq_value=-EPROBE_DEFER;break;
   case 6:map_error=1;break;
   case 7:attach_error=-EIO;break;
   case 8:mi_mini_owner=&dev;break;
  }
  int result=mi_mini_probe(&dev);
  assert(result==(fault==0?0:fault<=4?-EINVAL:fault==5?-EPROBE_DEFER:fault==8?-EBUSY:-EIO));
  assert(mapped==(fault==0||fault==6||fault==7));
  assert(attached==(fault==0||fault==7));
  assert(mi_mini_owner==((fault==0||fault==8)?&dev:NULL));
 }
 puts("PASS real Mi Mini probe: missing/wrong/short/oversized MMIO refused before mapping; deferred IRQ/map/attach errors preserved; single owner; platform injected, no hardware proof");
}
'''
with tempfile.TemporaryDirectory(prefix='mi-mini-resource-check-') as temp:
    path = Path(temp) / 'check.c'
    exe = Path(temp) / 'check'
    path.write_text('#define EPROBE_DEFER 517\n' + prefix + probe + tail)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    str(path), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
