/* RC-only edit resolution under the caller's existing service/config guard.
 * No password is exported, inferred from a placeholder or read independently
 * from another revision. Not an HTTP wire format and performs no writes.
 */
#ifndef WR_IOT_CONFIG_EDIT_H
#define WR_IOT_CONFIG_EDIT_H
#include "saved-config.h"
enum wr_iot_config_key_action {WR_IOT_CONFIG_KEY_KEEP=1,WR_IOT_CONFIG_KEY_REPLACE=2};
static inline int wr_iot_config_edit_resolve(struct wr_iot_saved_config *out,
 const struct wr_iot_saved_config *fields,enum wr_iot_config_key_action action,
 const char *expected,size_t expected_length,const char *captured,size_t captured_length)
{
 struct wr_iot_saved_config baseline={0},candidate={0},verified={0};
 char encoded[WR_IOT_SAVED_CONFIG_MAX]={0};int ok=0;
 if(!out||!fields||!expected||!captured||expected_length!=captured_length||
    !expected_length||expected_length>=WR_IOT_SAVED_CONFIG_MAX||
    memcmp(expected,captured,expected_length)||
    !wr_iot_saved_config_decode(&baseline,captured,captured_length)||
    !wr_iot_saved_config_encode(encoded,sizeof(encoded),&baseline)||
    strlen(encoded)!=captured_length||memcmp(encoded,captured,captured_length))goto done;
 candidate=*fields;
 if(action==WR_IOT_CONFIG_KEY_KEEP){
  /* KEEP must carry no replacement bytes, including after the first NUL. */
  size_t i;
  for(i=0;i<sizeof(candidate.profile.password);i++)if(candidate.profile.password[i])goto done;
  memcpy(candidate.profile.password,baseline.profile.password,sizeof(candidate.profile.password));
 }else if(action!=WR_IOT_CONFIG_KEY_REPLACE)goto done;
 if(!wr_iot_saved_config_encode(encoded,sizeof(encoded),&candidate)||
    !wr_iot_saved_config_decode(&verified,encoded,strlen(encoded)))goto done;
 *out=verified;ok=1;
 done:
 wr_iot_saved_wipe(&baseline,sizeof(baseline));wr_iot_saved_wipe(&candidate,sizeof(candidate));
 wr_iot_saved_wipe(&verified,sizeof(verified));wr_iot_saved_wipe(encoded,sizeof(encoded));return ok;
}
#endif
