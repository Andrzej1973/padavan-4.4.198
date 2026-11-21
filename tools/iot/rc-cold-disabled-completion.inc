/* Private RC exports for disabled completion. */
int wr_iot_rc_cold_disabled_parent_release(struct wr_iot_cold_disabled_parent_release *s,struct wr_iot_cold_disabled_release *r)
{return wr_iot_cold_disabled_parent_release(s,r);}
int wr_iot_rc_cold_disabled_terminal_begin(struct wr_iot_cold_disabled_terminal *s,struct wr_iot_cold_disabled_parent_release *r)
{return wr_iot_cold_disabled_terminal_begin(s,r);}
int wr_iot_rc_cold_disabled_terminal_step(struct wr_iot_cold_disabled_terminal *s)
{return wr_iot_cold_disabled_terminal_step(s);}
int wr_iot_rc_cold_disabled_terminal_retire(struct wr_iot_cold_disabled_terminal *s)
{return wr_iot_cold_disabled_terminal_retire(s);}
