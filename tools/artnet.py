"""Read ArtPollReply or send a short, explicit QA5X color test."""
import argparse
import json
import socket
import struct
import time

from tools.show_hardware import Lighting


def parse_reply(data):
    if len(data) < 194 or data[:10] != b'Art-Net\0\x00\x21':
        return None
    base = (data[18] & 127) << 8 | (data[19] & 15) << 4
    count = min(4, struct.unpack('>H', data[172:174])[0])
    return {'name': data[26:44].split(b'\0')[0].decode('ascii', errors='replace'),
            'ports': [{'port': n + 1, 'port_type': data[174 + n],
                       'output_universe': base | (data[190 + n] & 15)}
                      for n in range(count)]}


def discover(host, timeout=3):
    """ArtPoll reads configuration only; no DMX/output changes."""
    results = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', 6454))
        sock.settimeout(timeout)
        sock.sendto(b'Art-Net\0\x00\x20\x00\x0e\x00\x00', (host, 6454))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            sock.settimeout(max(.01, deadline - time.monotonic()))
            try:
                data, peer = sock.recvfrom(2048)
            except socket.timeout:
                break
            reply = parse_reply(data)
            if peer[0] == host and reply:
                results.append(reply)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.178.146')
    parser.add_argument('--color', choices=('red', 'green', 'blue', 'amber', 'black'))
    parser.add_argument('--universe', type=int)
    parser.add_argument('--address', type=int)
    parser.add_argument('--mode', type=int, choices=(4, 5, 7))
    args = parser.parse_args()
    if not args.color:
        results = discover(args.host)
        print(json.dumps(results, indent=2))
        if not results:
            raise SystemExit('Keine ArtPoll-Antwort vom Node erhalten.')
        return
    if args.universe is None or args.address is None or args.mode is None:
        parser.error('Color test requires --universe (zero-based), --address and --mode')
    if not 0 <= args.universe <= 32767 or not 1 <= args.address <= 513 - args.mode:
        parser.error('Invalid universe or DMX address')
    config = dict(host=args.host, universe=args.universe,
                  start_address=args.address, channel_mode=args.mode)
    lighting = Lighting(config)
    color = [0, 0, 0, 0]
    if args.color != 'black':
        color[('red', 'green', 'blue', 'amber').index(args.color)] = 100
    try:
        lighting.color(color)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            lighting.tick(time.monotonic())
            time.sleep(lighting.FRAME_PERIOD)
    finally:
        lighting.close()


if __name__ == '__main__':
    main()
