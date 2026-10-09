#define _GNU_SOURCE
#define WR_IOT_DNSMASQ_FIXTURE_ROOT "."
#include "service-transaction.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 char directory[]="/tmp/iot-dnsmasq-files-XXXXXX",text[32];struct wr_iot_saved_bundle bundle;FILE *fp;size_t i;
 assert(mkdtemp(directory));assert(!chdir(directory));
 assert(!mkdir("etc",0700));assert(!mkdir("etc/dnsmasq",0700));assert(!mkdir("etc/dnsmasq/dhcp",0700));assert(!mkdir("tmp",0700));
 fp=fopen("etc/dnsmasq.conf","w");assert(fp);assert(fputs("old-main\n",fp)>=0);assert(!fclose(fp));
 fp=fopen("etc/ethers","w");assert(fp);assert(fputs("old-ethers\n",fp)>=0);assert(!fclose(fp));
 memset(&bundle,0,sizeof(bundle));assert(wr_iot_dnsmasq_files_capture(&bundle));assert(bundle.count==8);
 for(i=0;i<bundle.count;i++){fp=fopen(bundle.paths[i],"w");assert(fp);assert(fputs("generated\n",fp)>=0);assert(!fclose(fp));}
 assert(wr_iot_bundle_seal(&bundle));assert(wr_iot_bundle_restore(&bundle));
 fp=fopen("etc/dnsmasq.conf","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"old-main\n"));assert(!fclose(fp));
 fp=fopen("etc/ethers","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"old-ethers\n"));assert(!fclose(fp));
 for(i=0;i<bundle.count;i++)if(!bundle.saved[i].existed)assert(access(bundle.paths[i],F_OK)!=0);
 wr_iot_bundle_release(&bundle); {
  struct wr_iot_service_transaction first,second;
  wr_iot_service_transaction_init(&first);wr_iot_service_transaction_init(&second);
  assert(wr_iot_service_transaction_begin(&first,"service.lock"));
  assert(!wr_iot_service_transaction_begin(&second,"service.lock"));assert(second.lock.fd==-1&&!second.files.count);
  assert(!wr_iot_service_transaction_restore(&first,"service.lock"));assert(!wr_iot_service_transaction_finish(&first,"service.lock"));
  fp=fopen("etc/dnsmasq.conf","w");assert(fp);assert(fputs("transaction-main\n",fp)>=0);assert(!fclose(fp));
  assert(wr_iot_service_transaction_seal(&first,"service.lock"));
  assert(wr_iot_service_transaction_restore(&first,"service.lock"));
  fp=fopen("etc/dnsmasq.conf","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"old-main\n"));assert(!fclose(fp));
  assert(!wr_iot_service_transaction_begin(&second,"service.lock"));
  assert(wr_iot_service_transaction_finish(&first,"service.lock"));
  assert(!wr_iot_service_transaction_finish(&first,"service.lock"));
  assert(wr_iot_service_transaction_begin(&second,"service.lock"));assert(wr_iot_service_transaction_seal(&second,"service.lock"));
  assert(wr_iot_service_transaction_finish(&second,"service.lock"));assert(!wr_iot_service_transaction_begin_guarded(&first,"service.lock"));
  assert(wr_iot_service_guard_enter(1)==1);assert(!wr_iot_service_transaction_begin_guarded(&first,"wrong.lock"));assert(first.lock.fd==-1);assert(wr_iot_service_transaction_begin_guarded(&first,"service.lock"));
  assert(!wr_iot_service_transaction_begin(&second,"service.lock"));
  assert(wr_iot_service_guard_enter(1)==1);wr_iot_service_guard_leave(1);
  assert(wr_iot_service_transaction_seal(&first,"service.lock"));assert(wr_iot_service_transaction_restore(&first,"service.lock"));
  assert(wr_iot_service_transaction_finish(&first,"service.lock"));
  assert(!wr_iot_service_transaction_begin(&second,"service.lock"));
  wr_iot_service_guard_leave(1);assert(wr_iot_service_transaction_begin(&second,"service.lock"));
  assert(wr_iot_service_transaction_seal(&second,"service.lock"));assert(wr_iot_service_transaction_finish(&second,"service.lock"));assert(!unlink("service.lock"));
 }

 assert(!unlink("etc/dnsmasq.conf"));assert(!unlink("etc/ethers"));assert(!rmdir("etc/dnsmasq/dhcp"));assert(!rmdir("etc/dnsmasq"));assert(!rmdir("etc"));assert(!rmdir("tmp"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS fixed dnsmasq eight-file registry restores prior contents and prior absence; locked file transaction lifecycle verified; daemon, hostname/domain and ARP rollback integration pending");return 0;
}
