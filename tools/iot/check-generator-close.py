#!/usr/bin/env python3
"""Actual prepared WR2g generator stream-error handling, other bands retained."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
module=ast.parse((here/'prepare-rc.py').read_text())
fragment=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='iot_generator_checked_close' for t in n.targets))
code=r'''
#include <stdio.h>
#include <assert.h>
static int stream_error,flush_error,close_error,flushes,closes;
static int fake_error(FILE*f){assert(f);return stream_error;}
static int fake_flush(FILE*f){assert(f);flushes++;return flush_error;}
static int fake_close(FILE*f){assert(f);closes++;return close_error;}
#define ferror fake_error
#define fflush fake_flush
#define fclose fake_close
static int finish(FILE*fp,int is_soc_ap,int is_aband){(void)is_soc_ap;(void)is_aband;
'''+fragment+r'''
}
int main(void){
 FILE *fp=(FILE*)1;(void)fake_error;(void)fake_flush;
 for(int fault=0;fault<4;fault++){
  stream_error=fault==1;flush_error=fault==2;close_error=fault==3;flushes=closes=0;
#if defined(BOARD_WR1200JS)
  assert(finish(fp,1,0)==(fault?-1:0)&&flushes==1&&closes==1);
#else
  assert(finish(fp,1,0)==0&&!flushes&&closes==1);
#endif
  flushes=closes=0;assert(finish(fp,0,0)==0&&!flushes&&closes==1);
  flushes=closes=0;assert(finish(fp,1,1)==0&&!flushes&&closes==1);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-generator-close-') as d:
 unit=Path(d)/'check.c';unit.write_text(code)
 for board in ('BOARD_WR1200JS','BOARD_OTHER'):
  binary=Path(d)/board
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-D'+board,str(unit),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual prepared generator close: WR SoC2g ferror/fflush/fclose failures return-1, close once; success0; other boards/bands retain baseline behavior; stdio injected')
