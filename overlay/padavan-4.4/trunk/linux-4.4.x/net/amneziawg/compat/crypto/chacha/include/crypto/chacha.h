/* SPDX-License-Identifier: GPL-2.0 OR MIT */
/* Linux 4.4 adapter for AmneziaWG header protection's ChaCha API.
 * Use the bundled Zinc implementation; preserve RFC7539 state layout.
 */
#ifndef _AWG_COMPAT_CHACHA_H
#define _AWG_COMPAT_CHACHA_H

#include <linux/string.h>
#include <zinc/chacha20.h>

#define CHACHA_IV_SIZE 16
#define CHACHA_KEY_SIZE 32
#define CHACHA_BLOCK_SIZE 64

static inline void chacha_init(u32 *state, const u32 *key, const u8 *iv)
{
	state[0] = CHACHA20_CONSTANT_EXPA;
	state[1] = CHACHA20_CONSTANT_ND_3;
	state[2] = CHACHA20_CONSTANT_2_BY;
	state[3] = CHACHA20_CONSTANT_TE_K;
	memcpy(state + 4, key, CHACHA_KEY_SIZE);
	state[12] = get_unaligned_le32(iv);
	state[13] = get_unaligned_le32(iv + 4);
	state[14] = get_unaligned_le32(iv + 8);
	state[15] = get_unaligned_le32(iv + 12);
}

static inline void chacha20_crypt(u32 *state, u8 *dst, const u8 *src,
				  unsigned int bytes)
{
	struct chacha20_ctx ctx;
	simd_context_t simd;

	memcpy(ctx.state, state, sizeof(ctx.state));
	simd_get(&simd);
	chacha20(&ctx, dst, src, bytes, &simd);
	simd_put(&simd);
	memcpy(state, ctx.state, sizeof(ctx.state));
}

#endif
