##
#  Samsung Galaxy S7 Edge (SM-G935F, Exynos 8890) platform.
#
#  Experimental display/keypad bring-up; not hardware validated.
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
##

[Defines]
  PLATFORM_NAME                  = hero2lte
  PLATFORM_GUID                  = 7A9E4C2D-3B1F-4C6A-9D8E-2F5A1B7C9E01
  PLATFORM_VERSION               = 0.1
  DSC_SPECIFICATION              = 0x00010005
  OUTPUT_DIRECTORY               = Build/hero2ltePkg
  SUPPORTED_ARCHITECTURES        = AARCH64
  BUILD_TARGETS                  = RELEASE|DEBUG
  SKUID_IDENTIFIER               = DEFAULT
  FLASH_DEFINITION               = hero2ltePkg/hero2lte.fdf
  USE_CUSTOM_DISPLAY_DRIVER      = 0
  UNIXNU_PAYLOAD                 = 0

!include S5E8890Pkg/S5E8890Pkg.dsc.inc

[PcdsFixedAtBuild]
  #
  # DDR Memory
  #
  gArmTokenSpaceGuid.PcdSystemMemoryBase|0x80000000

  #
  # UEFI Stack
  #
  gArmPlatformTokenSpaceGuid.PcdCPUCoresStackBase|0xC9200000
  gArmPlatformTokenSpaceGuid.PcdCPUCorePrimaryStackSize|0x40000

  #
  # SMBIOS
  #
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemManufacturer|"Samsung"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemModel|"Galaxy S7 Edge"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailModel|"hero2lte"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailSku|"SM-G935F_hero2lte"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemBoardModel|"Galaxy S7 Edge"

  #
  # Simple Frame Buffer
  #
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferWidth|1440
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferHeight|2560
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferColorDepth|32

[LibraryClasses]
  #
  # Memory Libraries
  #
  MemoryMapLib|hero2ltePkg/Library/MemoryMapLib/MemoryMapLib.inf
  KeypadDeviceLib|hero2ltePkg/Library/KeypadDeviceLib/KeypadDeviceLib.inf

!if $(UNIXNU_PAYLOAD) == 1
  # UniXNU package, supplied by the device build tree.
  UniXNULib|UniXNUPkg/Library/UniXNULib/UniXNULib.inf
!endif

[Components]
  SiliciumPkg/Drivers/KeypadDeviceDxe/KeypadDeviceDxe.inf
  SiliciumPkg/Drivers/KeypadDxe/KeypadDxe.inf

!if $(UNIXNU_PAYLOAD) == 1
  # UniXNU loader, ramdisk and Darwin handoff.
  UniXNUPkg/Application/UniXNU/UniXNU.inf
  UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf
  UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf
  DarwinBootPkg/Driver/DarwinBoot.inf
!endif
