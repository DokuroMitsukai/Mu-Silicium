// SPDX-License-Identifier: BSD-2-Clause-Patent
#include <Uefi.h>
#include <Library/IoLib.h>
#include <Library/KeypadDeviceLib.h>

#define GPIO_ALIVE_BASE  0x10580000
#define GPIO_DAT         0x04
#define DEBOUNCE_NS      20000000ULL

typedef struct {
  UINT32       Bank;
  UINT32       Pin;
  EFI_KEY_DATA Key;
  BOOLEAN      Sample;
  BOOLEAN      Pressed;
  UINT64       StableTime;
} HERO_KEY;

// DT gpio_keys: GPA0[3:5], GPA2[4], active low. Leave mux/pulls untouched.
STATIC HERO_KEY mKeys[] = {
  { 0x00, 3, { { SCAN_UP,   0 }, { 0, 0 } }, FALSE, FALSE, 0 },
  { 0x00, 4, { { SCAN_DOWN, 0 }, { 0, 0 } }, FALSE, FALSE, 0 },
  { 0x00, 5, { { SCAN_ESC,  0 }, { 0, 0 } }, FALSE, FALSE, 0 },
  { 0x40, 4, { { SCAN_NULL, CHAR_CARRIAGE_RETURN }, { 0, 0 } }, FALSE, FALSE, 0 }
};

EFI_STATUS
EFIAPI
KeypadDeviceReset (KEYPAD_DEVICE_PROTOCOL *This)
{
  for (UINTN Index = 0; Index < ARRAY_SIZE (mKeys); Index++) {
    mKeys[Index].Sample     = FALSE;
    mKeys[Index].Pressed    = FALSE;
    mKeys[Index].StableTime = 0;
  }

  return EFI_SUCCESS;
}

EFI_STATUS
KeypadDeviceGetKeys (
  KEYPAD_DEVICE_PROTOCOL *This,
  KEYPAD_RETURN_API      *KeypadReturnApi,
  UINT64                  Delta)
{
  for (UINTN Index = 0; Index < ARRAY_SIZE (mKeys); Index++) {
    HERO_KEY *Key = &mKeys[Index];
    BOOLEAN Pressed = (MmioRead32 (GPIO_ALIVE_BASE + Key->Bank + GPIO_DAT) &
                       (1U << Key->Pin)) == 0;

    if (Pressed != Key->Sample) {
      Key->Sample     = Pressed;
      Key->StableTime = 0;
      continue;
    }

    if (Key->StableTime < DEBOUNCE_NS) {
      Key->StableTime += MIN (Delta, DEBOUNCE_NS - Key->StableTime);
    }

    if (Key->StableTime == DEBOUNCE_NS && Pressed != Key->Pressed) {
      Key->Pressed = Pressed;
      if (Pressed) {
        KeypadReturnApi->PushEfikeyBufTail (KeypadReturnApi, &Key->Key);
      }
    }
  }

  return EFI_SUCCESS;
}
