#include "radio24-validate.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 struct wr_modern_radio24_policy ce={0x3ffeU,1,0x3ffeU},fcc={0xffeU,1,0xffeU},unknown={0,0,0};
 struct wr_modern_radio24_request r={"1","0","2","0",NULL,"13"};
 assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_OK);
 assert(wr_modern_radio24_validate(&r,&fcc)==WR_RADIO24_INVALID);
 assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_POLICY_UNAVAILABLE);
 unknown=ce;unknown.verified=0;assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_POLICY_UNAVAILABLE);
 unknown=ce;unknown.channels|=1U<<14;assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_POLICY_UNAVAILABLE);
 r.channel="14";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.channel="06";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.channel="6x";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.channel="9";r.width="1";r.extension="1";
 unknown=ce;unknown.ht40_primary=0;
 assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_POLICY_UNAVAILABLE);
 unknown=ce;unknown.ht40_primary&=~(1U<<9);
 assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_INVALID);
 unknown=ce;unknown.ht40_primary|=1U<<14;
 assert(wr_modern_radio24_validate(&r,&unknown)==WR_RADIO24_POLICY_UNAVAILABLE);
 assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_OK);
 assert(wr_modern_radio24_validate(&r,&fcc)==WR_RADIO24_INVALID);
 r.extension="0";assert(wr_modern_radio24_validate(&r,&fcc)==WR_RADIO24_OK);
 r.channel="1";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.channel="0";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_OK);
 r.mode="0";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.width=r.extension=NULL;assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_OK);
 r.mode="6";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 r.mode="2";r.width="0";r.hidden="yes";assert(wr_modern_radio24_validate(&r,&ce)==WR_RADIO24_INVALID);
 puts("PASS radio24 validator: supplied policy only, unknown/debug14 rejected, exact enums/channels, secondary mask, legacy omission; no effective-policy provider/runtime claim");return 0;
}
