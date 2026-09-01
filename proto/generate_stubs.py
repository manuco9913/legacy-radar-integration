"""Regenerate Python gRPC stubs from sensor.proto into proto/generated/.

Run from anywhere: `python proto/generate_stubs.py`
Requires: grpcio-tools (dev-only dependency, see requirements-dev.txt).
"""
import pathlib
import sys

from grpc_tools import protoc

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
OUT_DIR = PROTO_DIR / "generated"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    args = [
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        str(PROTO_DIR / "sensor.proto"),
    ]
    exit_code = protoc.main(args)
    if exit_code != 0:
        sys.exit(exit_code)
    print(f"[proto] generated stubs in {OUT_DIR}")


if __name__ == "__main__":
    main()
