#!/usr/bin/env python3
"""Check BootShim layout with and without its ARM64 header."""
from pathlib import Path
import struct
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(dir=root) as directory:
    directory = Path(directory)
    for header, base, size, marker in ((1, 0xB1200000, 0x200000, 0),
                                       (1, 0xB1323000, 0x210000, 0),
                                       (0, 0xB1200000, 0x200000, 0),
                                       (1, 0xB1200000, 0x200000, 0xE2A00000)):
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
        assert disassembly.count('dc\tcvac') == (3 if marker else 1)
        assert disassembly.count('ic\tiallu') == 1
        assert 'CTR_EL0' in disassembly, 'cache line size is hard-coded'
        assert 'add\tx6, x6, x7' in disassembly, 'cache stride is not from CTR_EL0'
        lines = [line for line in disassembly.splitlines() if '\t' in line]
        dc = max(i for i, line in enumerate(lines) if 'dc\tcvac' in line)
        dsb1 = next(i for i in range(dc, len(lines)) if 'dsb\tsy' in lines[i])
        ic = next(i for i in range(dsb1, len(lines)) if 'ic\tiallu' in lines[i])
        dsb2 = next(i for i in range(ic + 1, len(lines)) if 'dsb\tsy' in lines[i])
        isb = next(i for i in range(dsb2 + 1, len(lines)) if 'isb' in lines[i])
        br = next(i for i in range(isb + 1, len(lines)) if 'br\tx5' in lines[i])
        assert dc < dsb1 < ic < dsb2 < isb < br, (
            f'bad sync order: dc={dc} dsb={dsb1} ic={ic} dsb={dsb2} '
            f'isb={isb} br={br}')
        if marker:
            assert struct.pack('<Q', marker + 184320) in data
            assert struct.pack('<Q', 0x13960070) in data
            assert disassembly.count('stp\tx9, x9') == 2
            assert disassembly.count('dsb\tsy') >= 5
        print(f'PASS: header={header}, base={base:#x}, size={size:#x}, marker={marker:#x}, shim={len(data)}')

    # Mirror the assembly loop: clean at the base, then step by the cache
    # line until the line containing the last byte has been cleaned.  This
    # checks coverage and termination for unaligned sizes without executing
    # AArch64 code.
    def check_stride(base, size, line):
        last = base + size - 1
        addresses = []
        address = base
        while True:
            addresses.append(address)
            address += line
            if address > last:
                break
        assert addresses[0] == base
        assert all(b - a == line for a, b in zip(addresses, addresses[1:]))
        assert addresses[-1] <= last < addresses[-1] + line

    for line in (16, 32, 64, 128, 2048):
        for size in (1, 63, 64, 65, 0x200000):
            check_stride(0xB1200000, size, line)
    print('PASS: cache stride covers the FD for 16-2048 byte lines')
