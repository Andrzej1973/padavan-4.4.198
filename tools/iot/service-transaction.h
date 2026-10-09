/* File transaction core; caller proves daemon/kernel-state success before commit. */
#ifndef WR_IOT_SERVICE_TRANSACTION_H
#define WR_IOT_SERVICE_TRANSACTION_H
#include "service-lock.h"
#include "dnsmasq-files.h"
#include "service-guard.h"
struct wr_iot_service_transaction {struct wr_iot_service_lock lock;struct wr_iot_saved_bundle files;int active;};
static inline void wr_iot_service_transaction_init(struct wr_iot_service_transaction *transaction){
 memset(transaction,0,sizeof(*transaction));transaction->lock.fd=-1;
}
static inline int wr_iot_service_transaction_begin(struct wr_iot_service_transaction *transaction,const char *lock_path){
 if(!transaction||transaction->active||transaction->lock.fd!=-1)return 0;
 if(!wr_iot_service_lock_take(&transaction->lock,lock_path))return 0;
 if(!wr_iot_dnsmasq_files_capture(&transaction->files)||!wr_iot_service_lock_valid(&transaction->lock,lock_path)){
  wr_iot_bundle_release(&transaction->files);wr_iot_service_lock_release(&transaction->lock);return 0;
 }
 transaction->active=1;return 1;
}
/* Called while the same-process service guard is held. The transaction owns
 * only a duplicate descriptor; caller retains its outer guard until finish. */
static inline int wr_iot_service_transaction_begin_guarded(struct wr_iot_service_transaction *transaction,const char *lock_path){
 if(!transaction||transaction->active||transaction->lock.fd!=-1)return 0;
 transaction->lock.fd=wr_iot_service_guard_dup();
 if(transaction->lock.fd<0)return 0;
 if(!wr_iot_service_lock_valid(&transaction->lock,lock_path)||!wr_iot_dnsmasq_files_capture(&transaction->files)||
    !wr_iot_service_lock_valid(&transaction->lock,lock_path)){
  wr_iot_bundle_release(&transaction->files);wr_iot_service_lock_release(&transaction->lock);return 0;
 }
 transaction->active=1;return 1;
}
static inline int wr_iot_service_transaction_seal(struct wr_iot_service_transaction *transaction,const char *lock_path){
 return transaction&&transaction->active&&wr_iot_service_lock_valid(&transaction->lock,lock_path)&&wr_iot_bundle_seal(&transaction->files);
}
static inline int wr_iot_service_transaction_restore(struct wr_iot_service_transaction *transaction,const char *lock_path){
 return transaction&&transaction->active&&wr_iot_service_lock_valid(&transaction->lock,lock_path)&&wr_iot_bundle_restore(&transaction->files);
}
/* Use only after a verified new service or a verified recovered previous service.
 * Restoring files alone does not prove daemon or kernel-state recovery. */
static inline int wr_iot_service_transaction_finish(struct wr_iot_service_transaction *transaction,const char *lock_path){
 if(!transaction||!transaction->active||!transaction->files.sealed||!wr_iot_service_lock_valid(&transaction->lock,lock_path))return 0;
 wr_iot_bundle_release(&transaction->files);wr_iot_service_lock_release(&transaction->lock);transaction->active=0;return 1;
}
#endif
