# NZXT Function lighting on Linux

Terminal lighting control for the original **NZXT Function MiniTKL**: named
colours, arbitrary RGB values, reactive effects, and scenes selected with the
real **FN+F1–F4** keys. No CAM or OpenRGB required.

The keyboard runs the animation. Python reads the selected preset slot and
applies its scene; it does not listen to typing or render every frame.

**LLM-assisted development:** substantial parts of the implementation, protocol
analysis, tests and documentation were generated or revised with **OpenAI
Codex**. The keyboard owner provided hardware testing and feedback. See
[the development disclosure](AI_ASSISTANCE.md) for scope and limitations.

**Tested device:** original MiniTKL, USB **`1e71:2105`**, on Arch Linux.
Other Function models, Function 2 and Elite are not enabled.

## Install

Requires Linux, Python **3.10+**, udev with systemd-logind, and an active local
login. The background service uses systemd's user session. No pip packages.

```sh
git clone https://github.com/greysullivan/nzxt-function-linux.git
cd nzxt-function-linux
sudo sh ./install-device-access
sh ./install-user
```

The first script installs a device access rule; sudo is needed only for that
step. The second installs commands in `~/.local/bin` and enables the user
service. Ensure `~/.local/bin` is in your shell's `PATH`:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Keep that line in your shell configuration if needed. Reconnect the keyboard
if the access rule has not taken effect.

## Colours

```sh
keys-purple
keys-pink
keys colours
keys '#336699'
keys-off
keys status
```

`keys purple` and `keys-purple` are equivalent. Hex values accept an optional
`#`; quote it in the shell. `off`, `black` and `000000` disable all lighting.

Named colours now use vivid RGB values, including full-intensity red, green,
and blue. **Rose keeps its original soft `#DFA0A0`.** White is full-intensity
`#FFFFFF`. The keyboard's brightness setting still controls perceived brightness;
actual shades depend on its LEDs.

Run `keys colours` (also `keys colors` or `keys list`) to list the palette without
changing the keyboard. Each name works as `keys NAME` and `keys-NAME`, including
hyphenated names such as `keys-sky-blue`.

| Name | RGB hex | Name | RGB hex |
| --- | --- | --- | --- |
| red | `#FF0000` | crimson | `#DC143C` |
| orange | `#FF8000` | amber | `#FFBF00` |
| gold | `#FFD700` | yellow | `#FFFF00` |
| lime | `#80FF00` | chartreuse | `#BFFF00` |
| green | `#00FF00` | emerald | `#00C040` |
| teal | `#008080` | turquoise | `#00FFBF` |
| cyan | `#00FFFF` | sky-blue | `#00BFFF` |
| azure | `#0080FF` | blue | `#0000FF` |
| royal-blue | `#4000FF` | navy | `#000080` |
| indigo | `#6000FF` | purple | `#8000FF` |
| violet | `#BF00FF` | magenta | `#FF00FF` |
| hot-pink | `#FF1493` | pink | `#FF0080` |
| rose | `#DFA0A0` | white | `#FFFFFF` |

For other shades, supply any six-digit RGB hex value, from `000000` to `ffffff`
(16,777,216 possible values; the LEDs may not visibly distinguish them all).
`keys effect NAME` accepts the same palette for F4's reactive colour.

Updating does not recolour an existing saved selection. Run a named command
again, such as `keys blue`, to apply its new vivid value. Theme following still
uses the palette file's exact accent and foreground values.

Colour commands configure the base for F1 and F4. F2/F3 stay unmanaged; commands
run there save settings for the next managed slot without changing their
lighting. The keyboard's current brightness level is preserved.

## F1 and F4, one palette

```sh
keys purple
keys effect auto
keys slots on
```

| Physical shortcut | Scene | Appearance |
| --- | --- | --- |
| **FN+F1** | Still | Solid base colour |
| **FN+F2** | Onboard preset | Existing rainbow/wave effect; left unchanged |
| **FN+F3** | Onboard preset | Existing colour-changing effect; left unchanged |
| **FN+F4** | Impact | Fixed-colour ripples over the F1 base |

F1 and F4 share a base. F4's automatic effect uses the theme's own foreground
colour, staying within the palette. Fixed bases use neutral white, or charcoal
when the base is white. No complementary hue or rainbow cycling is added to
F4. An explicit manual effect colour overrides the automatic choice.

```sh
keys effect cyan
keys effect '#FFD080'
keys speed 50
keys effect auto
```

Speed is 1–100, default 45. `keys effect black` requests a black reactive colour;
`keys off` disables both layers on a managed slot. F2/F3 remain unchanged.

Manual selection is also available:

```sh
# Select FN+F4 on the keyboard first:
keys scene impact
# Select FN+F1 first to apply Still manually:
keys-still
keys slots on
```

Manual scene commands require the matching physical slot and stop automatic
FN following. `keys slots on` resumes it. F1 stays solid and F4 uses Impact;
automatic following never writes lighting to F2/F3. Allow about half a second
after an FN switch. The original effect can appear briefly before the managed
scene is applied.

**These are Linux-managed scenes, not permanent onboard profile saves.** FN
following needs a running watcher. Other computers without this tool use the
keyboard's original profiles. No mapping, macro or profile-storage commands are
sent.

If earlier experiments changed the live F2/F3 lighting, restore the captured
stock-style rainbow wave and colour-shift patterns explicitly:

```sh
keys restore-defaults
```

This restores and verifies only F2/F3 lighting. It is not a backup recovery of
user-customized profiles or a whole-keyboard factory reset. F1/F4, mappings and
macros are untouched by that operation.

## Optional desktop-theme following

For a theme generator that writes a JSON `accent` colour:

```sh
keys theme /path/to/palette.json
```

The file needs six hex digits:

```json
{"accent": "#9B68C7"}
```

`keys theme` alone uses `~/.config/air-theme/palette.json`, respecting
`XDG_CONFIG_HOME`. The watcher follows changes while retaining the scene,
speed and reactive-colour preference. Automatic reactive colour follows the
palette foreground. `keys-blue` returns to an independent fixed base.

Other theme tools can provide the same small JSON file. X11, Wayland and input
event libraries are not required by this tool.

## Persistence and service

Successful settings are saved under `~/.local/state/keyboard-rgb`, respecting
`XDG_STATE_HOME`. They restore on login and reconnect. No colour is chosen by
the installer before your first command. Failed commands preserve the saved
selection.

```sh
keys --help
systemctl --user status keyboard-rgb.service
journalctl --user -u keyboard-rgb.service -n 20 --no-pager
systemctl --user disable --now keyboard-rgb.service
systemctl --user enable --now keyboard-rgb.service
```

Use `sh ./install-user --no-service` to install without starting the watcher.
Run `keys --watch` in a terminal instead if desired. One-shot commands work
without a watcher; automatic FN, theme and reconnect following do not.

For updates, pull the repository and rerun `sh ./install-user`. Existing
static-only settings migrate with their fixed colour and FN following disabled.

## Help and development

- [Linux troubleshooting and removal](docs/LINUX.md)
- [Hardware support](docs/HARDWARE.md)
- [Protocol and evidence](docs/PROTOCOL.md)
- [Contributing](CONTRIBUTING.md)
- [LLM assistance disclosure](AI_ASSISTANCE.md)
- [Potential OpenRGB contribution](docs/OPENRGB.md)

```sh
python3 -m unittest -v test_keys
```

Tests use sanitized reports and mocked hardware. They do not change lighting.
MIT licensed. This independent project is not affiliated with NZXT.
