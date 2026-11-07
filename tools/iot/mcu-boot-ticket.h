#ifndef WR_IOT_MCU_BOOT_TICKET_H
#define WR_IOT_MCU_BOOT_TICKET_H
/* Software provenance only. No firmware/RX epoch or normal admission receipt. */
struct wr_iot_mcu_boot_ticket {
 unsigned long peer_serial,radio_serial,radio_epoch,close_serial,close_epoch;
};
#endif
