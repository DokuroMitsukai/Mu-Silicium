/**
  hero2lte bring-up display, timer and keypad probe.

  Draws directly into the S-Boot framebuffer so it does not depend on the
  console being initialized yet.  A periodic event proves the GIC/timer path
  and repeated DECON refresh.  A key notify proves the keypad reaches ConIn.

  SPDX-License-Identifier: BSD-2-Clause-Patent
**/

#include <Uefi.h>
#include <Library/CacheMaintenanceLib.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Protocol/GraphicsOutput.h>
#include <Protocol/SimpleTextInEx.h>

#define TIMER_X       20
#define TIMER_Y       20
#define TIMER_SIZE    120
#define KEY_X         20
#define KEY_Y         180
#define KEY_WIDTH     720
#define KEY_HEIGHT    120
#define COUNT_X       20
#define COUNT_Y       340
#define COUNT_STEP    36
#define COUNT_MAX     20

STATIC EFI_GRAPHICS_OUTPUT_PROTOCOL     *mGop;
STATIC EFI_SIMPLE_TEXT_INPUT_EX_PROTOCOL *mConInEx;
STATIC BOOLEAN                           mKeyNotifyDone;
STATIC EFI_EVENT                         mTimer;
STATIC UINT32                            mTick;
STATIC UINT32                            mKeyCount;
STATIC UINT32                            mKeyExpire;

STATIC EFI_KEY_DATA mKeyData[] = {
  { { SCAN_UP,   0 }, { 0, 0 } },
  { { SCAN_DOWN, 0 }, { 0, 0 } },
  { { SCAN_ESC,  0 }, { 0, 0 } },
  { { SCAN_NULL, CHAR_CARRIAGE_RETURN }, { 0, 0 } }
};

STATIC
VOID
FillRect (
  IN UINT32 X,
  IN UINT32 Y,
  IN UINT32 Width,
  IN UINT32 Height,
  IN UINT32 Color
  )
{
  UINT32 *FrameBuffer;
  UINT32  MaxX;
  UINT32  MaxY;
  UINTN   Stride;
  UINT32  Row;

  if (mGop == NULL || mGop->Mode == NULL || mGop->Mode->Info == NULL) {
    return;
  }

  FrameBuffer = (UINT32 *)(UINTN)mGop->Mode->FrameBufferBase;
  MaxX        = mGop->Mode->Info->HorizontalResolution;
  MaxY        = mGop->Mode->Info->VerticalResolution;
  Stride      = mGop->Mode->Info->PixelsPerScanLine;
  if (X >= MaxX || Y >= MaxY) {
    return;
  }
  if (X + Width > MaxX) {
    Width = MaxX - X;
  }
  if (Y + Height > MaxY) {
    Height = MaxY - Y;
  }

  for (Row = 0; Row < Height; Row++) {
    UINT32 *Line = FrameBuffer + (Y + Row) * Stride + X;
    UINTN   Index;

    for (Index = 0; Index < Width; Index++) {
      Line[Index] = Color;
    }
    WriteBackDataCacheRange (Line, Width * sizeof (UINT32));
  }
}

STATIC
EFI_STATUS
EFIAPI
KeyNotify (
  IN EFI_KEY_DATA *KeyData
  )
{
  UINT32 Color = 0x00FFFF00; // Yellow: any other key.

  switch (KeyData->Key.ScanCode) {
    case SCAN_UP:
      Color = 0x00FF0000; // Red
      break;
    case SCAN_DOWN:
      Color = 0x0000FF00; // Green
      break;
    case SCAN_ESC:
      Color = 0x000000FF; // Blue (home)
      break;
    case SCAN_NULL:
      if (KeyData->Key.UnicodeChar == CHAR_CARRIAGE_RETURN) {
        Color = 0x00FFFFFF; // White (power)
      }
      break;
    default:
      break;
  }

  FillRect (KEY_X, KEY_Y, KEY_WIDTH, KEY_HEIGHT, Color);
  mKeyExpire = mTick + 10;
  mKeyCount++;
  if (mKeyCount <= COUNT_MAX) {
    FillRect (COUNT_X + (mKeyCount - 1) * COUNT_STEP, COUNT_Y, 30, 30, 0x00FFFFFF);
  }
  return EFI_SUCCESS;
}

STATIC
VOID
EnsureKeyNotify (
  VOID
  )
{
  EFI_STATUS Status;
  UINTN      Index;
  VOID       *Handle;

  if (mKeyNotifyDone) {
    return;
  }

  Status = gBS->LocateProtocol (&gEfiSimpleTextInputExProtocolGuid, NULL, (VOID **)&mConInEx);
  if (EFI_ERROR (Status)) {
    return;
  }

  mKeyNotifyDone = TRUE;
  for (Index = 0; Index < ARRAY_SIZE (mKeyData); Index++) {
    mConInEx->RegisterKeyNotify (mConInEx, &mKeyData[Index], KeyNotify, &Handle);
  }
}

STATIC
VOID
EFIAPI
TimerTick (
  IN EFI_EVENT Event,
  IN VOID     *Context
  )
{
  UINT32 Color;
  UINT32 Drawn;

  if (mGop == NULL) {
    if (EFI_ERROR (gBS->LocateProtocol (&gEfiGraphicsOutputProtocolGuid, NULL, (VOID **)&mGop))) {
      return;
    }
  }

  mTick++;
  EnsureKeyNotify ();

  // Alternate every five ticks (one second at 200 ms) to prove timer ticks
  // and repeated framebuffer refresh.
  Color = ((mTick / 5) & 1) != 0 ? 0x0000FFFF : 0x00FF00FF;
  FillRect (TIMER_X, TIMER_Y, TIMER_SIZE, TIMER_SIZE, Color);

  if (mKeyExpire != 0 && mTick >= mKeyExpire) {
    FillRect (KEY_X, KEY_Y, KEY_WIDTH, KEY_HEIGHT, 0);
    mKeyExpire = 0;
  }

  // Repaint the key counter in case BDS cleared the screen after the key.
  Drawn = mKeyCount < COUNT_MAX ? mKeyCount : COUNT_MAX;
  if (Drawn != 0) {
    FillRect (COUNT_X, COUNT_Y, Drawn * COUNT_STEP - 6, 30, 0x00FFFFFF);
  }
}

EFI_STATUS
EFIAPI
BringupTestEntry (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE *SystemTable
  )
{
  EFI_STATUS Status;

  gBS->LocateProtocol (&gEfiGraphicsOutputProtocolGuid, NULL, (VOID **)&mGop);

  Status = gBS->CreateEvent (
                  EVT_TIMER | EVT_NOTIFY_SIGNAL,
                  TPL_CALLBACK,
                  TimerTick,
                  NULL,
                  &mTimer
                  );
  if (EFI_ERROR (Status)) {
    return EFI_SUCCESS;
  }

  Status = gBS->SetTimer (mTimer, TimerPeriodic, 2000000);
  if (EFI_ERROR (Status)) {
    gBS->CloseEvent (mTimer);
    return EFI_SUCCESS;
  }

  return EFI_SUCCESS;
}
