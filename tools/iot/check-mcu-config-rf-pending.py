#!/usr/bin/env python3
"""Execute RF write-record identity, retention and generation boundaries."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
source=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "mcu-config-rf-pending.h"
int main(void){struct wr_iot_config_rf_pending p={0},before;unsigned field;
 assert(wr_iot_config_rf_record(&p,1,2,3,4,5,6,7,8));before=p;
 assert(wr_iot_config_rf_record_matches(&p,1,1,2,3,4,5,6,7,8));
 assert(!wr_iot_config_rf_record(&p,1,2,3,4,5,6,9,10)&&!memcmp(&p,&before,sizeof(p)));
 for(field=0;field<9;field++){
  struct wr_iot_config_rf_pending q=p;
  switch(field){case 0:q.generation++;break;case 1:q.peer_serial++;break;case 2:q.radio_serial++;break;
   case 3:q.radio_epoch++;break;case 4:q.close_serial++;break;case 5:q.close_epoch++;break;
   case 6:q.stream++;break;case 7:q.address++;break;case 8:q.value++;break;}
  assert(!wr_iot_config_rf_record_matches(&q,1,1,2,3,4,5,6,7,8));
 }
 p.poisoned=1;assert(!wr_iot_config_rf_record_matches(&p,1,1,2,3,4,5,6,7,8));
 p=(struct wr_iot_config_rf_pending){.generation=~0u};
 assert(!wr_iot_config_rf_record(&p,1,2,3,4,5,6,7,8)&&p.poisoned&&!p.active&&p.generation==~0u);
 p=(struct wr_iot_config_rf_pending){0};assert(!wr_iot_config_rf_record(&p,0,2,3,4,5,6,7,8)&&!p.active&&!p.generation);
 assert(wr_iot_config_rf_record(&p,1,2,3,4,5,0,0,0));
 assert(wr_iot_config_rf_record_matches(&p,1,1,2,3,4,5,0,0,0));
 /* Model a future proven resolution; no driver clearing API is installed. */
 p.active=0;assert(wr_iot_config_rf_record(&p,1,2,3,4,5,0,0,0)&&p.generation==2);
 assert(!wr_iot_config_rf_record_matches(&p,1,1,2,3,4,5,0,0,0));
 assert(!wr_iot_config_rf_record_matches(NULL,1,1,2,3,4,5,6,7,8));
 puts("PASS RF pending record: all ticket/tuple/generation fields, duplicate retention, poison/overflow refusal; no hardware proof or counter clearing");}
'''
with tempfile.TemporaryDirectory(prefix='wr-rf-pending-') as td:
 c=Path(td)/'check.c';c.write_text(source)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
