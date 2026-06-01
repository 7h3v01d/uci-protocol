"""
UCI Transport Abstraction Layer  —  uci/transport/
===================================================
This package contains UCI transport implementations.

v0.1.0-alpha status
-------------------
The local (in-process) transport is used by the test rig.
HTTP transport is the next planned implementation.

Planned transports
------------------
  local.py     — In-process transport (v0.1, used by test rig)
  http.py      — HTTP/HTTPS transport (planned v0.2)
  websocket.py — WebSocket transport (planned)
  ipc.py       — Named pipe / Unix socket transport (planned)
  grpc.py      — gRPC transport (planned)

Transport contract
------------------
All transports must preserve UCI semantics. A transport:
  - carries UCI messages between nodes
  - MUST NOT redefine governance semantics
  - MUST NOT redefine trust semantics
  - MUST preserve correlation identifiers
  - MUST preserve canonical response structure

See docs/uci_transport_model_v0_1.md for the full specification.
"""
