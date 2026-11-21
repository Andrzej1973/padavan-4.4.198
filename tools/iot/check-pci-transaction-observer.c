#include <assert.h>
#include <stdio.h>
#include "pci-transaction-observer.h"

struct fake_pci {
 unsigned short command;
 unsigned short devsta[4];
 unsigned int reads, sleeps, fail_read, devsta_reads, command_reads;
 unsigned int reenable_on_command_read;
 unsigned int clear_calls, fail_clear, silent_clear;
};

static int fake_clear_master(void *context)
{
 struct fake_pci *pci = context;
 ++pci->clear_calls;
 if (pci->fail_clear)
  return -1;
 if (!pci->silent_clear)
  pci->command &= (unsigned short)~WR_IOT_PCI_COMMAND_MASTER;
 return 0;
}

static int fake_read(void *context, unsigned int offset, unsigned short *value)
{
 struct fake_pci *pci = context;
 if (++pci->reads == pci->fail_read)
  return -1;
 if (offset == WR_IOT_PCI_COMMAND) {
  if (++pci->command_reads == pci->reenable_on_command_read)
   pci->command |= WR_IOT_PCI_COMMAND_MASTER;
  *value = pci->command;
  return 0;
 }
 assert(offset == 0x70U + WR_IOT_PCI_EXP_DEVSTA);
 *value = pci->devsta[pci->devsta_reads++];
 return 0;
}

static void fake_sleep(void *context, unsigned int milliseconds)
{
 struct fake_pci *pci = context;
 assert(milliseconds == 100U || milliseconds == 200U ||
        milliseconds == 400U);
 ++pci->sleeps;
}

int main(void)
{
 struct fake_pci pci = {0};
 struct wr_iot_pci_transaction_io io = {
  &pci, fake_clear_master, fake_read, fake_sleep};

 pci = (struct fake_pci){.command = WR_IOT_PCI_COMMAND_MASTER};
 assert(wr_iot_pci_disable_master_and_observe(&io, 0x70U) ==
        WR_IOT_PCI_TX_CLEAR_OBSERVED);
 assert(pci.clear_calls == 1U && pci.command_reads == 2U);

 pci = (struct fake_pci){.command = WR_IOT_PCI_COMMAND_MASTER,
                         .silent_clear = 1U};
 assert(wr_iot_pci_disable_master_and_observe(&io, 0x70U) ==
        WR_IOT_PCI_TX_MASTER_ACTIVE);

 pci = (struct fake_pci){.command = WR_IOT_PCI_COMMAND_MASTER,
                         .fail_clear = 1U};
 assert(wr_iot_pci_disable_master_and_observe(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);
 assert(pci.reads == 0U);

 io.clear_master = 0;
 assert(wr_iot_pci_disable_master_and_observe(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);
 io.clear_master = fake_clear_master;

 pci = (struct fake_pci){.command = WR_IOT_PCI_COMMAND_MASTER};
 assert(wr_iot_pci_disable_master_and_observe(&io, 0U) ==
        WR_IOT_PCI_TX_INVALID);
 assert(pci.clear_calls == 0U);

 pci = (struct fake_pci){0};

 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_CLEAR_OBSERVED);
 assert(pci.reads == 3U && pci.sleeps == 0U);

 pci = (struct fake_pci){.reenable_on_command_read = 2U};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_MASTER_ACTIVE);
 assert(pci.reads == 3U);

 pci = (struct fake_pci){.fail_read = 3U};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.command = 0U};

 pci = (struct fake_pci){.command = WR_IOT_PCI_COMMAND_MASTER};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_MASTER_ACTIVE);
 assert(pci.reads == 1U);

 pci = (struct fake_pci){.command = 0xffffU};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.fail_read = 1U};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.fail_read = 2U};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.devsta = {WR_IOT_PCI_EXP_DEVSTA_TRPND},
                         .fail_read = 3U};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.devsta = {0xffffU}};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_INVALID);

 pci = (struct fake_pci){.devsta = {
  WR_IOT_PCI_EXP_DEVSTA_TRPND, WR_IOT_PCI_EXP_DEVSTA_TRPND,
  WR_IOT_PCI_EXP_DEVSTA_TRPND, WR_IOT_PCI_EXP_DEVSTA_TRPND}};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_PENDING);
 assert(pci.reads == 5U && pci.sleeps == 3U);

 pci = (struct fake_pci){.devsta = {
  WR_IOT_PCI_EXP_DEVSTA_TRPND, 0U}};
 assert(wr_iot_pci_observe_transaction_clear(&io, 0x70U) ==
        WR_IOT_PCI_TX_CLEAR_OBSERVED);
 assert(pci.reads == 4U && pci.sleeps == 1U);

 assert(wr_iot_pci_observe_transaction_clear(&io, 0U) ==
        WR_IOT_PCI_TX_INVALID);
 puts("PASS checked PCIe transaction observer fault cases");
 return 0;
}
