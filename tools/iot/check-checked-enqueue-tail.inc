int main(void){
 struct adapter ad;unsigned int payload=0x1234;
 for(int checked=0;checked<2;checked++)for(int mode=0;mode<5;mode++){
  memset(&ad,0,sizeof(ad));allocations=frees=held=queued=wakes=0;owned=NULL;
  fail_at=mode==1?1:mode==2?2:0;
  ad.flags=mode==0?1:0;ad.CmdQ.CmdQState=mode==3?0:1;
  int ret=checked?wr_iot_enqueue_internal_cmd(&ad,7,&payload,sizeof(payload)):
   RTEnqueueInternalCmd(&ad,7,&payload,sizeof(payload));
  assert(!held);
  if(mode==0)assert(ret==1&&!allocations&&!frees&&!queued&&!wakes);
  if(mode==1)assert(ret==2&&allocations==1&&!frees&&!queued&&!wakes);
  if(mode==2)assert(ret==2&&allocations==2&&frees==1&&!queued&&!wakes);
  if(mode==3)assert(ret==(checked?1:0)&&allocations==2&&frees==2&&!queued&&!wakes);
  if(mode==4){
   assert(ret==0&&queued==1&&wakes==1&&!frees&&owned);
   assert(owned->buffer!=&payload&&owned->bufferlength==sizeof(payload));
   assert(!memcmp(owned->buffer,&payload,sizeof(payload)));
   assert(owned->command==7&&!owned->CmdFromNdis);
   os_free_mem(&ad,owned->buffer);os_free_mem(&ad,owned);owned=NULL;
  }
 }
 puts("PASS shared enqueue: checked rejection is failure; legacy preserved; NIC/allocation/rejection/success ownership; primitives injected");
 return 0;
}
