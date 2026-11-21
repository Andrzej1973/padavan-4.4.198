#ifndef WR_IOT_RESTART_PROFILE_RECEIPT_H
#define WR_IOT_RESTART_PROFILE_RECEIPT_H
#include "radio-profile-state.h"
/* File identity only; contains neither file bytes nor credentials. Capture
 * from an owned completed restoration before profile_finish clears its state.
 * Caller keeps service guard and serializes writers across capture/use. */
struct wr_iot_restart_profile_receipt {
 int valid;pid_t owner;
 char path[128];struct wr_iot_generated_file file;
};
static inline int wr_iot_restart_profile_receipt_take(
 struct wr_iot_restart_profile_receipt *out,struct wr_iot_radio_profile_state *profile)
{
 struct wr_iot_restart_profile_receipt candidate={0};size_t length;
 if(!out||out->valid||out->owner||!wr_iot_radio_profile_owned(profile)||
    !profile->recovering||!profile->recovered||profile->files.count!=1||
    profile->files.pending||!memchr(profile->files.paths[0],0,sizeof(profile->files.paths[0]))||
    !wr_iot_generated_matches(&profile->restored_file,profile->files.paths[0]))return 0;
 length=strlen(profile->files.paths[0]);if(!length||length>=sizeof(candidate.path))return 0;
 memcpy(candidate.path,profile->files.paths[0],length+1);
 candidate.file=profile->restored_file;candidate.owner=getpid();candidate.valid=1;
 *out=candidate;return 1;
}
/* Read-only capture cancellation: record the original identity only if it is
 * still current. Refusal never prevents disposal of private capture memory. */
static inline int wr_iot_restart_profile_receipt_cancel_take(
 struct wr_iot_restart_profile_receipt *out,struct wr_iot_radio_profile_state *profile)
{
 struct wr_iot_restart_profile_receipt candidate={0};size_t length;
 if(!out||out->valid||out->owner||!wr_iot_radio_profile_owned(profile)||
    profile->generated||profile->recovering||profile->removing||
    profile->files.count!=1||profile->files.journalled||profile->files.dirty||profile->files.pending||
    !memchr(profile->files.paths[0],0,sizeof(profile->files.paths[0]))||
    !wr_iot_generated_matches(&profile->files.generated[0],profile->files.paths[0]))return 0;
 length=strlen(profile->files.paths[0]);if(!length||length>=sizeof(candidate.path))return 0;
 memcpy(candidate.path,profile->files.paths[0],length+1);candidate.file=profile->files.generated[0];
 candidate.owner=getpid();candidate.valid=1;*out=candidate;return 1;
}
static inline int wr_iot_restart_profile_receipt_current(const struct wr_iot_restart_profile_receipt *receipt)
{
 struct stat current;
 return receipt&&receipt->valid==1&&receipt->owner==getpid()&&
  memchr(receipt->path,0,sizeof(receipt->path))&&receipt->path[0]&&
  wr_iot_radio_profile_guard()&&wr_iot_generated_matches(&receipt->file,receipt->path)&&
  (!receipt->file.existed||(!lstat(receipt->path,&current)&&
   current.st_mtim.tv_nsec==receipt->file.metadata.st_mtim.tv_nsec&&
   current.st_ctim.tv_nsec==receipt->file.metadata.st_ctim.tv_nsec));
}
/* Refresh identity only after restoring this receipt's original captured bytes.
 * Caller retains pre-UP rollback ownership/guard; this proves no loaded keys. */
static inline int wr_iot_restart_profile_receipt_restored(
 struct wr_iot_restart_profile_receipt *receipt,const struct wr_iot_radio_profile_state *profile)
{
 const struct wr_iot_saved_file *saved;const struct stat *old,*captured;
 struct wr_iot_saved_file restored={0};struct wr_iot_restart_profile_receipt candidate;
 int ok=0;
 if(!receipt||!profile||receipt->valid!=1||receipt->owner!=getpid()||
    !profile->active||profile->owner!=getpid()||!profile->recovering||!profile->recovered||
    profile->removing||profile->files.count!=1||profile->files.pending||
    !memchr(receipt->path,0,sizeof(receipt->path))||!receipt->path[0]||
    !memchr(profile->files.paths[0],0,sizeof(profile->files.paths[0]))||
    strcmp(receipt->path,profile->files.paths[0])||!wr_iot_radio_profile_guard()||
    !wr_iot_generated_matches(&profile->restored_file,receipt->path))return 0;
 /* Same guarded retry after a failed final unmask needs no second update. */
 if(wr_iot_restart_profile_receipt_current(receipt))return 1;
 saved=&profile->files.saved[0];old=&receipt->file.metadata;captured=&saved->metadata;
 if(!receipt->file.existed||!saved->existed||!saved->data||
    saved->size>WR_IOT_SAVED_LIMIT||saved->size!=(size_t)old->st_size||
    old->st_dev!=captured->st_dev||old->st_ino!=captured->st_ino||
    old->st_size!=captured->st_size||old->st_mode!=captured->st_mode||
    old->st_uid!=captured->st_uid||old->st_gid!=captured->st_gid||
    old->st_mtim.tv_sec!=captured->st_mtim.tv_sec||old->st_mtim.tv_nsec!=captured->st_mtim.tv_nsec||
    old->st_ctim.tv_sec!=captured->st_ctim.tv_sec||old->st_ctim.tv_nsec!=captured->st_ctim.tv_nsec)return 0;
 if(!wr_iot_saved_capture(&restored,receipt->path)||!restored.existed||
    restored.size!=saved->size||memcmp(restored.data,saved->data,saved->size))goto done;
 candidate=*receipt;candidate.file=profile->restored_file;
 if(!wr_iot_restart_profile_receipt_current(&candidate))goto done;
 *receipt=candidate;ok=1;
 done:
 if(restored.data){volatile unsigned char *bytes=restored.data;size_t length=restored.size;while(length--)*bytes++=0;}
 wr_iot_saved_release(&restored);return ok;
}
#endif
