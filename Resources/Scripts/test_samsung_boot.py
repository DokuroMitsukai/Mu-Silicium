#!/usr/bin/env python3
"""Exercise Samsung repacking without private device captures."""
import struct
import unittest

from repack_samsung_boot import FOOTER, align, image_id, repack, unpack


def fixture(parts, samsung=True, page=2048):
    header = bytearray(page)
    header[:8] = b'ANDROID!'
    struct.pack_into('<10I', header, 8, len(parts[0]), 0x10008000,
                     len(parts[1]), 0x11000000, len(parts[2]), 0x10F00000,
                     0x10000100, page, len(parts[3]), 0x14000165)
    header[64:80] = b'stock board name'
    header[608:624] = b'stock extra args'
    header[576:608] = image_id(parts if parts[3] else parts[:3])
    data = bytes(header)
    for part in parts:
        data += part + bytes(align(len(part), page) - len(part))
    return data + (FOOTER + bytes(8192) if samsung else b'')


class SamsungBootTest(unittest.TestCase):
    def setUp(self):
        self.parts = [b'linux' * 1500, b'initrd', b'second', b'DTBH' + bytes(512)]
        self.stock = fixture(self.parts)
        self.uefi = fixture([b'firmware', b'dummy', b'', b''], False)

    def test_repack(self):
        result = repack(self.stock, self.uefi)
        page, parts, end = unpack(result)
        self.assertEqual(len(result), len(self.stock))
        self.assertEqual(parts, [b'firmware', b'dummy', *self.parts[2:]])
        self.assertEqual(result[end:end + len(FOOTER)], FOOTER)
        before, after = bytearray(self.stock[:page]), bytearray(result[:page])
        for offset, length in ((8, 4), (16, 4), (576, 32)):
            before[offset:offset + length] = bytes(length)
            after[offset:offset + length] = bytes(length)
        self.assertEqual(before, after)
        self.assertEqual(result, repack(self.stock, self.uefi))

    def test_reject_corruption(self):
        broken = bytearray(self.stock)
        broken[2048] ^= 1
        with self.assertRaisesRegex(ValueError, 'ID mismatch'):
            repack(broken, self.uefi)

    def test_reject_missing_footer(self):
        _, _, end = unpack(self.stock)
        with self.assertRaisesRegex(ValueError, 'footer'):
            repack(self.stock[:end], self.uefi)

    def test_preserve_unknown_trailer(self):
        stock = self.stock[:-1] + b'x'
        _, _, end = unpack(stock)
        result = repack(stock, self.uefi)
        self.assertEqual(result[end:], stock[end:])

    def test_reject_oversize(self):
        large = fixture([b'x' * len(self.stock), b'dummy', b'', b''], False)
        with self.assertRaisesRegex(ValueError, 'stock trailer'):
            repack(self.stock, large)

    def test_reject_truncation(self):
        for length in (0, 64, 1632, 2048, 4096):
            with self.subTest(length=length), self.assertRaises(ValueError):
                repack(self.stock[:length], self.uefi)


if __name__ == '__main__':
    unittest.main()
