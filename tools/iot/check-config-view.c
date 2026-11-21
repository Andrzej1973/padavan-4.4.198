#include "config-view.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="IoT",
 .password="private-key-one",.gateway="192.168.50.1",.mask="255.255.255.0",
 .first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_config_view view,other,before;
 char record[WR_IOT_SAVED_CONFIG_MAX];size_t length;
 assert(wr_iot_saved_config_encode(record,sizeof(record),&config));length=strlen(record);
 assert(wr_iot_config_view_read(&view,record,length));
 assert(!view.enabled&&view.key_present&&!strcmp(view.ssid,"IoT")&&
        !strcmp(view.gateway,"192.168.50.1")&&!strcmp(view.mask,"255.255.255.0")&&
        !strcmp(view.first,"192.168.50.20")&&!strcmp(view.last,"192.168.50.200"));
 strcpy(config.profile.password,"private-key-two");
 assert(wr_iot_saved_config_encode(record,sizeof(record),&config));length=strlen(record);
 assert(wr_iot_config_view_read(&other,record,length));
 assert(!memcmp(&view,&other,sizeof(view)));
 memset(&view,0x5a,sizeof(view));before=view;
 assert(!wr_iot_config_view_read(&view,record,length-1));
 assert(!memcmp(&view,&before,sizeof(view)));
 assert(!wr_iot_config_view_read(&view,record,length+1));
 assert(!memcmp(&view,&before,sizeof(view)));
 record[0]='X';assert(!wr_iot_config_view_read(&view,record,length));
 assert(!memcmp(&view,&before,sizeof(view)));
 assert(!wr_iot_config_view_read(NULL,record,length));
 assert(!wr_iot_config_view_read(&view,NULL,length));
 assert(!wr_iot_config_view_read(&view,record,sizeof(record)));
 assert(!memcmp(&view,&before,sizeof(view)));
 config.profile.enabled=1;
 assert(wr_iot_saved_config_encode(record,sizeof(record),&config));
 assert(wr_iot_config_view_read(&view,record,strlen(record))&&view.enabled);
 puts("PASS nonsecret config view: both desired states, identical bytes for different keys, exact bounded canonical input, unchanged output on refusal; no IPC/HTTP binding");
 return 0;
}
