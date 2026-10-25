#include <Uefi.h>
#include <Library/BaseMemoryLib.h>
#include <Library/CacheMaintenanceLib.h>
#include <Library/IoLib.h>

EFI_STATUS
EFIAPI
BootMarkerEntry (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE *SystemTable)
{
  // Yellow: DXE dispatched, before CPU/GIC/timer drivers in APRIORI.
  VOID   *FrameBuffer = (VOID *)(UINTN)(BOOT_DIAGNOSTIC_FB + 552960);
  UINTN   Length      = 1440 * 32 * sizeof (UINT32);
  UINT32  Trigger;

  SetMem32 (FrameBuffer, Length, 0x00FFFF00);
  WriteBackDataCacheRange (FrameBuffer, Length);

  // Same trigger handling validated by EntryProbe.S.
  Trigger = MmioRead32 (0x13960070);
  if ((Trigger & BIT4) != 0) {
    Trigger &= ~BIT5;
  } else {
    Trigger |= BIT8;
  }
  MmioWrite32 (0x13960070, Trigger);
  return EFI_SUCCESS;
}
