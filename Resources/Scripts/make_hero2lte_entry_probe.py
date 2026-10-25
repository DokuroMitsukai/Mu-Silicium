#!/usr/bin/env python3
"""Replace a Samsung diagnostic kernel with a standalone display-entry probe."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

from repack_samsung_boot import FOOTER, image_id, unpack


def make_probe(template, probe):
    page, parts, end = unpack(template)
    kernel = parts[0]
    if (page != 2048 or not parts[3].startswith(b'DTBH') or
            template[end:end + len(FOOTER)] != FOOTER):
        raise ValueError('expected captured Samsung DTBH layout')
    if (kernel[56:60] != b'ARMd' or len(probe) < 64 or
            probe[56:60] != b'ARMd' or len(probe) > len(kernel)):
        raise ValueError('invalid ARM64 template or entry probe')
    replacement = bytearray(probe + bytes(len(kernel) - len(probe)))
    replacement[8:64] = kernel[8:64]
    parts[0] = bytes(replacement)
    result = bytearray(template)
    result[page:page + len(kernel)] = replacement
    result[576:608] = image_id(parts)
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / 'Platforms/Samsung/hero2ltePkg/EntryProbe.S'
    try:
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            obj, binary = Path(temporary) / 'probe.o', Path(temporary) / 'probe.bin'
            subprocess.run(['clang', '--target=aarch64-linux-gnu', '-c',
                            str(source), '-o', str(obj)], check=True)
            subprocess.run(['llvm-objcopy', '-O', 'binary', str(obj), str(binary)], check=True)
            result = make_probe(args.template.read_bytes(), binary.read_bytes())
        with args.output.open('xb') as stream:
            stream.write(result)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{hashlib.sha256(result).hexdigest()}  {args.output}')


if __name__ == '__main__':
    main()
