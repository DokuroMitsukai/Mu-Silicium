#include <Uefi.h>
#include <Library/BaseMemoryLib.h>
#include <Library/CacheMaintenanceLib.h>

EFI_STATUS
EFIAPI
BootMarkerEntry (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE *SystemTable)
{
  // Yellow: DXE dispatched, before CPU/GIC/timer drivers in APRIORI.
  VOID  *FrameBuffer = (VOID *)(UINTN)(BOOT_DIAGNOSTIC_FB + 552960);
  UINTN  Length      = 1440 * 32 * sizeof (UINT32);

  SetMem32 (FrameBuffer, Length, 0x00FFFF00);
  WriteBackDataCacheRange (FrameBuffer, Length);
  return EFI_SUCCESS;
}
