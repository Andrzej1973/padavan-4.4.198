#include <assert.h>
#include <stdio.h>
#include "export-rules.h"
int main(void)
{
 struct wr_usbip_export_rule rules[WR_USBIP_EXPORT_RULES]={0};size_t slot;
 assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_OK);
 rules[0].enabled=1;strcpy(rules[0].bus,"1-1");strcpy(rules[0].vendor,"1234");
 strcpy(rules[0].product,"abcd");strcpy(rules[0].serial_hex,"756e6974");
 assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_OK);
 rules[1]=rules[0];assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_DUPLICATE_PORT&&slot==1);
 strcpy(rules[1].bus,"1-2");assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_DUPLICATE_IDENTITY);
 strcpy(rules[1].serial_hex,"756e697432");assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_OK);
 rules[1].serial_hex[0]=0;assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_INVALID);
 rules[1].enabled=0;assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_OK);
 strcpy(rules[0].serial_hex,"0a");assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_INVALID);
 strcpy(rules[0].serial_hex,"f");assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_INVALID);
 memset(rules[0].serial_hex,'a',sizeof(rules[0].serial_hex));assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_INVALID);
 rules[0].serial_hex[512]=0;assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_OK);
 strcpy(rules[0].bus,"../1-1");assert(wr_usbip_export_validate(rules,16,&slot)==WR_USBIP_EXPORT_INVALID);
 assert(wr_usbip_export_validate(rules,17,&slot)==WR_USBIP_EXPORT_INVALID);
 puts("PASS USBIP export rule validation; no runtime actions");return 0;
}
