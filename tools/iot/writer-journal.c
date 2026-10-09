#include "writer-journal.h"
#include <unistd.h>
static struct wr_iot_service_transaction *bound;
static pid_t owner;
static int failed;
static int held(struct wr_iot_service_transaction *t){
 struct stat guard,transaction;int ok,fd=wr_iot_service_guard_dup();
 if(fd<0)return 0;
 ok=t&&t->lock.fd>=0&&!fstat(fd,&guard)&&!fstat(t->lock.fd,&transaction)&&
    guard.st_dev==transaction.st_dev&&guard.st_ino==transaction.st_ino;
 close(fd);return ok;
}
static int valid(void){return bound&&owner==getpid()&&bound->active&&held(bound);}
int wr_iot_writer_journal_bind(struct wr_iot_service_transaction *transaction){
 if(bound||!transaction||!transaction->active||transaction->files.count!=8||!held(transaction))return 0;
 bound=transaction;owner=getpid();failed=0;return 1;
}
int wr_iot_writer_journal_unbind(struct wr_iot_service_transaction *transaction){
 if(bound!=transaction||!valid()||bound->files.pending)return 0;
 bound=NULL;owner=0;return 1;
}
int wr_iot_writer_journal_begin(unsigned int mask){
 unsigned int started=0;size_t i;
 if(!bound)return 1;
 if(!valid()||!mask||(mask&~255U)){failed=1;return 0;}
 for(i=0;i<8;i++)if(mask&(1U<<i)){
  if(!wr_iot_bundle_write_begin(&bound->files,i)){
   /* No writer has run yet. Close only intents acquired by this invocation. */
   size_t j;for(j=0;j<8;j++)if(started&(1U<<j))wr_iot_bundle_write_end(&bound->files,j);
   failed=1;return 0;
  }
  started|=1U<<i;
 }
 return 1;
}
int wr_iot_writer_journal_end(unsigned int mask){
 size_t i;int ok=1;
 if(!bound)return 1;
 if(!valid()||!mask||(mask&~255U)){failed=1;return 0;}
 for(i=0;i<8;i++)if((mask&(1U<<i))&&!wr_iot_bundle_write_end(&bound->files,i))ok=0;
 if(!ok)failed=1;
 return ok;
}
int wr_iot_writer_journal_failed(void){return failed;}
