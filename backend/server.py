"""
Backend: gRPC ingest + WebSocket broadcast (tracer bullet).

Receives normalized SensorReadings from the adapter over gRPC, logs them, and
broadcasts the latest reading to any connected WebSocket clients (the operator
UI). `/health` and structured JSON logging land in issue #6.
"""
import asyncio
import json
import pathlib
import sys
import threading
from concurrent import futures

import grpc
import websockets

GENERATED = pathlib.Path(__file__).resolve().parent.parent / "proto" / "generated"
sys.path.insert(0, str(GENERATED))
import sensor_pb2  # noqa: E402
import sensor_pb2_grpc  # noqa: E402

WS_CLIENTS: set = set()


def reading_to_json(reading: sensor_pb2.SensorReading) -> str:
    return json.dumps(
        {
            "device_id": reading.device_id,
            "timestamp_ms": reading.timestamp_ms,
            "range_m": reading.range_m,
            "bearing_deg": reading.bearing_deg,
        }
    )


async def broadcast(payload: str):
    if not WS_CLIENTS:
        return
    await asyncio.gather(*(client.send(payload) for client in WS_CLIENTS), return_exceptions=True)


class SensorServicer(sensor_pb2_grpc.SensorServiceServicer):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._count = 0

    def StreamReadings(self, request_iterator, context):
        for reading in request_iterator:
            self._count += 1
            print(
                f"[backend] received #{self._count} device={reading.device_id} "
                f"range={reading.range_m:.1f}m bearing={reading.bearing_deg:.1f}deg"
            )
            payload = reading_to_json(reading)
            asyncio.run_coroutine_threadsafe(broadcast(payload), self._loop)
        return sensor_pb2.StreamAck(received_count=self._count)


async def ws_handler(websocket):
    WS_CLIENTS.add(websocket)
    print(f"[backend] operator UI connected ({len(WS_CLIENTS)} total)")
    try:
        await websocket.wait_closed()
    finally:
        WS_CLIENTS.discard(websocket)
        print(f"[backend] operator UI disconnected ({len(WS_CLIENTS)} total)")


def serve_grpc(loop: asyncio.AbstractEventLoop, port: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    sensor_pb2_grpc.add_SensorServiceServicer_to_server(SensorServicer(loop), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"[backend] gRPC server listening on 0.0.0.0:{port}")
    server.wait_for_termination()


async def main():
    loop = asyncio.get_running_loop()
    grpc_thread = threading.Thread(target=serve_grpc, args=(loop, 50051), daemon=True)
    grpc_thread.start()

    async with websockets.serve(ws_handler, "0.0.0.0", 8080):
        print("[backend] WebSocket server listening on 0.0.0.0:8080")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
