#ifndef WR_IOT_PROFILE_H
#define WR_IOT_PROFILE_H
int wr_iot_profile_apply(const char *,const char *,const char *);
/* Caller holds service guard, owns this profile generation, and has proven
 * radio quiescence. Removes exact owned third entries from CURRENT profile;
 * no global generator/SKU/NVRAM calls. File result is not RF/runtime proof. */
int wr_iot_profile_remove(const char *,const char *,const char *);
#endif
