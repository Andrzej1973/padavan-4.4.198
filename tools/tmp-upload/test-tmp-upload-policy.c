#include <assert.h>
#include "tmp-upload-policy.h"
int main(void)
{
 unsigned long long result;
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,0,16*WR_TMP_MIB,&result)==-2);
 assert(result==24*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,4*WR_TMP_MIB,64*WR_TMP_MIB,&result)==1);
 assert(result==50*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,4*WR_TMP_MIB,40*WR_TMP_MIB,&result)==1);
 assert(result==28*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,0,32*WR_TMP_MIB,&result)==-2);
 assert(result==24*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(60*WR_TMP_MIB,0,0,&result)==2);
 assert(result==60*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,25*WR_TMP_MIB,64*WR_TMP_MIB,&result)==-1);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,0,~0ULL,&result)==1);
 assert(result==50*WR_TMP_MIB);
 assert(wr_tmp_upload_plan(24*WR_TMP_MIB,0,64*WR_TMP_MIB,0)==-1);
 return 0;
}
