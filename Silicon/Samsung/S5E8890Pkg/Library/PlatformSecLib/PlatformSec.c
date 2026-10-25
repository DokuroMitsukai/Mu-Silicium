/**
  Copyright (c) 2011-2012, ARM Limited. All rights reserved.
  SPDX-License-Identifier: BSD-2-Clause-Patent
**/

#include <Library/IoLib.h>
#include <Library/DebugLib.h>
#include <Library/PlatformSecLib.h>
#include <Library/MemoryMapHelperLib.h>

#include "PlatformRegisters.h"

VOID
PlatformInitialize ()
{
  EFI_STATUS                   Status;
  EFI_MEMORY_REGION_DESCRIPTOR DeconRegion;

  Status = LocateMemoryRegionByName ("Decon", &DeconRegion);
  if (EFI_ERROR (Status)) {
    return;
  }

  // Preserve S-Boot's display state; the 8895 trigger value is not valid evidence.
  DEBUG ((DEBUG_INFO, "DECON trigger: 0x%x\n",
          MmioRead32 (DeconRegion.Address + HW_SW_TRIG_CONTROL)));
}
