//
// Copyright (c) 2012-2013, ARM Limited. All rights reserved.
// SPDX-License-Identifier: BSD-2-Clause-Patent
//

#include <AsmMacroLib.h>

ASM_FUNC (PlatformAssemblyInitialize)
#if BOOT_DIAGNOSTIC_FB
  // Blue: SEC entry reached, before stack initialization.
  ldr   x7, =(BOOT_DIAGNOSTIC_FB + 368640)
  mov   w8, #11520
  ldr   x9, =0x000000ff000000ff
1:
  stp   x9, x9, [x7]
  dc    cvac, x7
  add   x7, x7, #16
  subs  w8, w8, #1
  b.ne  1b
  dsb   sy
  // Same trigger handling validated by EntryProbe.S.
  ldr   x10, =0x13960070
2:
  ldr   w11, [x10]
  tbz   w11, #4, 3f
  bic   w11, w11, #0x20
  b     4f
3:
  orr   w11, w11, #0x100
4:
  str   w11, [x10]
  dsb   sy
#endif
  // Nothing to do here.
  ret
