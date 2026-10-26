# hero2lte bring-up

Status: UEFI runs on SM-G935F hardware (bootloader `G935FXXS6ESI4`, hardware
revision 9). The Project Silicium logo and "no bootable OS" screen appear.
That screen is expected: this build has no storage driver or XNU payload yet.

Earlier standalone and diagnostic images stopped at the Samsung splash. The
standalone entry probe then showed a white band, isolating entry and refresh.
Enabling the same refresh from the instrumented BootShim stages made the full
firmware visible. Stock Android has been restored before those tests.

## Host checks

From the firmware repository:

```sh
python3 Resources/Scripts/test_bootshim.py
python3 Resources/Scripts/test_samsung_boot.py
python3 Resources/Scripts/test_hero2lte_keypad.py
python3 Resources/Scripts/test_hero2lte_entry_probe.py
```

After a build, `test_hero2lte_build.py [--diagnostics] [--bringup-test]`
checks the image, shim size, forwarded flags and SEC/DXE content.

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

Writes are cleaned to the point of coherency and followed by a barrier. Every
marker also requests a DECON refresh using the trigger handling that the
standalone entry probe validated on hardware. Markers are diagnostic only;
refresh itself is now enabled unconditionally by SEC (see below).

Film the display during any approved test; later drawing can overwrite the
bands. Colors assume BGRA. Scanout address and stride match S-Boot's captured
configuration, but are not independently varied: **no visible bands is
inconclusive**.

The instrumented build changes both shim size and firmware contents. Do not
attribute a different result solely to packaging unless the unchanged-kernel
variant was tested separately. Preserving DTBH/footer does not establish
signature acceptance, and DTBH is not consumed by UEFI itself.

For the timer/keypad probe, with no bands:

```sh
./build-hero2lte.sh --bringup-test
python3 src/Mu-Silicium/Resources/Scripts/test_hero2lte_build.py --bringup-test
python3 src/Mu-Silicium/Resources/Scripts/repack_samsung_boot.py \
  --stock flash/boot-stock.img --uefi src/Mu-Silicium/Mu-hero2lte.img \
  --output out/boot-uefi-samsung-bringup.img
```

The default build already uses the new memory layout; repack it as
`out/boot-uefi-samsung-safemem.img` and test that before the probe. The probe
consumes no storage and leaves BDS input handling registered.

## Hardware result

The flashed image `out/boot-uefi-samsung-refresh.img` reached the full UEFI
UI: Project Silicium logo and the "failed to find an operating system" screen.
That is the expected end state because there is no storage driver or XNU
payload in this build.

This validates the preserved Samsung container, BootShim execution, SEC
initialization, DXE dispatch and enough of GICv2/timer/keypad/SimpleFbDxe for
BDS.

The non-diagnostic image `boot-uefi-samsung-plain.img` then produced the same
logo and missing-OS screen. Display refresh therefore no longer depends on
the diagnostic build.

The safemem image reached the same UEFI UI, validating FD/stack/heap relocation
to `0xB1200000`-`0xBFF40000`. The bring-up image then showed the top-left block
alternating magenta/cyan once per second, accepted volume, home and power keys,
and incremented the white counter. The phone was manually rebooted to TWRP
afterward; no probe-triggered reset was observed.

## Display refresh

`PlatformAssemblyInitialize` in `S5E8890Pkg/PlatformSecLib` now performs the
trigger update unconditionally, before the stack or HOBs exist. If HW trigger
enable (bit 4) is set it clears HW mask bit 5; otherwise it sets SW trigger bit
8. Other bits are preserved. Hardware-observed behavior shows the HW path is
active after unmasking, so continuous TE refresh is restored without a
per-frame hook.

Only `0x13960070` is touched. S-Boot's panel, clock and DECON configuration is
otherwise left alone. If a future handoff leaves DECON in SW-trigger mode, a
single refresh would be requested and a per-frame hook would then be required.

## Cache coherency

BootShim derives the data cache line size from `CTR_EL0`, cleans the
relocated FD to the point of coherency, executes `DSB`, invalidates the
instruction cache, then executes `DSB`/`ISB` before branching. The clean loop
stops after the line containing the last FD byte, so it works for any FD size
and does not touch a line after the image. The first version hard-coded
64-byte lines, skipped the middle barrier and could clean one line past the
image; all three are corrected.

SEC already invalidated the FD range, but only after entry, and invalidation
discards dirty lines rather than writing them back.

## Standalone entry/refresh probe

The packaging-only and four-band images both remained on the Samsung splash;
no bands were observed. Partition readback matched the diagnostic image exactly.

The standalone probe removes FD relocation and UEFI from the experiment:

```sh
python3 src/Mu-Silicium/Resources/Scripts/test_hero2lte_entry_probe.py
python3 src/Mu-Silicium/Resources/Scripts/make_hero2lte_entry_probe.py \
  --template out/boot-uefi-samsung-diagnostic.img \
  --output out/boot-hero2lte-entry-refresh.img
```

It replaces only the kernel bytes and Android image ID. Kernel length, ARM64
header fields at offsets 8-63, ramdisk, DTBH and the complete trailer remain
unchanged. There is no UEFI payload. It draws a white 128-line top band and
repeatedly requests refresh without a stack, timer or interrupts.

**Result on hardware:** the white band appeared. This proves S-Boot entered
the probe's instructions and that the framebuffer plus the trigger method can
produce visible output. It did not, by itself, prove BootShim or UEFI ran.

This probe modifies DECON trigger control at `0x13960070`: it clears HW
trigger mask bit 5 when HW enable bit 4 is set, otherwise sets SW trigger bit
8. Other bits are preserved. These operations are corroborated by the captured
device's S-Boot trigger routine and the Exynos 8890 kernel register
definitions; they are not the old guessed 8895 trigger value. It does not
configure clocks, panel, GPIO or storage.

For the probe alone, no band would have been inconclusive: access permissions,
cache operations or an earlier bootloader stage could prevent observation. A
watchdog reset is possible because the probe intentionally does not boot an OS.

## Memory layout

The original dreamlte-derived layout put the heap over DT `video_frame` and
`video_scaler`, and the FD/stack inside `video_scaler`. Those nodes are
`secure` and `reusable`, so they are not a safe long-term home.

The new layout uses the unreserved gap:

| Region | Address | Size |
| --- | --- | --- |
| UEFI FD | `0xB1200000` | 2 MiB |
| UEFI stack | `0xB1400000` | 256 KiB |
| DXE heap | `0xB1440000` | 235 MiB, ending `0xBFF40000` |

Evidence:

- `memory@80000000` covers `0x80000000`-`0xFE400000`; the only reserved node in
  the gap is TIMA at `0xB1000000`-`0xB1200000`.
- S-Boot is linked at `0x02000000` (its literals reference addresses inside a
  4 MiB image at that base).
- S-Boot derives the kernel entry from `0x80000000 + (rand & 0x3f) * 0x4000 +
  0x80000`, i.e. `0x80080000`-`0x81040000`, and loads the ramdisk at
  `0x89000000`.
- The ION pools start at `0xC0000000`; the heap leaves a 768 KiB guard below
  them.

This removes the UEFI overlap in source, pending hardware validation. It does
not by itself define the XNU memory map: high RAM at `0x880000000`, the DT
reserved pools and the handoff contract still need validation before XNU uses
them.

## Bring-up probe

`--bringup-test` adds `BringupTestDxe`. It is a visible hardware test, not
production UI:

- a 120 px block at (20,20) alternates magenta/cyan every second, proving timer
  ticks and repeated framebuffer refresh;
- a 720 px bar at (20,180) turns red for volume up, green for volume down, blue
  for home, white for power and yellow for other keys;
- white blocks at (20,340) count accepted key notifies.

The driver registers a UEFI timer event and a `SimpleTextInEx` key notify, so
it leaves BDS input handling intact. It draws directly into the S-Boot
framebuffer and does not initialize storage, clocks or panel.

## Remaining firmware issues

- **UEFI timer, keypad and display are validated; XNU entry is next.** The
  safemem and bring-up probes passed on hardware. GICv2 support in ArmCpu,
  the XNU handoff, storage and power management remain.
- **Keypad mux/pull state is still inherited from S-Boot.** GPIO ALIVE
  `0x10580000` matches the DT `pinctrl@10580000`; mappings match `gpio_keys`
  (GPA0[3] volume up, GPA0[4] volume down, GPA0[5] home, GPA2[4] power). The
  probe confirms the pins are usable at handoff, not that a cold-boot driver
  would configure them correctly.
- **Timer events are validated at 200 ms.** Longer-running behavior and
  interrupt latency under load remain unmeasured.
- **No storage driver.** UFS is mapped in the memory map but not initialized,
  so no bootable OS can be found.
- `UNIXNU_PAYLOAD` is now forwarded (`--unixnu`), but this tree does not
  contain `UniXNUPkg` or `DarwinBootPkg`. Enabling the flag will fail until
  those packages are integrated.
- The firmware volume uses about `0x6a100` of `0x200000` bytes. The remaining
  space is sufficient for the small UniXNU loader set.
- RELEASE has no framebuffer serial logging. DEBUG has more logging, but also
  clears the framebuffer during SEC and is a separate experiment.

Neither build nor repack flashes anything. Keep TWRP on RECOVERY, verified
EFS/CPEFS and stock BOOT backups, and require explicit approval for each flash
or reboot. Do not wipe or repartition for these tests.
