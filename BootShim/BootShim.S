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
  // Clean the relocated FD to the point of coherency, then drop stale
  // instruction cache lines before branching into it.
  //
  // CTR_EL0.DminLine is log2(words per line), so the byte stride is
  // 4 << DminLine. Clean the line containing each address and stop once
  // the line containing the last FD byte has been cleaned; this works for
  // any FD size and never touches a line after the image.
  mrs   x7, ctr_el0
  ubfx  x7, x7, #16, #4
  mov   x8, #4
  lsl   x7, x8, x7
  ldr   x6, =FD_BASE
  ldr   x8, =FD_SIZE
  cbz   x8, 6f
  add   x8, x8, x6
  sub   x8, x8, #1
5:
  dc    cvac, x6
  add   x6, x6, x7
  cmp   x6, x8
  b.ls  5b
6:
  dsb   sy
  ic    iallu
  dsb   sy
  isb
  br    x5

_Dead:
  b     _Dead

.text
.ltorg
.align 4

_Payload:
