#!/usr/bin/env python3
"""Run the real keypad polling logic against mocked GPIO reads."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(dir=root) as directory:
    directory = Path(directory)
    harness = directory / 'test.c'
    harness.write_text(r'''
#include <assert.h>
#include "Platforms/Samsung/hero2ltePkg/Library/KeypadDeviceLib/KeypadDeviceLib.c"
static UINT32 gpa0 = 0xff, gpa2 = 0xff;
static unsigned events;
static EFI_KEY_DATA last;
UINT32 EFIAPI MmioRead32 (UINTN address) {
  assert(address == 0x10580004 || address == 0x10580044);
  return address == 0x10580004 ? gpa0 : gpa2;
}
static VOID EFIAPI push (KEYPAD_RETURN_API *api, EFI_KEY_DATA *key) {
  events++; last = *key;
}
int main(void) {
  KEYPAD_RETURN_API api = {push};
  KeypadDeviceReset(0);
  KeypadDeviceGetKeys(0, &api, 1000000000);
  assert(events == 0);
  gpa0 &= ~(1U << 3);
  KeypadDeviceGetKeys(0, &api, 1000000000);
  KeypadDeviceGetKeys(0, &api, 10000000);
  assert(events == 0);
  gpa0 |= 1U << 3;
  KeypadDeviceGetKeys(0, &api, 10000000);
  gpa0 &= ~(1U << 3);
  KeypadDeviceGetKeys(0, &api, 10000000);
  KeypadDeviceGetKeys(0, &api, 20000000);
  assert(events == 1 && last.Key.ScanCode == SCAN_UP);
  KeypadDeviceGetKeys(0, &api, 1000000000);
  assert(events == 1);
  gpa0 |= 1U << 3;
  KeypadDeviceGetKeys(0, &api, 1);
  KeypadDeviceGetKeys(0, &api, 20000000);
  gpa0 &= ~(1U << 3);
  KeypadDeviceGetKeys(0, &api, 1);
  KeypadDeviceGetKeys(0, &api, 20000000);
  assert(events == 2);
  gpa0 &= ~((1U << 4) | (1U << 5));
  gpa2 &= ~(1U << 4);
  KeypadDeviceGetKeys(0, &api, 1);
  KeypadDeviceGetKeys(0, &api, ~(UINT64)0);
  assert(events == 5 && last.Key.UnicodeChar == CHAR_CARRIAGE_RETURN);
  assert(mKeys[1].Key.Key.ScanCode == SCAN_DOWN);
  assert(mKeys[2].Key.Key.ScanCode == SCAN_ESC);
  return 0;
}
''')
    executable = directory / 'test'
    subprocess.run(['clang', '-fshort-wchar', '-Werror', '-I', str(root),
                    '-I', str(root / 'Mu_Basecore/MdePkg/Include'),
                    '-I', str(root / 'Mu_Basecore/MdePkg/Include/X64'),
                    '-I', str(root / 'Silicon/Silicium/SiliciumPkg/Include'),
                    str(harness), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
print('PASS: active-low GPIOs, debounce, held key, rearm, and key mappings')
