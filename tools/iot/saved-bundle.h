/* Caller owns one serialized service generation; no live restart integration yet. */
#ifndef WR_IOT_SAVED_BUNDLE_H
#define WR_IOT_SAVED_BUNDLE_H
#include "restore-file.h"
#define WR_IOT_BUNDLE_MAX 8
struct wr_iot_saved_bundle {
 size_t count;int sealed;unsigned int restored;
 char paths[WR_IOT_BUNDLE_MAX][128];
 struct wr_iot_saved_file saved[WR_IOT_BUNDLE_MAX];
 struct wr_iot_generated_file generated[WR_IOT_BUNDLE_MAX];
};
static inline void wr_iot_bundle_release(struct wr_iot_saved_bundle *bundle){
 size_t i;if(!bundle)return;
 for(i=0;i<WR_IOT_BUNDLE_MAX;i++)wr_iot_saved_release(&bundle->saved[i]);
 memset(bundle,0,sizeof(*bundle));
}
static inline int wr_iot_bundle_capture(struct wr_iot_saved_bundle *out,const char *const *paths,size_t count){
 struct wr_iot_saved_bundle candidate;size_t i,j,n;
 if(!out||out->count||!paths||!count||count>WR_IOT_BUNDLE_MAX)return 0;
 memset(&candidate,0,sizeof(candidate));
 for(i=0;i<count;i++){
  if(!paths[i]||!(n=strlen(paths[i]))||n>=sizeof(candidate.paths[i]))goto fail;
  for(j=0;j<i;j++)if(!strcmp(paths[i],candidate.paths[j]))goto fail;
  memcpy(candidate.paths[i],paths[i],n+1);
  if(!wr_iot_saved_capture(&candidate.saved[i],paths[i]))goto fail;
 }
 candidate.count=count;*out=candidate;return 1;
fail:wr_iot_bundle_release(&candidate);return 0;
}
/* Only seal after this transaction's own writes, with all other writers blocked. */
static inline int wr_iot_bundle_seal(struct wr_iot_saved_bundle *bundle){
 struct wr_iot_generated_file generated[WR_IOT_BUNDLE_MAX];size_t i;
 if(!bundle||!bundle->count||bundle->count>WR_IOT_BUNDLE_MAX||bundle->sealed)return 0;
 memset(generated,0,sizeof(generated));
 for(i=0;i<bundle->count;i++)if(!wr_iot_generated_capture(&generated[i],bundle->paths[i]))return 0;
 memcpy(bundle->generated,generated,sizeof(generated));bundle->sealed=1;return 1;
}
/* Keep snapshots after any error. Completed files are skipped on retry. */
static inline int wr_iot_bundle_restore(struct wr_iot_saved_bundle *bundle){
 size_t i;int complete=1;
 if(!bundle||!bundle->sealed||!bundle->count||bundle->count>WR_IOT_BUNDLE_MAX)return 0;
 for(i=0;i<bundle->count;i++)if(!(bundle->restored&(1U<<i))&&
    !wr_iot_generated_matches(&bundle->generated[i],bundle->paths[i]))return 0;
 for(i=0;i<bundle->count;i++)if(!(bundle->restored&(1U<<i))){
  if(wr_iot_saved_restore(&bundle->saved[i],&bundle->generated[i],bundle->paths[i]))bundle->restored|=1U<<i;
  else complete=0;
 }
 return complete;
}
#endif
