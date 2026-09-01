"""
Sensor simulator: emits the Legacy Radar Unit's UDP wire format.

Frame layout (24 bytes total), per docs/customer-discovery.md:

    offset  size  field          encoding
    0       2     magic          fixed 0xFEED
    2       1     msg_type       fixed 1 (reading)
    3       4     device_id      uint32, big-endian
    7       8     timestamp_ms   uint64, big-endian
    15      4     range_m        float32, LITTLE-endian  <- the device's quirk
    19      4     bearing_deg    float32, big-endian
    23      1     checksum       xor of bytes 0-22

This is the tracer-bullet version: one hardcoded device emitting plausible
readings on a fixed interval. Fault injection (malformed/duplicate/
out-of-order/stale) is deliberately deferred to issue #9.
"""
import argparse
import random
import socket
import struct
import time

MAGIC = b"\xfe\xed"
MSG_TYPE_READING = 1
DEFAULT_DEVICE_ID = 2100  # LRU-2100


def build_frame(device_id: int, timestamp_ms: int, range_m: float, bearing_deg: float) -> bytes:
    header = MAGIC + struct.pack(">B", MSG_TYPE_READING)
    header += struct.pack(">I", device_id)
    header += struct.pack(">Q", timestamp_ms)
    # Quirk: range_m is little-endian while the rest of the frame is big-endian.
    body = struct.pack("<f", range_m)
    body += struct.pack(">f", bearing_deg)
    payload = header + body
    checksum = 0
    for b in payload:
        checksum ^= b
    return payload + struct.pack(">B", checksum)


def main():
    parser = argparse.ArgumentParser(description="Legacy Radar Unit (LRU-2100) UDP simulator")
    parser.add_argument("--host", default="127.0.0.1", help="adapter's UDP host")
    parser.add_argument("--port", type=int, default=5005, help="adapter's UDP port")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between readings")
    parser.add_argument("--device-id", type=int, default=DEFAULT_DEVICE_ID)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[sensor-sim] device {args.device_id} broadcasting to {args.host}:{args.port} "
          f"every {args.interval}s")

    bearing = 0.0
    try:
        while True:
            timestamp_ms = int(time.time() * 1000)
            range_m = round(random.uniform(50.0, 500.0), 1)
            bearing = (bearing + random.uniform(1.0, 5.0)) % 360.0
            frame = build_frame(args.device_id, timestamp_ms, range_m, bearing)
            sock.sendto(frame, (args.host, args.port))
            print(f"[sensor-sim] sent range={range_m}m bearing={bearing:.1f}deg")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[sensor-sim] stopped")


if __name__ == "__main__":
    main()
