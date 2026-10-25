#!/usr/bin/env python3
"""Check the standalone entry probe and container isolation."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from make_hero2lte_entry_probe import make_probe
from repack_samsung_boot import unpack
from test_samsung_boot import fixture


class EntryProbeTest(unittest.TestCase):
    def test_probe(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(dir=root) as directory:
            obj, binary = Path(directory) / 'probe.o', Path(directory) / 'probe.bin'
            subprocess.run(['clang', '--target=aarch64-linux-gnu', '-c',
                            str(root / 'Platforms/Samsung/hero2ltePkg/EntryProbe.S'),
                            '-o', str(obj)], check=True)
            subprocess.run(['llvm-objcopy', '-O', 'binary', str(obj), str(binary)], check=True)
            probe = binary.read_bytes()
            dis = subprocess.check_output(['llvm-objdump', '-d', str(obj)], text=True)
        self.assertEqual(struct.unpack_from('<I', probe)[0], 0x14000010)
        self.assertEqual(probe[56:60], b'ARMd')
        self.assertNotIn('bl\t', dis)
        self.assertNotIn('[sp', dis)
        self.assertIn('#0xe2a00000', dis)
        self.assertIn(struct.pack('<Q', 0x13960070), probe)
        kernel = bytearray(4096)
        kernel[56:60] = b'ARMd'
        struct.pack_into('<QQ', kernel, 8, 0xC9000000, len(kernel))
        template = fixture([bytes(kernel), b'dummy', b'', b'DTBH' + bytes(256)])
        result = make_probe(template, probe)
        _, parts, _ = unpack(result)
        self.assertEqual(len(result), len(template))
        self.assertEqual(parts[0][8:64], kernel[8:64])
        self.assertEqual(result[2048 + len(kernel):], template[2048 + len(kernel):])
        self.assertEqual(result[:576], template[:576])
        self.assertEqual(result[608:2048], template[608:2048])
        self.assertEqual(parts[1:], unpack(template)[1][1:])

    def test_reject_bad_probe(self):
        template = fixture([bytes(4096), b'dummy', b'', b'DTBH'])
        with self.assertRaises(ValueError):
            make_probe(template, b'invalid')


if __name__ == '__main__':
    unittest.main()
