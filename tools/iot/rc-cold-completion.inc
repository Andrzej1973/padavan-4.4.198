/* Thin private RC exports, after the four cold completion fragments. */
int wr_iot_rc_cold_parent_release(struct wr_iot_cold_parent_release *s,struct wr_iot_cold_release *r)
{return wr_iot_cold_parent_release(s,r);}
int wr_iot_rc_cold_terminal_begin(struct wr_iot_cold_terminal *s,struct wr_iot_cold_parent_release *r)
{return wr_iot_cold_terminal_begin(s,r);}
int wr_iot_rc_cold_terminal_step(struct wr_iot_cold_terminal *s)
{return wr_iot_cold_terminal_step(s);}
int wr_iot_rc_cold_terminal_retire(struct wr_iot_cold_terminal *s)
{return wr_iot_cold_terminal_retire(s);}
