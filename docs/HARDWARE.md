# Hardware support

| Device | USB ID | Status |
| --- | --- | --- |
| Original NZXT Function MiniTKL | `1e71:2105` | Enabled; tested on physical hardware |
| Original Function TKL | `1e71:2104` | Upstream capture source; not enabled here |
| Other original Function variants | Other IDs | Not enabled |
| Function 2 / Function Elite | Different devices | Not supported |

Initial testing used Arch Linux and an active local logind seat. Other Linux
distributions need validation of their device permissions and user services.

Established on the MiniTKL:

- Dedicated vendor interface 1, report ID `0x43`.
- Static RGB, off, and reactive commands return expected acknowledgements.
- Register `0x44` follows physical FN+F1–F4 through indices 0–3.
- The service detects those changes and applies lighting only to F1 and F4.
- F2/F3 stock-style lighting restoration is verified by base/overlay readback.
- Reconnects are detected across changing USB paths and hidraw numbers.

Acknowledgements alone do not prove visual appearance. Reports from physical
keyboards should distinguish visible results from packet-level success.

Configuration is stored on Linux. Permanent onboard save/backup operations are
not implemented. Lighting changes affect the addressed live profile; stopping
the service does not undo an earlier change. The tool does not program mappings or macros, but native FN
selection can still load mappings/macros already stored in those profiles.

There is no firmware updater, audio-reactive mode, per-key editor, macro recorder
or typing-event listener. Animations run in the keyboard. The whole-keyboard
mask originates from the TKL capture; additional layouts need physical testing.
