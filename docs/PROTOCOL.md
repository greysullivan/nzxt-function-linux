# Protocol and evidence

Initial evidence comes from the annotated USBPcap files in
[OpenRGB issue 2395](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/2395),
captured on a Function TKL `1e71:2104`. Commands were then tested on an original
MiniTKL `1e71:2105`.

NZXT documents FN slots in the
[Function manual](https://cdn-g.nzxt.com/dl/1646904242-peripherals_keyboard_function-digital-manual_en_pdf_2109.pdf)
and reactive lighting in its
[lighting guide](https://support.nzxt.com/hc/en-us/articles/4414924658587-Changing-Lighting-Modes-for-the-Function-Keyboard).

Only sanitized lighting reports are included in `tests/fixtures/lighting.json`.
Original downloads and third-party source are excluded from Git. The driver is
written independently from observed commands and responses.

## Reports

Interface 1 has usage page `0xffca` and report ID `0x43`, with 63 payload bytes:
**64 bytes including the ID**. Device identity and the complete report descriptor
are checked before commands. Single-report packets are:

```
43 <0x80 | payload length> 00 <command and parameters> <zero padding>
```

The captured whole-keyboard mask is 18 bytes:

```
ff ff ff 5f ff ff ff 7f ff 6f 27 7e fb 67 fe 7f 00 08
```

| Operation | Command and parameters after the header |
| --- | --- |
| Solid | `30 P 01`, mask, RGB |
| Base readback | `31 P` |
| Base off | `32 P` |
| Ripple | `37 P 07`, mask, speed, `00 03 02`, RGB |
| Fade (research only) | `37 P 08`, mask, speed, `00 02`, RGB |
| Line (research only) | `37 P 09`, mask, speed, `00 03 02`, RGB |
| Reactive readback | `38 P` |
| Reactive off | `39 P` |

`P` is the zero-based target profile, 0–3. It must not be hardcoded to zero
when applying lighting to FN+F4. Readback commands `31` and `38` are getters,
not commands to clear the profile. A record begins with `01 P ...`; an empty
layer returns `02 P`.

The reactive capture uses white and speed 70 (`46`). This tool varies the RGB
fields and exposes speed 1–100. Other constant parameters are preserved from the
capture; their detailed semantics are not independently established.

A scene sends a base command followed by a reactive command. Static scenes
disable the reactive layer; off disables both layers.

## Responses and selected slot

First comes a matching echo prefixed `43 e5 00`. This is not success. Captured
writes then return `43 82 00 01 P ...`. The success result is the single byte
`01`; `P` retains the profile index and is not the high byte of an error code.
Trailing bytes are not interpreted. Missing or failed responses do not commit new
Linux settings. Reads return a length-prefixed data report after their echo.

CAM's startup capture reads `0x44` using:

```
43 81 00 44 00 ... (64 bytes)
```

On this MiniTKL, physical FN+F1–F4 returned `43 81 00 <index> ...` with indices
`00`, `01`, `02`, `03`. The watcher queries about twice per second and writes
lighting only when the slot, scene settings, theme colour or connection changes.
No host typing events are needed.

Automatic policy manages only F1 (solid) and F4 (fixed-colour ripple). It sends
no lighting writes to F2/F3. The explicit `restore-defaults` command reinstates
their captured stock-style wave and colour-shift base definitions and disables
their overlays, then verifies both readbacks. It is not a full profile restore.

The captured `0x40` register reports brightness. Other captured status registers
are available in the development inspector; they are not assumed to provide a
complete profile backup. No unknown profile-storage commands are sent.
