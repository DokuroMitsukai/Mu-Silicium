#!/usr/bin/env python3
"""Wrap a legacy UEFI boot image in a captured Samsung DTBH boot layout."""
import argparse
import hashlib
from pathlib import Path
import struct

FOOTER = b'SEANDROIDENFORCE'


def align(size, page):
    return (size + page - 1) // page * page


def image_id(parts):
    digest = hashlib.sha1()
    for part in parts:
        digest.update(part)
        digest.update(struct.pack('<I', len(part)))
    return digest.digest() + bytes(12)


def unpack(data):
    if len(data) < 1632 or data[:8] != b'ANDROID!':
        raise ValueError('not a legacy Android boot image')
    fields = struct.unpack_from('<10I', data, 8)
    page = fields[7]
    if page not in (2048, 4096, 8192, 16384):
        raise ValueError('unsupported page size')
    if len(data) < page:
        raise ValueError('truncated header page')
    sizes = (fields[0], fields[2], fields[4], fields[8])
    parts, offset = [], page
    for size in sizes:
        end = offset + align(size, page)
        if end > len(data):
            raise ValueError('truncated payload')
        parts.append(data[offset:offset + size])
        offset = end
    hashed = parts if sizes[3] else parts[:3]
    if data[576:608] != image_id(hashed):
        raise ValueError('boot image ID mismatch')
    return page, parts, offset


def repack(stock, uefi):
    page, parts, end = unpack(stock)
    _, replacement, _ = unpack(uefi)
    if not parts[3].startswith(b'DTBH') or stock[end:end + len(FOOTER)] != FOOTER:
        raise ValueError('stock image needs DTBH and an aligned Samsung footer')
    if replacement[2] or replacement[3] or not replacement[0] or not replacement[1]:
        raise ValueError('replacement must contain only kernel and ramdisk')
    parts[:2] = replacement[:2]
    header = bytearray(stock[:page])
    struct.pack_into('<I', header, 8, len(parts[0]))
    struct.pack_into('<I', header, 16, len(parts[1]))
    header[576:608] = image_id(parts)
    output = bytes(header)
    for part in parts:
        output += part + bytes(align(len(part), page) - len(part))
    if len(output) > end:
        raise ValueError('replacement overlaps the captured stock trailer')
    output += FOOTER
    # Partition dumps can retain an older image tail. Do not interpret or move it.
    result = bytearray(len(stock))
    result[end:] = stock[end:]
    result[:len(output)] = output
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--uefi', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.stock.resolve(), args.uefi.resolve()):
        parser.error('output must not overwrite either input')
    try:
        result = repack(args.stock.read_bytes(), args.uefi.read_bytes())
        with args.output.open('xb') as stream:
            stream.write(result)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{hashlib.sha256(result).hexdigest()}  {args.output}')


if __name__ == '__main__':
    main()
