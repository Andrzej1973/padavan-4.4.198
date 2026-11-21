#include <assert.h>
typedef unsigned int UINT32;typedef int BOOLEAN;
typedef struct {int gone;} RTMP_ADAPTER;
#define TRUE 1
#define FALSE 0
#define TX_DMA_EN 1u
#define TX_DMA_BUSY 2u
#define RX_DMA_EN 4u
#define RX_DMA_BUSY 8u
#define MT_WPDMA_GLO_CFG 0
#define fRTMP_ADAPTER_NIC_NOT_EXIST 0
#define RTMP_TEST_FLAG(a,f) ((void)(f),(a)->gone)
static unsigned reads,mode;
static UINT32 read_value(RTMP_ADAPTER *a){reads++;if(mode==5){a->gone=1;return 0;}if(mode==4)return ~0u;if(mode==3)return reads%2?0:TX_DMA_BUSY;if(mode==2)return RX_DMA_EN;if(mode==1)return RX_DMA_BUSY;return 0;}
#define RTMP_IO_READ32(a,r,p) do{(void)(r);*(p)=read_value(a);}while(0)
#define RtmpusecDelay(us) ((void)(us))
#include "mcu-dma-disabled-idle.inc"
int main(void){RTMP_ADAPTER a={0};
for(mode=0;mode<=5;mode++){a.gone=0;reads=0;assert(wr_iot_mcu_dma_disabled_idle(&a)==(mode==0));assert(reads<=200);if(mode==0)assert(reads==2);}
a.gone=1;reads=0;assert(!wr_iot_mcu_dma_disabled_idle(&a)&&!reads);return 0;}
