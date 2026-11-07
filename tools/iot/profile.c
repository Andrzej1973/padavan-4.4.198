#include "profile.h"
#include "profile-file.h"
int wr_iot_profile_apply(const char *path,const char *ssid,const char *password) {
 return wr_iot_profile_replace(path,ssid,password,1);
}
int wr_iot_profile_remove(const char *path,const char *ssid,const char *password) {
 return wr_iot_profile_remove_file(path,ssid,password);
}
