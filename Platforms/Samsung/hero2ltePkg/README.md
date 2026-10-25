# hero2lte Phase 1 diagnostics

The first standalone image stopped at the Samsung splash. Stock BOOT was
restored and Android boots again. The splash does not establish that BootShim
ran. Saved pmsg contains Android messages; saved compressed dmesg does not
inflate successfully.

## Host checks

From the firmware repository:

```sh
python3 Resources/Scripts/test_bootshim.py
python3 Resources/Scripts/test_samsung_boot.py
python3 Resources/Scripts/test_hero2lte_keypad.py
```

## Controlled image variants

Keep the failed image unchanged. First repackage that exact image to isolate
Samsung container compatibility. From the project root:

```sh
python3 src/Mu-Silicium/Resources/Scripts/repack_samsung_boot.py \
  --stock flash/boot-stock.img --uefi flash/boot-uefi.img \
  --output out/boot-uefi-samsung-packaging.img
```

The tool verifies both legacy image IDs, preserves the stock header except
kernel/ramdisk sizes and image ID, retains second-stage/DTBH bytes, and adds
the Samsung footer at the new payload end. The captured tail, including
nonzero residual data and another footer, stays at its original absolute
offset. Replacements may not overlap that tail. Output size equals the
captured partition size. Existing output files and input files are not
overwritten. No private capture belongs in this repository.

For a separate instrumented variant:

```sh
./build-hero2lte.sh --boot-diagnostics
python3 src/Mu-Silicium/Resources/Scripts/test_hero2lte_build.py --diagnostics
python3 src/Mu-Silicium/Resources/Scripts/repack_samsung_boot.py \
  --stock flash/boot-stock.img --uefi src/Mu-Silicium/Mu-hero2lte.img \
  --output out/boot-uefi-samsung-diagnostic.img
```

This option is off by default. It uses four 32-line bands at the top of the
captured 1440-wide, 32-bpp framebuffer (0xE2A00000):

| Band | Stage reached |
| --- | --- |
| Red, lines 0-31 | BootShim, before writing the relocated FD |
| Green, lines 32-63 | FD copy finished, or payload already at FD base |
| Blue, lines 64-95 | SEC assembly entry, before stack initialization |
| Yellow, lines 96-127 | DXE dispatch, before CPU/GIC/timer drivers |

Writes are cleaned to the point of coherency and followed by a barrier.
No GPIO, storage or DECON control registers are changed by these markers.
Film the display during any approved test; later drawing can overwrite them.
Colors assume BGRA. Scanout address, stride and refresh remain unvalidated:
**no visible bands is inconclusive**, not proof of S-Boot rejection.

The instrumented build changes both shim size and firmware contents. Do not
attribute a different result solely to packaging unless the unchanged-kernel
variant was tested separately. Preserving DTBH/footer does not establish
signature acceptance, and DTBH is not consumed by UEFI itself.

## Still unresolved

- The heap overlaps DT `video_frame` and `video_scaler`; FD and stack overlap
  `video_scaler`. These regions are secure/reusable in the captured DT. That
  is not proof they are accessible at S-Boot handoff. No speculative relocation
  has been made.
- BootShim inherits S-Boot's MMU/cache/exception-level state. A green marker
  proves the copy loop returned, not that instruction fetch or RAM ownership
  is correct.
- Architectural-timer PPIs and display refresh are not hardware validated.
- RELEASE has no framebuffer serial logging. DEBUG has more logging, but also
  clears the framebuffer during SEC and is a separate experiment.

Neither build nor repack flashes anything. Keep TWRP on RECOVERY, verified
EFS/CPEFS and stock BOOT backups, and require explicit approval for each flash
or reboot. Do not wipe or repartition for these tests.
