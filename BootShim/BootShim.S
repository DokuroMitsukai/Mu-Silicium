#if BOOT_DIAGNOSTIC_FB
  // hero2lte: one 32-scanline band per stage; preserve DECON state.
  .macro marker color, offset
  ldr   x7, =(BOOT_DIAGNOSTIC_FB + \offset)
  mov   w8, #11520
  ldr   x9, =\color
1:
  stp   x9, x9, [x7]
  dc    cvac, x7
  add   x7, x7, #16
  subs  w8, w8, #1
  b.ne  1b
  dsb   sy
  .endm

  // hero2lte: same trigger handling validated by EntryProbe.S.
  .macro refresh
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
  .endm
#endif

_Head:
  adr   x1, _Payload    /* Set _Entry address */
  b     _Start          /* Jump to the real code */

#if REQUIRES_KERNEL_HEADER == 1
_StackBase:
  .quad FD_BASE         /* Text Offset */

_StackSize:
  .quad FD_SIZE + (_Payload - _Head) /* Shim and appended FD */
  .quad 0               /* Flags */
  .quad 0               /* Reserved */
  .quad 0               /* Reserved */
  .quad 0               /* Reserved */
  .ascii "ARM\x64"      /* ARM64 Magic */
  .long 0               /* Reserved */
#endif

_Start:
#if BOOT_DIAGNOSTIC_FB
  marker 0x00ff000000ff0000, 0 // Red: shim entered, before FD writes.
  refresh
#endif
  mov   x4, x1
  ldr   x5, =FD_BASE
  cmp   x4, x5
  beq   _Entry
  ldr   x6,  =FD_SIZE

_CopyLoop:
  ldp   x2, x3, [x4], #16
  stp   x2, x3, [x5], #16
  subs  x6, x6, #16
  b.ne  _CopyLoop
  ldr   x5, =FD_BASE

_Entry:
#if BOOT_DIAGNOSTIC_FB
  marker 0x0000ff000000ff00, 184320 // Green: FD copied (or already in place).
  refresh
#endif
  br    x5

_Dead:
  b     _Dead

.text
.ltorg
.align 4

_Payload:
