#include "interface-reference.h"
#include <assert.h>
#include <stddef.h>
int main(void){
 struct wr_iot_interface_ref r;int dev=0,other=0;
 wr_iot_ref_init(&r,&dev,7);
 assert(!wr_iot_ref_reserve(&r,&dev,0,1));
 assert(!wr_iot_ref_reserve(&r,&other,7,1));
 assert(wr_iot_ref_reserve(&r,&dev,7,1));
 assert(!wr_iot_ref_begin_close(&r,&dev,7,1));
 assert(wr_iot_ref_open_finish(&r,&dev,7,1,0));
 assert(r.open_unmutated==1);
 assert(!wr_iot_ref_consume(&r,&dev,7,1));
 assert(!wr_iot_ref_reserve(&r,&dev,7,1));
 assert(wr_iot_ref_reserve(&r,&dev,7,2));
 assert(r.open_unmutated==0);
 assert(wr_iot_ref_open_finish(&r,&dev,7,2,1));
 assert(r.open_unmutated==0);
 assert(!wr_iot_ref_begin_close(&r,&dev,8,2));
 assert(!wr_iot_ref_consume(&r,&dev,7,2));
 assert(wr_iot_ref_begin_close(&r,&dev,7,2));
 assert(!wr_iot_ref_begin_close(&r,&dev,7,2));
 assert(!wr_iot_ref_reserve(&r,&dev,7,3));
 assert(r.phase==WR_REF_CLOSING); /* failed DOWN must retain this state */
 assert(wr_iot_ref_consume(&r,&dev,7,2));
 assert(!wr_iot_ref_consume(&r,&dev,7,2));
 assert(wr_iot_ref_reserve(&r,&dev,7,3));
 assert(!wr_iot_ref_open_finish(&r,&dev,7,2,1));
 assert(wr_iot_ref_open_finish(&r,&dev,7,3,1));
 assert(!wr_iot_ref_begin_close(&r,&dev,7,2));
 assert(wr_iot_ref_begin_close(&r,&dev,7,3));
 assert(wr_iot_ref_consume(&r,&dev,7,3));
 assert(wr_iot_ref_reserve(&r,&dev,7,~0UL));
 assert(wr_iot_ref_open_finish(&r,&dev,7,~0UL,0));
 assert(!wr_iot_ref_reserve(&r,&dev,7,0));
 wr_iot_ref_init(&r,&dev,8);
 assert(wr_iot_ref_reserve(&r,&dev,8,1));
 assert(!wr_iot_ref_open_uncertain(&r,&other,8,1));
 assert(wr_iot_ref_open_uncertain(&r,&dev,8,1));
 assert(r.phase==WR_REF_UNCERTAIN_OPEN);
 assert(!wr_iot_ref_open_finish(&r,&dev,8,1,0));
 assert(!wr_iot_ref_reserve(&r,&dev,8,2));
 assert(!wr_iot_ref_begin_close(&r,&dev,8,1));
 /* Main first-open failure after AP_MAIN_OPEN must retain ownership/pin. */
 wr_iot_ref_init(&r,&dev,9);
 assert(wr_iot_ref_reserve(&r,&dev,9,1));
 {int retain=-1;
  assert(!wr_iot_ref_complete_main_open(&r,&other,9,1,
   WR_MAIN_OPEN_UNCERTAIN_FAILURE,&retain));
  assert(!wr_iot_ref_complete_main_open(&r,&dev,9,1,
   (enum wr_iot_main_open_outcome)99,&retain));
  assert(r.phase==WR_REF_RESERVED&&retain==-1);
  assert(wr_iot_ref_complete_main_open(&r,&dev,9,1,
   WR_MAIN_OPEN_UNCERTAIN_FAILURE,&retain));
  assert(r.phase==WR_REF_UNCERTAIN_OPEN&&retain==1);
  assert(!wr_iot_ref_reserve(&r,&dev,9,2));
  assert(!wr_iot_ref_complete_main_open(&r,&dev,9,1,
   WR_MAIN_OPEN_UNMUTATED_FAILURE,&retain));
 }
 wr_iot_ref_init(&r,&dev,10);
 assert(wr_iot_ref_reserve(&r,&dev,10,1));
 {int retain=-1;
  assert(wr_iot_ref_complete_main_open(&r,&dev,10,1,
   WR_MAIN_OPEN_UNMUTATED_FAILURE,&retain));
  assert(r.phase==WR_REF_IDLE&&retain==0);
  assert(r.open_unmutated==1);
  assert(wr_iot_ref_reserve(&r,&dev,10,2));
  assert(r.open_unmutated==0);
  assert(wr_iot_ref_complete_main_open(&r,&dev,10,2,
   WR_MAIN_OPEN_ACQUIRED,&retain));
  assert(r.phase==WR_REF_OWNED&&retain==1);
 }
 /* AP-client family OPEN failure after successful virtual-UP is uncertain. */
 wr_iot_ref_init(&r,&dev,11);
 assert(wr_iot_ref_reserve(&r,&dev,11,1));
 {int retain=-1;
  assert(!wr_iot_ref_complete_aux_open(&r,&other,11,1,1,1,1,1,0,&retain));
  assert(!wr_iot_ref_complete_aux_open(&r,&dev,11,1,1,0,1,0,0,&retain));
  assert(r.phase==WR_REF_RESERVED&&retain==-1);
  assert(wr_iot_ref_complete_aux_open(&r,&dev,11,1,1,1,1,1,0,&retain));
  assert(r.phase==WR_REF_UNCERTAIN_OPEN&&retain==1);
  assert(!wr_iot_ref_reserve(&r,&dev,11,2));
 }
 wr_iot_ref_init(&r,&dev,12);
 assert(wr_iot_ref_reserve(&r,&dev,12,1));
 {int retain=-1;
  assert(wr_iot_ref_complete_aux_open(&r,&dev,12,1,1,0,0,0,0,&retain));
  assert(r.phase==WR_REF_IDLE&&retain==0);
  assert(r.open_unmutated==1);
  assert(wr_iot_ref_reserve(&r,&dev,12,2));
  assert(wr_iot_ref_complete_aux_open(&r,&dev,12,2,1,1,1,1,1,&retain));
  assert(r.phase==WR_REF_OWNED&&retain==1);
 }
 wr_iot_ref_init(&r,&dev,13);
 assert(wr_iot_ref_reserve(&r,&dev,13,1));
 {int retain=-1;
  assert(wr_iot_ref_complete_aux_open(&r,&dev,13,1,1,1,0,0,0,&retain));
  assert(r.phase==WR_REF_UNCERTAIN_OPEN&&retain==1);
 }
 /* WDS has no family OPEN; its checked virtual-UP alone owns the reference. */
 wr_iot_ref_init(&r,&dev,14);
 assert(wr_iot_ref_reserve(&r,&dev,14,1));
 {int retain=-1;
  assert(!wr_iot_ref_complete_aux_open(&r,&dev,14,1,0,1,1,1,1,&retain));
  assert(wr_iot_ref_complete_aux_open(&r,&dev,14,1,0,1,1,0,0,&retain));
  assert(r.phase==WR_REF_OWNED&&retain==1);
 }
 wr_iot_ref_init(&r,&dev,15);
 assert(wr_iot_ref_reserve(&r,&dev,15,1));
 {int retain=-1;
  assert(wr_iot_ref_complete_aux_open(&r,&dev,15,1,0,1,0,0,0,&retain));
  assert(r.phase==WR_REF_UNCERTAIN_OPEN&&retain==1);
 }
 return 0;
}
