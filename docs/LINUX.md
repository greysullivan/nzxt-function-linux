# Linux setup and troubleshooting

## Model and permissions

```sh
lsusb -d 1e71:2105
sudo sh ./install-device-access
```

Only the original MiniTKL `1e71:2105` is enabled. Similar names do not establish
protocol compatibility.

The installer creates `/etc/udev/rules.d/70-nzxt-function-keys.rules`, reloads
udev, and reapplies it to attached MiniTKLs. USB interface 1 receives an active
local user's logind `uaccess` grant. The typing interface retains its previous
permissions. `/dev/nzxt-function-lighting` points to the lighting device.

```sh
ls -l /dev/nzxt-function-lighting
getfacl /dev/nzxt-function-lighting
keys status
```

If there is no read/write ACL for your user, check the active local login and
reconnect the keyboard. SSH-only or inactive logins do not automatically receive
a grant. HID devices are not made world-writable, and no root daemon is needed.
Hidraw numbers may change after reconnecting; discovery handles this.

## Missing commands or scenes

Add `~/.local/bin` to `PATH` and reopen the terminal. Zsh may need `rehash`.
The shortcuts are executable symlinks, so shell aliases are not necessary.

If FN scenes do not follow:

```sh
keys slots on
systemctl --user is-active keyboard-rgb.service
journalctl --user -u keyboard-rgb.service -n 20 --no-pager
```

Manual scene selection stops following FN slots. Re-enable it with
`keys slots on`. F1 stays solid, F4 receives the palette-limited impact effect,
and F2/F3 remain unmanaged. Allow about half a second after a switch. With no
watcher, FN shortcuts use whatever is currently configured onboard.

Stopping the watcher does not undo live lighting settings already sent to a
profile. `keys restore-defaults` explicitly restores captured stock-style F2
rainbow wave and F3 colour shift, disables their reactive overlays, and checks
the readbacks. It does not touch F1/F4 or restore user-customized profile backups.

## Theme and I/O errors

`keys status` shows whether the base is fixed or follows a file. The palette
must contain an `accent` string with six hex digits. An unreadable or malformed
palette causes a logged error; the watcher retries when the file becomes valid.

Close other applications controlling the keyboard's RGB if acknowledgements
fail. Concurrent clients can mix responses. New settings are saved only after
both lighting commands succeed. A failed foreground change attempts to restore
the previous scene; disconnects are retried by the watcher.

For a corrupted state file, stop the service, move `state.json` out of
`~/.local/state/keyboard-rgb`, choose a colour again, then restart the service.

## Removal

```sh
systemctl --user disable --now keyboard-rgb.service
```

Remove the user `keyboard-rgb.service` unit, `~/.local/bin/keys`, and this
project's colour/scene symlinks. Keep unrelated commands. Then run
`systemctl --user daemon-reload`. Saved settings can be kept or removed
separately.

To remove device access:

```sh
sudo rm /etc/udev/rules.d/70-nzxt-function-keys.rules
sudo udevadm control --reload-rules
```

Reconnect the keyboard to clear the previous grant. Removal does not erase
the original onboard profiles.
