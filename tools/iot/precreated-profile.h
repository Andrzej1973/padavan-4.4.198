/* Cold profile preparation only. Runtime ON/OFF must never call the radio
 * generator, remove the third entry, or invoke vendor SSID/AuthMode setters.
 * Caller supplies validated requested credentials even when IoT is OFF.
 * A successful stream is not evidence that the driver loaded it or BSS is DOWN. */
#ifndef WR_IOT_PRECREATED_PROFILE_H
#define WR_IOT_PRECREATED_PROFILE_H
#include "profile-stream.h"
static inline int wr_iot_precreated_profile(FILE *input,FILE *temporary,
 const char *ssid,const char *password,int requested_enabled)
{
 if(requested_enabled!=0&&requested_enabled!=1)return 0;
 /* Build inclusion and BSS reservation are independent of runtime enable.
  * Always append the isolated third profile. Enable belongs to the later
  * admission/bridge/firewall transaction, never to BssidNum. */
 return wr_iot_profile_stream(input,temporary,ssid,password,1);
}
#endif
