#!/usr/bin/python3
"""Read capture-backed status registers and observe only the vendor HID endpoint.

No storage or profile-selection commands are sent. No keyboard input endpoint
is opened. Run with 'snapshot' or 'monitor SECONDS'.
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import select
import sys
import time

loader = importlib.machinery.SourceFileLoader('keys_driver', str(Path(__file__).resolve().parents[1] / 'keys'))
spec = importlib.util.spec_from_loader(loader.name, loader)
keys = importlib.util.module_from_spec(spec)
loader.exec_module(keys)


def query(fd, address):
    report = bytes([0x43, 0x81, 0, address]).ljust(64, b'\0')
    os.write(fd, report)
    end = time.monotonic() + 1.5
    while time.monotonic() < end:
        if not select.select([fd], [], [], max(0, end - time.monotonic()))[0]:
            break
        data = os.read(fd, 64)
        if len(data) == 64 and data[0] == 0x43 and data[1] != 0xe5:
            size = data[1] & 0x7f
            return data[3:3 + size].hex()
    raise RuntimeError(f'No reply for {address:02x}')


def main():
    duration = 0 if sys.argv[1:] == ['snapshot'] else int(sys.argv[2]) if len(sys.argv) == 3 and sys.argv[1] == 'monitor' else -1
    if not 0 <= duration <= 120:
        raise SystemExit('Usage: inspect_profiles.py snapshot | monitor SECONDS (1..120)')
    path, _ = keys.discover()
    fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
    try:
        keys.validate_fd(fd)
        registers = [0x44] if duration else [0x40, 0x44, 0x48, 0x86]
        previous = None
        start = time.monotonic()
        while True:
            with keys.locked():
                result = {f'{reg:02x}': query(fd, reg) for reg in registers}
            if result != previous:
                print(json.dumps({'elapsed': round(time.monotonic()-start, 2), 'registers': result}), flush=True)
                previous = result
            if time.monotonic() - start >= duration:
                break
            time.sleep(.25)
    finally:
        os.close(fd)


if __name__ == '__main__':
    main()
