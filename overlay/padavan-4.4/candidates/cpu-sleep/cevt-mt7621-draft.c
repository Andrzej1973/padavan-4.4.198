/*
 * This file is subject to the terms and conditions of the GNU General Public
 * License.  See the file "COPYING" in the main directory of this archive
 * for more details.
 *
 * Copyright (C) 2013 by John Crispin <blogic@openwrt.org>
 */

#include <linux/clockchips.h>
#include <linux/clocksource.h>
#include <linux/interrupt.h>
#include <linux/reset.h>
#include <linux/init.h>
#include <linux/time.h>
#include <linux/of.h>
#include <linux/of_irq.h>
#include <linux/of_address.h>
#include <linux/sched_clock.h>

#include <asm/mach-ralink/ralink_regs.h>

#define SYSTICK_FREQ		(50 * 1000)

#define SYSTICK_CONFIG		0x00
#define SYSTICK_COMPARE		0x04
#define SYSTICK_COUNT		0x08

/* route systick irq to mips irq 7 instead of the r4k-timer */
#define CFG_EXT_STK_EN		0x2
/* enable the counter */
#define CFG_CNT_EN		0x1

/* mt7620 frequency scaling defines */
#define CLK_LUT_CFG	0x40
#define SLEEP_EN	BIT(31)

struct systick_device {
	void __iomem *membase;
	struct clock_event_device dev;
	int irq_requested;
	int freq_scale;
	void __iomem *sleep_control;
	u32 saved_sleep_ratio;
	int mt7621;
};

static void (*systick_freq_scaling)(struct systick_device *sdev, int status);
/* Consumed by GIC only after explicit early systick initialization. */
bool mt7621_systick_ready;

static int systick_set_oneshot(struct clock_event_device *evt);
static int systick_shutdown(struct clock_event_device *evt);

static inline void mt7620_freq_scaling(struct systick_device *sdev, int status)
{
	if (sdev->freq_scale == status)
		return;

	sdev->freq_scale = status;

	pr_info("%s: %s autosleep mode\n", sdev->dev.name,
			(status) ? ("enable") : ("disable"));
	if (status)
		rt_sysc_w32(rt_sysc_r32(CLK_LUT_CFG) | SLEEP_EN, CLK_LUT_CFG);
	else
		rt_sysc_w32(rt_sysc_r32(CLK_LUT_CFG) & ~SLEEP_EN, CLK_LUT_CFG);
}


/* Draft MT7621 callback. Enable only after stable SMP broadcast is wired. */
static void mt7621_freq_scaling(struct systick_device *sdev, int status)
{
	u32 value;
	if (!sdev->sleep_control || sdev->freq_scale == status)
		return;
	value = ioread32(sdev->sleep_control);
	if (status) {
		sdev->saved_sleep_ratio = value & 0x0f0f;
		value = (value & ~0x0f0f) | 0x0404;
	} else {
		value = (value & ~0x0f0f) | sdev->saved_sleep_ratio;
	}
	iowrite32(value, sdev->sleep_control);
	sdev->freq_scale = status;
}

static inline unsigned int read_count(struct systick_device *sdev)
{
	return ioread32(sdev->membase + SYSTICK_COUNT);
}

static inline unsigned int read_compare(struct systick_device *sdev)
{
	return ioread32(sdev->membase + SYSTICK_COMPARE);
}

static inline void write_compare(struct systick_device *sdev, unsigned int val)
{
	iowrite32(val, sdev->membase + SYSTICK_COMPARE);
}

static int systick_next_event(unsigned long delta,
				struct clock_event_device *evt)
{
	struct systick_device *sdev;
	u16 deadline, now;

	sdev = container_of(evt, struct systick_device, dev);
	if (delta < 3 || delta > 0x7fff)
		return -ETIME;
	deadline = (u16)read_count(sdev) + delta;
	write_compare(sdev, deadline);
	now = read_count(sdev);
	return (s16)(now - deadline) >= 0 ? -ETIME : 0;
}

static void systick_event_handler(struct clock_event_device *dev)
{
	/* noting to do here */
}

static irqreturn_t systick_interrupt(int irq, void *dev_id)
{
	int ret = 0;
	struct clock_event_device *cdev;
	struct systick_device *sdev;

	if (read_c0_cause() & STATUSF_IP7) {
		cdev = (struct clock_event_device *) dev_id;
		sdev = container_of(cdev, struct systick_device, dev);

		/* Clear Count/Compare Interrupt */
		write_compare(sdev, read_compare(sdev));
		cdev->event_handler(cdev);
		ret = 1;
	}

	return IRQ_RETVAL(ret);
}

static struct systick_device systick = {
	.dev = {
		.features		= CLOCK_EVT_FEAT_ONESHOT,
		.set_next_event		= systick_next_event,
		.set_state_shutdown	= systick_shutdown,
		.set_state_oneshot	= systick_set_oneshot,
		.event_handler		= systick_event_handler,
	},
};

static u64 notrace mt7621_systick_sched_read(void)
{
	return ioread32(systick.membase + SYSTICK_COUNT) & 0xffff;
}

static struct irqaction systick_irqaction = {
	.handler = systick_interrupt,
	.flags = IRQF_PERCPU | IRQF_TIMER,
	.dev_id = &systick.dev,
};

static int systick_shutdown(struct clock_event_device *evt)
{
	struct systick_device *sdev;

	sdev = container_of(evt, struct systick_device, dev);

	if (sdev->irq_requested)
		remove_irq(systick.dev.irq, &systick_irqaction);
	sdev->irq_requested = 0;
	iowrite32(CFG_CNT_EN, systick.membase + SYSTICK_CONFIG);

	if (systick_freq_scaling)
		systick_freq_scaling(sdev, 0);

	return 0;
}

static int systick_set_oneshot(struct clock_event_device *evt)
{
	struct systick_device *sdev;

	sdev = container_of(evt, struct systick_device, dev);

	if (!sdev->irq_requested) {
		int error = setup_irq(systick.dev.irq, &systick_irqaction);
		if (error)
			return error;
	}
	sdev->irq_requested = 1;
	iowrite32(CFG_EXT_STK_EN | CFG_CNT_EN,
		  systick.membase + SYSTICK_CONFIG);

	if (systick_freq_scaling)
		systick_freq_scaling(sdev, 1);

	return 0;
}

static const struct of_device_id systick_match[] = {
	{ .compatible = "ralink,mt7620a-systick", .data = mt7620_freq_scaling},
	{ .compatible = "mediatek,mt7621-systick", .data = mt7621_freq_scaling},
	{},
};

static void __init ralink_systick_init(struct device_node *np)
{
	const struct of_device_id *match;
	int rating = 200;
	int error;
	u32 previous_config;

	systick.membase = of_iomap(np, 0);
	if (!systick.membase)
		return;

	match = of_match_node(systick_match, np);
	if (of_device_is_compatible(np, "mediatek,mt7621-systick")) {
		/* Second DT resource must describe RBUS matrix + 0x10. */
		systick.sleep_control = of_iomap(np, 1);
		if (!systick.sleep_control) {
			iounmap(systick.membase);
			systick.membase = NULL;
			return;
		}
		systick.mt7621 = 1;
	}
	if (match) {
		systick_freq_scaling = match->data;
		/*
		 * cevt-r4k uses 300, make sure systick
		 * gets used if available
		 */
		rating = 310;
	}

	/* register clock event */
	systick.dev.irq = irq_of_parse_and_map(np, 0);
	if (!systick.dev.irq) {
		pr_err("%s: request_irq failed", np->name);
		goto unmap;
	}
	systick_irqaction.name = np->name;
	/* Validate IRQ before publishing a stable time source or enabling sleep. */
	error = setup_irq(systick.dev.irq, &systick_irqaction);
	if (error) {
		pr_err("%s: systick IRQ setup failed: %d\n", np->name, error);
		goto unmap;
	}
	systick.irq_requested = 1;
	previous_config = ioread32(systick.membase + SYSTICK_CONFIG);
	iowrite32(CFG_CNT_EN, systick.membase + SYSTICK_CONFIG);
	error = clocksource_mmio_init(systick.membase + SYSTICK_COUNT, np->name,
		SYSTICK_FREQ, systick.mt7621 ? 350 : rating, 16, clocksource_mmio_readl_up);
	if (error) {
		iowrite32(previous_config, systick.membase + SYSTICK_CONFIG);
		remove_irq(systick.dev.irq, &systick_irqaction);
		systick.irq_requested = 0;
		goto unmap;
	}
	if (systick.mt7621)
		sched_clock_register(mt7621_systick_sched_read, 16, SYSTICK_FREQ);
	mt7621_systick_ready = systick.mt7621;
	systick.dev.name = np->name;
	systick.dev.rating = systick.mt7621 ? 250 : rating;
	systick.dev.cpumask = cpumask_of(0);
	clockevents_config_and_register(&systick.dev, SYSTICK_FREQ, 0x3, 0x7fff);
	pr_info("%s: running - mult: %d, shift: %d\n",
			np->name, systick.dev.mult, systick.dev.shift);
	return;

unmap:
	if (systick.sleep_control)
		iounmap(systick.sleep_control);
	iounmap(systick.membase);
	systick.sleep_control = NULL;
	systick.membase = NULL;
	systick_freq_scaling = NULL;
}

/* Draft: call before clocksource_probe(), making GIC selection deterministic. */
void __init mt7621_systick_early_init(void)
{
	struct device_node *node;
	node = of_find_compatible_node(NULL, NULL, "mediatek,mt7621-systick");
	if (!node)
		return;
	if (of_device_is_available(node))
		ralink_systick_init(node);
	of_node_put(node);
}


