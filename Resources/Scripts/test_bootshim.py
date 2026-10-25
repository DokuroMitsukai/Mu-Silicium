#!/usr/bin/env python3
"""Check BootShim layout with and without its ARM64 header."""
from pathlib import Path
import struct
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(dir=root) as directory:
    directory = Path(directory)
    for header, base, size, marker in ((1, 0xC9000000, 0x200000, 0),
                                       (1, 0xC9123000, 0x210000, 0),
                                       (0, 0xC9000000, 0x200000, 0),
                                       (1, 0xC9000000, 0x200000, 0xE2A00000)):
        obj, binary = directory / 'shim.o', directory / 'shim.bin'
        subprocess.run(['clang', '--target=aarch64-linux-gnu', '-c', str(root / 'BootShim/BootShim.S'),
                        '-o', str(obj), f'-DREQUIRES_KERNEL_HEADER={header}',
                        f'-DFD_BASE={base}', f'-DFD_SIZE={size}',
                        f'-DBOOT_DIAGNOSTIC_FB={marker}'], check=True)
        subprocess.run(['llvm-objcopy', '-O', 'binary', str(obj), str(binary)], check=True)
        symbols = subprocess.check_output(['llvm-nm', '-n', str(obj)], text=True)
        payload = next(int(line.split()[0], 16) for line in symbols.splitlines()
                       if line.split()[-1] == '_Payload')
        data = binary.read_bytes()
        assert payload == len(data), 'literal pool lies after payload label'
        assert payload % 16 == 0
        if header:
            assert data[56:60] == b'ARM\x64'
            assert struct.unpack_from('<Q', data, 16)[0] == len(data) + size
        disassembly = subprocess.check_output(['llvm-objdump', '-d', str(obj)], text=True)
        assert disassembly.count('dc\tcvac') == (2 if marker else 0)
        if marker:
            assert struct.pack('<Q', marker + 184320) in data
            assert struct.pack('<Q', 0x13960070) in data
            assert disassembly.count('stp\tx9, x9') == 2
            assert disassembly.count('dsb\tsy') >= 2
        print(f'PASS: header={header}, base={base:#x}, size={size:#x}, marker={marker:#x}, shim={len(data)}')
