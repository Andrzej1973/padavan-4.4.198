#include <string.h>
#include "initial-restart-entry.h"
#include "initial-restart-select.h"
#include "restart-entry.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
#include "precreated-entropy.h"
enum wr_iot_radio_entry_result wr_iot_initial_restart_entry(int radio_on,int reload)
{
 struct wr_iot_idle_result selected={0};struct wr_iot_rc_physical_intent intent={1,1,0};
 unsigned char bytes[32]={0};volatile unsigned char *wipe;
 enum wr_iot_initial_selection selection;
 enum wr_iot_radio_entry_result result=WR_RADIO_ENTRY_REFUSED;
 unsigned i,nonzero=0;
 if(radio_on!=1)return WR_RADIO_ENTRY_NATIVE;
 if((reload!=0&&reload!=1)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return result;
 /* Existing owned backend takes its established restart path. The following
  * selector independently requires exact never-opened backend admission. */
 if(wr_iot_rc_restart_owned())return WR_RADIO_ENTRY_NATIVE;
 if(wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto done;
 for(i=0;i<16;i++)nonzero|=bytes[i];
 if(!nonzero)goto done;
 selection=wr_iot_initial_restart_select(bytes,&selected);
 if(selection==WR_INITIAL_SELECT_NATIVE){result=WR_RADIO_ENTRY_NATIVE;goto done;}
 if(selection!=WR_INITIAL_SELECT_ELIGIBLE)goto done;
 intent.reload=(unsigned)reload;
 /* Physical owner repeats proof under its own guard/fence. Once selection
  * succeeded, a refused claim can never authorize legacy fallthrough. */
 if(wr_iot_rc_physical_begin_initial_selected(&intent,bytes,&selected))result=WR_RADIO_ENTRY_OWNED;
 done:wipe=bytes;for(i=0;i<sizeof(bytes);i++)wipe[i]=0;
 memset(&selected,0,sizeof(selected));return result;
}
