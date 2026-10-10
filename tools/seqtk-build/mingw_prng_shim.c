/* SPDX-License-Identifier: MIT
 *
 * POSIX PRNG shims missing from the MinGW/MSVC runtime.
 * Implements the 48-bit linear congruential generator defined by the
 * Single UNIX Specification so seqtk's randbase and `mergefa -r` keep
 * working on Windows.
 *
 * Copyright (c) 2026 seqtk-gui contributors
 *
 * This file is a separate work of this project, licensed MIT like the rest of
 * seqtk-gui (see LICENSE.txt). It is linked alongside upstream seqtk.c but is
 * not part of upstream seqtk and does not place that project's MIT terms on
 * this file. Because it is compiled into bin/windows/seqtk.exe, it is the
 * change that makes the shipped binary a modified build of seqtk; that is
 * recorded in docs/BUILD_SEQTK.md and docs/THIRD_PARTY_NOTICES.md.
 */
#include <stdlib.h>

#define MULTIPLIER 0x5DEECE66ULL
#define ADDEND     0xBULL
#define MASK48     ((1ULL << 48) - 1)

static unsigned long long g_state48;

void srand48(long seedval)
{
	g_state48 = (((unsigned long long)seedval << 16) | 0x3333ULL) & MASK48;
}

static unsigned long long next48(void)
{
	g_state48 = (g_state48 * MULTIPLIER + ADDEND) & MASK48;
	return g_state48;
}

long lrand48(void)
{
	return (long)(next48() >> 17);
}

double drand48(void)
{
	return (double)next48() / 281474976710656.0;
}
