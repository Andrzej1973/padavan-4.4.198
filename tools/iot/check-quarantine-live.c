#include "quarantine-live.h"
int main(int argc,char **argv){
 if(argc!=2)return 2;
 if(!strcmp(argv[1],"4"))return wr_iot_quarantine_live(0)?0:1;
 if(!strcmp(argv[1],"6"))return wr_iot_quarantine_live(1)?0:1;
 return 2;
}
