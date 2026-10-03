/* MI-MINI platform attachment candidate. No hardware/runtime validation yet. */
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/init.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/platform_device.h>

#if !defined(CONFIG_SOC_MT7620) || defined(MODULE)
#error "MI-MINI candidate requires a built-in MT7620 kernel configuration"
#endif

extern int mi_mini_radio_attach(void __iomem *base, unsigned int irq);
extern void mi_mini_radio_detach(void);
static struct platform_device *mi_mini_owner;

static int mi_mini_probe(struct platform_device *pdev)
{
	struct resource *resource;
	void __iomem *base;
	int irq, result;

	if (mi_mini_owner)
		return -EBUSY;
	irq = platform_get_irq(pdev, 0);
	if (irq < 0)
		return irq;
	resource = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!resource)
		return -EINVAL;
	base = devm_ioremap_resource(&pdev->dev, resource);
	if (IS_ERR(base))
		return PTR_ERR(base);
	result = mi_mini_radio_attach(base, irq);
	if (result)
		return result;
	mi_mini_owner = pdev;
	return 0;
}

static int mi_mini_remove(struct platform_device *pdev)
{
	if (mi_mini_owner == pdev) {
		mi_mini_radio_detach();
		mi_mini_owner = NULL;
	}
	return 0;
}

static const struct of_device_id mi_mini_match[] = {
	{ .compatible = "xiaomi,mi-mini-mt7620-radio" },
	{ }
};

static struct platform_driver mi_mini_driver = {
	.probe = mi_mini_probe,
	.remove = mi_mini_remove,
	.driver = {
		.name = "mi-mini-mt7620-radio",
		.of_match_table = mi_mini_match,
	},
};

static int __init mi_mini_platform_init(void)
{
	return platform_driver_register(&mi_mini_driver);
}
device_initcall(mi_mini_platform_init);
