#!/usr/bin/env python3
"""Check the built RELEASE image, including diagnostic flag propagation."""
import argparse
from pathlib import Path
import struct
import subprocess

from repack_samsung_boot import unpack

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--diagnostics', action='store_true')
parser.add_argument('--bringup-test', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
build = root / 'Build/hero2ltePkg/RELEASE_CLANGPDB'
_, parts, _ = unpack((root / 'Mu-hero2lte.img').read_bytes())
shim = (root / 'BootShim/BootShim.bin').read_bytes()
fd = (build / 'FV/SILICIUM_UEFI.fd').read_bytes()
assert parts == [shim + fd, b'dummy', b'', b'']
assert len(shim) % 16 == 0
if args.diagnostics:
    assert 200 < len(shim) < 512
    assert struct.pack('<Q', 0x13960070) in shim, 'refresh request missing'
else:
    assert 112 <= len(shim) < 256
    assert struct.pack('<Q', 0x13960070) not in shim, 'refresh is not diagnostics-only'
assert len(fd) == 0x200000
assert struct.pack('<Q', 0xB1200000) in fd, 'FD base missing from memory map'
assert struct.pack('<Q', 0xB1400000) in fd, 'stack base missing from memory map'
assert struct.pack('<Q', 0xB1440000) in fd, 'heap base missing from memory map'
assert struct.unpack_from('<Q', shim, 16)[0] == len(parts[0])
helper = build / ('AARCH64/S5E8890Pkg/Library/PlatformSecLib/'
                  'PlatformSecLib/OUTPUT/AArch64/PlatformHelper.obj')
assert struct.pack('<Q', 0x13960070) in helper.read_bytes(), 'SEC refresh not built'
disassembly = subprocess.check_output(['llvm-objdump', '-d', str(helper)], text=True)
assert disassembly.count('dc\tcvac') == int(args.diagnostics), 'SEC marker flag not propagated'
report = (build / 'BUILD_REPORT.TXT').read_text()
assert ('Module Name:          BootMarkerDxe' in report) == args.diagnostics, 'DXE marker not included'
assert ('Module Name:          BringupTestDxe' in report) == args.bringup_test, 'bring-up test not included'
print(f'PASS: RELEASE image, payload/header, SEC and DXE markers={args.diagnostics}, bringup={args.bringup_test}')
