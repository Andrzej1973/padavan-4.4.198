/* Host-only checked PCIe transaction observation for the MT7603 remove plan.
 * This is not a DMA or adapter-release receipt and has no vendor binding. */
#ifndef WR_IOT_PCI_TRANSACTION_OBSERVER_H
#define WR_IOT_PCI_TRANSACTION_OBSERVER_H

#define WR_IOT_PCI_COMMAND 0x04U
#define WR_IOT_PCI_COMMAND_MASTER 0x0004U
#define WR_IOT_PCI_EXP_DEVSTA 0x0aU
#define WR_IOT_PCI_EXP_DEVSTA_TRPND 0x0020U

enum wr_iot_pci_transaction_result {
 WR_IOT_PCI_TX_INVALID = 0,
 WR_IOT_PCI_TX_MASTER_ACTIVE,
 WR_IOT_PCI_TX_PENDING,
 WR_IOT_PCI_TX_CLEAR_OBSERVED
};

/* Captured by the lifetime owner for the radio epoch under its shared lock.
 * A clear result from an older lifecycle must not authorize release. */
struct wr_iot_pci_observation {
 enum wr_iot_pci_transaction_result result;
 unsigned long radio_epoch;
};

struct wr_iot_pci_transaction_io {
 void *context;
 int (*clear_master)(void *context);
 int (*read_word)(void *context, unsigned int offset, unsigned short *value);
 void (*sleep_ms)(void *context, unsigned int milliseconds);
};

/* Only the final PCI remove owner may call this, after PDMA stop and its
 * writeback. It is not safe for ordinary interface down/reopen. The caller
 * must exclude all writers that could re-enable bus mastering until free. */
static inline enum wr_iot_pci_transaction_result
wr_iot_pci_disable_master_and_observe(
 const struct wr_iot_pci_transaction_io *io, unsigned int pcie_cap_offset);

static inline enum wr_iot_pci_transaction_result
wr_iot_pci_observe_transaction_clear(
 const struct wr_iot_pci_transaction_io *io, unsigned int pcie_cap_offset)
{
 unsigned short value;
 unsigned int i;
 const unsigned int delays[] = {0U, 100U, 200U, 400U};

 if (!io || !io->read_word || !io->sleep_ms ||
     pcie_cap_offset < 0x40U || pcie_cap_offset > 0xf0U ||
     (pcie_cap_offset & 3U))
  return WR_IOT_PCI_TX_INVALID;

 if (io->read_word(io->context, WR_IOT_PCI_COMMAND, &value) != 0 ||
     value == 0xffffU)
  return WR_IOT_PCI_TX_INVALID;
 if (value & WR_IOT_PCI_COMMAND_MASTER)
  return WR_IOT_PCI_TX_MASTER_ACTIVE;

 for (i = 0; i < 4U; ++i) {
  if (delays[i])
   io->sleep_ms(io->context, delays[i]);
  if (io->read_word(io->context,
      pcie_cap_offset + WR_IOT_PCI_EXP_DEVSTA, &value) != 0 ||
      value == 0xffffU)
   return WR_IOT_PCI_TX_INVALID;
  if (!(value & WR_IOT_PCI_EXP_DEVSTA_TRPND)) {
   /* A second read catches re-enabling during the bounded wait. The caller
    * must still fence all bus-master writers through adapter lifetime. */
   if (io->read_word(io->context, WR_IOT_PCI_COMMAND, &value) != 0 ||
       value == 0xffffU)
    return WR_IOT_PCI_TX_INVALID;
   return (value & WR_IOT_PCI_COMMAND_MASTER) ?
    WR_IOT_PCI_TX_MASTER_ACTIVE : WR_IOT_PCI_TX_CLEAR_OBSERVED;
  }
 }
 return WR_IOT_PCI_TX_PENDING;
}

static inline enum wr_iot_pci_transaction_result
wr_iot_pci_disable_master_and_observe(
 const struct wr_iot_pci_transaction_io *io, unsigned int pcie_cap_offset)
{
 if (!io || !io->clear_master || !io->read_word || !io->sleep_ms ||
     pcie_cap_offset < 0x40U || pcie_cap_offset > 0xf0U ||
     (pcie_cap_offset & 3U))
  return WR_IOT_PCI_TX_INVALID;
 if (io->clear_master(io->context) != 0)
  return WR_IOT_PCI_TX_INVALID;
 return wr_iot_pci_observe_transaction_clear(io, pcie_cap_offset);
}

#endif
