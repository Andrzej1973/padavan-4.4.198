#ifndef WR_IOT_RESTART_MAIN_STATE_H
#define WR_IOT_RESTART_MAIN_STATE_H
/* Fixed ra0 administrative read only; no RF/DMA completion or future lease. */
int wr_iot_restart_main_down(void);
/* Fixed SDK profile generator adapter; zero return is success. */
int wr_iot_rc_restart_generate(int);
#endif
