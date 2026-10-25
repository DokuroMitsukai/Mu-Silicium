ARCH              = arm64
TARGET            = aarch64-linux-gnu
CC                = clang
CFLAGS            = --target=$(TARGET)
BOOT_DIAGNOSTIC_FB ?= 0
OBJCOPY           = llvm-objcopy

all: BootShim.elf BootShim.bin

BootShim.bin: BootShim.elf
	$(OBJCOPY) -O binary $< $@

BootShim.elf: BootShim.S
	$(CC) ${CFLAGS} -c $< -o $@ -DREQUIRES_KERNEL_HEADER=$(REQUIRES_KERNEL_HEADER) -DFD_BASE=$(FD_BASE) -DFD_SIZE=$(FD_SIZE) -DBOOT_DIAGNOSTIC_FB=$(BOOT_DIAGNOSTIC_FB)

BootShim.S:
