from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#define IFNAME_2G_MAIN "ra0"
#define LED_SW2G 7
#define LED_ON 1
static int guard=1,held,ap,mode,radio=1,up=1,leds;
static int wr_iot_service_guard_enter(int enabled){assert(enabled==1);if(!guard)return 0;held++;return 1;}
static void wr_iot_service_guard_leave(int token){assert(token==1&&held==1);held--;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int is_interface_up(const char*n){assert(!strcmp(n,"ra0"));return up;}
static void led_control(int led,int on){assert(led==7&&on==1&&held==1);leds++;}
#define LED_CONTROL led_control
#include "restart-led-sdk.inc"
int main(void){
 guard=0;assert(!wr_iot_rc_restart_led_on()&&!held&&!leds);guard=1;
 ap=1;assert(!wr_iot_rc_restart_led_on()&&!held&&!leds);ap=0;
 mode=2;assert(!wr_iot_rc_restart_led_on()&&!held&&!leds);mode=0;
 radio=0;assert(!wr_iot_rc_restart_led_on()&&!held&&!leds);radio=1;
 up=0;assert(!wr_iot_rc_restart_led_on()&&!held&&!leds);up=1;
 assert(wr_iot_rc_restart_led_on()&&!held&&leds==1);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-led-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS fixed SDK LED adapter: guard/router/mode/radio/Main-UP refusal, balanced guard, exact stock calls; LED/helper actors injected, not physical indication proof')
