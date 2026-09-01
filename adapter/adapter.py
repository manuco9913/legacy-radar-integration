"""
Adapter: raw UDP -> gRPC bridge (tracer bullet).

Listens for the Legacy Radar Unit's UDP broadcast, parses each frame per the
wire format in docs/customer-discovery.md, and forwards it to the backend as
a SensorReading over one long-lived gRPC client-streaming call.

Deliberately thin for this issue: parsing only, no duplicate/out-of-order/
stale detection (issue #4) and no reconnect/backoff (issue #5) yet.
"""
import argparse
import pathlib
import socket
import struct
import sys

import grpc

GENERATED = pathlib.Path(__file__).resolve().parent.parent / "proto" / "generated"
sys.path.insert(0, str(GENERATED))
import sensor_pb2  # noqa: E402
import sensor_pb2_grpc  # noqa: E402

MAGIC = b"\xfe\xed"
MSG_TYPE_READING = 1
FRAME_LEN = 24  # magic(2) + type(1) + device_id(4) + timestamp(8) + range(4) + bearing(4) + checksum(1)


def parse_frame(raw: bytes) -> sensor_pb2.SensorReading:
    """Raw parse only. Malformed/duplicate/out-of-order/stale handling lands in #4."""
    if len(raw) != FRAME_LEN or raw[:2] != MAGIC:
        raise ValueError(f"unrecognized frame ({len(raw)} bytes)")
    msg_type = raw[2]
    if msg_type != MSG_TYPE_READING:
        raise ValueError(f"unsupported msg_type {msg_type}")
    device_id = struct.unpack(">I", raw[3:7])[0]
    timestamp_ms = struct.unpack(">Q", raw[7:15])[0]
    # Quirk: range_m is little-endian while the rest of the frame is big-endian.
    range_m = struct.unpack("<f", raw[15:19])[0]
    bearing_deg = struct.unpack(">f", raw[19:23])[0]
    return sensor_pb2.SensorReading(
        device_id=device_id,
        timestamp_ms=timestamp_ms,
        range_m=range_m,
        bearing_deg=bearing_deg,
    )


def udp_readings(udp_host: str, udp_port: int):
    """Generator yielding parsed SensorReadings as UDP frames arrive."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_host, udp_port))
    print(f"[adapter] listening for radar UDP frames on {udp_host}:{udp_port}")
    while True:
        raw, addr = sock.recvfrom(4096)
        try:
            reading = parse_frame(raw)
        except ValueError as exc:
            print(f"[adapter] dropping unparseable frame from {addr}: {exc}")
            continue
        yield reading


def main():
    parser = argparse.ArgumentParser(description="Legacy radar UDP-to-gRPC adapter")
    parser.add_argument("--udp-host", default="0.0.0.0")
    parser.add_argument("--udp-port", type=int, default=5005)
    parser.add_argument("--backend", default="localhost:50051")
    args = parser.parse_args()

    channel = grpc.insecure_channel(args.backend)
    stub = sensor_pb2_grpc.SensorServiceStub(channel)

    def logged_readings():
        for reading in udp_readings(args.udp_host, args.udp_port):
            print(
                f"[adapter] forwarding reading device={reading.device_id} "
                f"range={reading.range_m:.1f}m bearing={reading.bearing_deg:.1f}deg"
            )
            yield reading

    ack = stub.StreamReadings(logged_readings())
    print(f"[adapter] stream closed, backend acked {ack.received_count} readings")


if __name__ == "__main__":
    main()
