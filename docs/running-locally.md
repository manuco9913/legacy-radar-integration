# Running the tracer-bullet pipeline locally

No Docker yet (that's issue #8) — this is the manual, three-terminal way to see the
pipeline work end-to-end.

## 1. Install dependencies

```bash
pip install -r backend/requirements.txt -r adapter/requirements.txt -r requirements-dev.txt
```

## 2. Generate the gRPC stubs (only needed after editing proto/sensor.proto)

```bash
python proto/generate_stubs.py
```

## 3. Start each piece, in order, each in its own terminal

```bash
python backend/server.py       # gRPC :50051, WebSocket :8080
python adapter/adapter.py      # UDP :5005 -> backend gRPC
python sensor-sim/sim.py       # emits a reading every second
```

## 4. Watch it live

Open `frontend/index.html` directly in a browser (no server needed — it connects to
`ws://localhost:8080`). The range/bearing should update once per second and the status
should read "connected".
