# Web UI — End-user guide

This guide explains how to operate the Modbus ↔ OPC UA Gateway from the browser (default `http://127.0.0.1:8080`).

## Start the gateway

1. Install dependencies: `pip install -e ".[dev]"` (includes Excel import and file upload support).
2. Run: `python -m app --run --config config\gateway.yaml`
3. Open the URL shown in the console (usually `http://127.0.0.1:8080`).

The web UI reads live data from the **Gateway Core**; it does not talk to Modbus or OPC UA directly.

---

## Navigation

| Page | Purpose |
|------|---------|
| **Dashboard** | Live tag values, quality, mini trend sparklines, recent events |
| **Devices** | Add or remove Modbus devices (TCP/RTU/simulator) |
| **Tags** | Add, **edit**, or delete tag definitions |
| **Import** | Bulk import tags from CSV or Excel |
| **Polling** | Configure how often each **poll group** scans its tags |
| **Trends** | Full line chart for one tag (refreshes ~750 ms) |
| **History** | Tabular last **5 minutes** per tag (time, value, raw registers + byte order) |
| **Traffic** | Modbus request/response PDU shown as **hex** |
| **Events** | Gateway event log |
| **Diagnostics** | Communication monitor with device **and tag name** |

---

## Add a Modbus device

1. Go to **Devices**.
2. Fill in name, mode (e.g. `tcp_client`), host, port, timeouts.
3. Leave **Enable Modbus polling** checked to connect and poll tags on this device; uncheck to disable I/O without deleting the device.
4. Click **Add device**.

Use **Edit** on an existing row to change connection settings or turn polling on/off.

The configuration is saved to your YAML file (with backup). The gateway reloads Modbus connections automatically. If the PLC is offline, the device may show disconnected until it is reachable.

---

## Add or edit a tag

### Add

1. Go to **Tags**.
2. Choose the **device**, Modbus function, PLC-style address (e.g. `40001`), datatype, scaling (gain/offset), and **poll group**.
3. Click **Add tag**.

### Edit

1. On **Tags**, click **Edit** on a row.
2. Change fields in the dialog (you can rename the tag if the new name is unique).
3. Click **Save**.

Changes are written to YAML and the runtime reloads polling and OPC UA mapping.

---

## Import tags from CSV or Excel

1. Go to **Import**.
2. Download the template from the link on that page (`tags_import_template.csv`).
3. **Upload** the file or **paste** CSV text, then **Preview**.
4. Fix any errors listed, optionally check **Update existing tags with same name**, then **Commit import**.

For `.xlsx` files, `openpyxl` must be installed (`pip install openpyxl`).

---

## Polling period

Tags do not each have their own timer. They belong to a **poll group** (`default`, `fast`, or a custom group you create).

1. Go to **Polling**.
2. Set **Interval (ms)** for a group (minimum 50 ms) and click **Save**.
3. When adding/editing tags, assign the tag to the desired poll group.

Example: `fast` = 500 ms, `default` = 1000 ms, `slow` = 5000 ms.

---

## Dashboard and trends

- **Dashboard** updates over WebSocket when `websockets` is installed; otherwise it polls REST every 2 seconds.
- Numeric tags show a small **sparkline** when values are updating.
- **Trends** page shows a larger chart for the selected tag (last few hundred samples in memory only — not a historian).

If the dashboard stayed on “Connecting” in older builds, refresh after upgrade; the page now loads `app.js` and fetches data immediately.

---

## Modbus traffic (hex)

1. Open **Traffic** (or **Diagnostics** for a summary table).
2. Each poll shows **Tx** and **Rx** PDU bytes in hex (unit ID, function, data). This is a logical PDU view, not the full TCP MBAP header.
3. Use **Clear buffer** on the Traffic page to empty the capture.

---

## Diagnostics

Shows recent polls with **device**, **tag name**, address, result, and response time. Refreshes every 2 seconds.

Manual read test: use OpenAPI (`/docs`) → `POST /api/modbus/read`.

---

## Security

If `security.require_auth` is enabled in YAML, write operations require a login token (`POST /api/auth/login`) and `Authorization: Bearer …` header. Default dev configs are often open on localhost.

---

## Where configuration is stored

Browser changes update the YAML path you started the gateway with (e.g. `config/gateway.yaml`). Backups and audit entries are kept under `data/` and the backup store. See `docs/CONFIGURATION.md` for YAML reference.

---

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Tag value empty / BAD quality | Device connected? Address, function, datatype correct? |
| New tag not on dashboard | Wait one poll cycle; confirm tag **enabled** and device exists |
| Import fails | Column headers match template; device names exist |
| No WebSocket | `pip install websockets`; REST fallback still works |
| Excel import 501 | `pip install openpyxl` |

For deeper issues see `docs/TROUBLESHOOTING.md`.
