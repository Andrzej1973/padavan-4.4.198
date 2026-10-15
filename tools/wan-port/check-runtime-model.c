/*
 * Host-side model of the WR1200JS switch masks after the runtime WAN-port
 * override.
 *
 * This mirrors get_ports_mask_lan(), get_ports_mask_wan(), the isolation of the
 * board socket in get_isolated_port_x() and the port matrix assignment in
 * esw_mask_bridge_isolate() for this board's topology: external WAN 0, external
 * LAN 1..4, CPU WAN 5, CPU LAN 6, no bridged (bwan) members.
 *
 * It is a model, not the driver: the MIPS build of the real driver is separate
 * evidence. What it does prove is that the mask arithmetic keeps the invariants
 * the reassignment requirement depends on - the selected socket carries the WAN
 * side, the board socket is isolated instead of becoming a LAN port, and no LAN
 * port can still forward into either of them.
 */
#include <stdio.h>

#define ESW_PORT_ID_MAX		6u
#define ESW_EPHY_ID_MAX		4u
#define BOARD_WAN_X		0u
#define CPU_WAN_PORT		5u
#define CPU_LAN_PORT		6u
#define NO_ISOLATED_PORT	(ESW_PORT_ID_MAX + 1u)

#define MASK_CPU_WAN		(1u << CPU_WAN_PORT)
#define MASK_CPU_LAN		(1u << CPU_LAN_PORT)
#define MASK_LAN_EXTERNAL	((1u << 1) | (1u << 2) | (1u << 3) | (1u << 4))

struct switch_model {
	unsigned int wan_port_x;
	unsigned int mask_wan;
	unsigned int mask_lan;
	unsigned int isolated_port_x;
	unsigned int matrix[ESW_PORT_ID_MAX + 1];
};

static unsigned int isolated_port_x(unsigned int wan_port_x)
{
	return (wan_port_x == BOARD_WAN_X) ? NO_ISOLATED_PORT : BOARD_WAN_X;
}

static struct switch_model build(unsigned int wan_port_x)
{
	struct switch_model model;
	unsigned int i;

	model.wan_port_x = wan_port_x;
	model.isolated_port_x = isolated_port_x(wan_port_x);

	model.mask_wan = (1u << wan_port_x) | MASK_CPU_WAN;

	/* get_ports_mask_lan(): LAN sockets, minus the WAN role, minus the
	 * isolated board socket, plus the CPU LAN port. */
	model.mask_lan = MASK_LAN_EXTERNAL | MASK_CPU_LAN;
	model.mask_lan &= ~(1u << wan_port_x);
	model.mask_lan &= ~(1u << model.isolated_port_x);

	for (i = 0; i <= ESW_PORT_ID_MAX; i++)
		model.matrix[i] = 0;

	/* esw_mask_bridge_isolate(): LAN ports, then the isolated socket, then
	 * the WAN side. */
	for (i = 0; i <= ESW_PORT_ID_MAX; i++) {
		if (model.mask_lan & (1u << i))
			model.matrix[i] = model.mask_lan;
	}
	if (model.isolated_port_x <= ESW_EPHY_ID_MAX)
		model.matrix[model.isolated_port_x] = 0;
	for (i = 0; i <= ESW_PORT_ID_MAX; i++) {
		if (model.mask_wan & (1u << i))
			model.matrix[i] = model.mask_wan;
	}

	return model;
}

static int failures;

static void check(int condition, const char *what)
{
	if (!condition) {
		printf("FAIL %s\n", what);
		failures++;
	}
}

static void check_stock(void)
{
	struct switch_model model = build(BOARD_WAN_X);
	unsigned int i;

	check(model.isolated_port_x == NO_ISOLATED_PORT,
	      "the stock selection must not isolate any socket");
	check(model.mask_wan == ((1u << BOARD_WAN_X) | MASK_CPU_WAN),
	      "the stock WAN mask must be the board WAN socket plus CPU WAN");
	check(model.mask_lan == (MASK_LAN_EXTERNAL | MASK_CPU_LAN),
	      "the stock LAN mask must be every LAN socket plus CPU LAN");
	check(model.matrix[BOARD_WAN_X] == model.mask_wan,
	      "the stock WAN socket must forward on the WAN side");
	check(model.matrix[CPU_WAN_PORT] == model.mask_wan,
	      "CPU WAN must forward on the WAN side");
	for (i = 1; i <= ESW_EPHY_ID_MAX; i++) {
		check(model.matrix[i] == model.mask_lan,
		      "every stock LAN socket must forward on the LAN side");
	}
	check(model.matrix[CPU_LAN_PORT] == model.mask_lan,
	      "CPU LAN must forward on the LAN side");
}

static void check_selection(unsigned int selected)
{
	struct switch_model model = build(selected);
	unsigned int i;

	check(model.isolated_port_x == BOARD_WAN_X,
	      "the board socket must be isolated while the role is elsewhere");
	check(model.mask_wan == ((1u << selected) | MASK_CPU_WAN),
	      "the WAN mask must be the selected socket plus CPU WAN");
	check((model.mask_lan & (1u << selected)) == 0,
	      "the selected WAN socket must leave the LAN side");
	check((model.mask_lan & (1u << BOARD_WAN_X)) == 0,
	      "the isolated board socket must leave the LAN side");
	check((model.mask_lan & MASK_CPU_LAN) != 0,
	      "CPU LAN must keep the LAN side");
	check(model.matrix[selected] == model.mask_wan,
	      "the selected WAN socket must forward on the WAN side");
	check(model.matrix[CPU_WAN_PORT] == model.mask_wan,
	      "CPU WAN must forward on the WAN side");
	check(model.matrix[BOARD_WAN_X] == 0,
	      "the isolated board socket must not forward anywhere");
	check((model.matrix[BOARD_WAN_X] & MASK_CPU_WAN) == 0,
	      "the isolated board socket must not reach CPU WAN");

	for (i = 1; i <= ESW_EPHY_ID_MAX; i++) {
		if (i == selected)
			continue;
		check(model.matrix[i] == model.mask_lan,
		      "every remaining LAN socket must forward on the LAN side");
		check((model.matrix[i] & (1u << selected)) == 0,
		      "a remaining LAN socket must not forward into the WAN socket");
		check((model.matrix[i] & (1u << BOARD_WAN_X)) == 0,
		      "a remaining LAN socket must not forward into the isolated socket");
	}

	/* Restoring the board socket must reproduce the stock configuration. */
	check(build(BOARD_WAN_X).mask_lan == (MASK_LAN_EXTERNAL | MASK_CPU_LAN),
	      "restoring the board socket must restore the LAN side");
}

int main(void)
{
	unsigned int selected;

	check_stock();
	for (selected = 1; selected <= ESW_EPHY_ID_MAX; selected++)
		check_selection(selected);

	if (failures) {
		printf("FAIL runtime WAN-port mask model: %d check(s)\n", failures);
		return 1;
	}

	printf("PASS runtime WAN-port mask model: stock and four selections\n");
	return 0;
}
