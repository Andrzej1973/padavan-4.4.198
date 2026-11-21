/* Extra Linux references only; not a PCI hardware or DMA retirement pin. */
#ifndef WR_IOT_PHYSICAL_STOP_PIN_TYPES_H
#define WR_IOT_PHYSICAL_STOP_PIN_TYPES_H
struct task_struct;
struct net_device;
struct wr_iot_physical_stop_pins {
 struct task_struct *task;
 struct net_device *device;
 unsigned int module;
};
#endif
