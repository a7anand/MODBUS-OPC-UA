# Manual acceptance — TEST 3 (Modbus RTU)

PDF §46 TEST 3: **Modbus RTU device → RS-485 → Gateway → OPC UA Server**

This cannot be fully automated in CI without serial hardware. Procedure:

1. Connect RS-485 USB adapter (e.g. COM3).
2. In `config/gateway.yaml` add RTU client device (`mode: rtu_client`, `serial_port`, baud/parity).
3. Map tags to holding/input registers on the slave.
4. Run `python -m app --run --config config\gateway.yaml`.
5. Verify `/api/tags` shows **GOOD** quality and OPC UA nodes update.
6. Disconnect cable → tags **BAD/STALE**, gateway and Web UI remain responsive (TEST 4 overlap).
7. Reconnect → quality restores, recovery event in `/api/events`.

Record results in `docs/WINDOWS_COMPATIBILITY.md` test log.
