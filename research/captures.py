#!/usr/bin/python3
"""Read USBPcap interrupt data from the upstream issue's little-endian pcapngs.

No dependencies; these captures are small. Each yield is (endpoint, payload).
"""
import struct
from pathlib import Path


def packets(path):
    data = Path(path).read_bytes()
    if data[:4] != bytes.fromhex('0a0d0d0a') or data[8:12] != bytes.fromhex('4d3c2b1a'):
        raise ValueError('Expected little-endian pcapng')
    position = 0
    interfaces = []
    while position < len(data):
        kind, size = struct.unpack_from('<II', data, position)
        if size < 12 or size % 4 or position + size > len(data):
            raise ValueError('Invalid pcapng block')
        if struct.unpack_from('<I', data, position + size - 4)[0] != size:
            raise ValueError('Invalid pcapng trailer')
        body = data[position + 8:position + size - 4]
        if kind == 1:
            interfaces.append(struct.unpack_from('<H', body)[0])
        elif kind == 6:
            interface, _, _, captured, _ = struct.unpack_from('<5I', body)
            if interfaces[interface] != 249:
                raise ValueError('Expected USBPcap link type')
            packet = body[20:20 + captured]
            if len(packet) >= 27:
                header, _, _, _, _, _, _, endpoint, transfer, length = struct.unpack_from('<HQIHBHHBBI', packet)
                if transfer == 1 and length:
                    yield endpoint, packet[header:header + length]
        position += size


if __name__ == '__main__':
    import sys
    for name in sys.argv[1:]:
        print(name)
        for endpoint, payload in packets(name):
            print(f'{endpoint:02x}', payload.hex(' '))
