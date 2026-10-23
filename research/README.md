# Development evidence

Capture links: https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/2395

Local downloads, snapshots and logs are ignored by Git. Public fixtures contain
selected lighting reports only. `captures.py` extracts interrupt reports from
the upstream little-endian USBPcap files.

`inspect_profiles.py snapshot` queries addresses present in captured startup
traffic. `inspect_profiles.py monitor 120` observes register `0x44` for up to two
minutes. It opens only the vendor lighting endpoint and sends no profile-storage
commands. These are development tools; use `keys` for ordinary lighting control.
