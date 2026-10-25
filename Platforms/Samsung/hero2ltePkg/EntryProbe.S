// Standalone handoff probe. No stack, FD relocation or UEFI initialization.
.text
.global _Head
_Head:
  b     _Start
  nop
  // The builder copies the template's remaining ARM64 header unchanged.
  .space 48
  .ascii "ARM\x64"
  .long 0

_Start:
  // White band, lines 0-127 of S-Boot's 1440-wide, 32-bpp framebuffer.
  ldr   x7, =0xE2A00000
  mov   w8, #46080
  mov   x9, #-1
1:
  stp   x9, x9, [x7]
  dc    cvac, x7
  add   x7, x7, #16
  subs  w8, w8, #1
  b.ne  1b
  dsb   sy

  // S-Boot a0304/a03d8 and decon_8890/regs-decon.h agree on these bits.
  // Preserve trigger mode: unmask HW TE if enabled, otherwise request SW.
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
  // Retry without depending on timer setup or interrupts.
  mov   w12, #0x100000
5:
  subs  w12, w12, #1
  b.ne  5b
  b     2b
  .ltorg
