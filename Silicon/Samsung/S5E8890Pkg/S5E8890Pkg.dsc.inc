##
#  Samsung Exynos 8890 (S5E8890) support package.
#
#  This is deliberately a minimal SoC package for the first bring-up stage.
#  It uses the generic Silicium core (GICv2, ARM generic timer, SimpleFbDxe)
#  and does not pull in the Samsung PMIC/GPIO/UFS stack, which still needs
#  8890-specific drivers.
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
##

[Defines]
  #
  # Timer
  #
  USE_PHYSICAL_TIMER                         = 1

  #
  # KEP
  #
  HAS_CNTFRQ_EL0_EMPTY_ERRATA                = 1

!include SiliciumPkg/SiliciumPkg.dsc.inc

[BuildOptions]
  *_*_AARCH64_CC_FLAGS = -march=armv8-a+crypto
  *_CLANGPDB_AARCH64_CC_FLAGS = -D HAS_CNTFRQ_EL0_EMPTY_ERRATA=$(HAS_CNTFRQ_EL0_EMPTY_ERRATA)

[PcdsFixedAtBuild]
  #
  # ACPI
  #
  gEfiMdeModulePkgTokenSpaceGuid.PcdAcpiDefaultOemTableId|0x2030393838453553
  gEfiMdeModulePkgTokenSpaceGuid.PcdAcpiDefaultOemRevision|0x8890

  #
  # CPU
  #
  gArmPlatformTokenSpaceGuid.PcdCoreCount|8
  gArmPlatformTokenSpaceGuid.PcdClusterCount|2

  #
  # GICv2: distributor at 0x11001000, CPU interface at 0x11002000.
  #
  gArmTokenSpaceGuid.PcdGicDistributorBase|0x11001000
  gArmTokenSpaceGuid.PcdGicInterruptInterfaceBase|0x11002000

  #
  # Timer
  #
  gSiliciumPkgTokenSpaceGuid.PcdTimerFreqOverwrite|26000000

  #
  # SMBIOS
  #
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosProcessorModel|"Exynos (TM) 8890 @ 2.60 GHz"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosProcessorPartNumber|"S5E8890"

[LibraryClasses]
  #
  # SEC Libraries
  #
  PlatformSecLib|S5E8890Pkg/Library/PlatformSecLib/PlatformSecLib.inf

  #
  # Memory Libraries
  #
  RamManagerLib|SiliciumNullPkg/Library/RamManagerLibNull/RamManagerLibNull.inf
