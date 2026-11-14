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
#endif
