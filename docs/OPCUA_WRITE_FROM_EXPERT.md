# Writing tags from OPC UA Expert

## Why writes were denied (`BadUserAccessDenied`)

UA Expert log:

`Write to node 'NS2|String|SIm2/coil2' failed [ret = BadUserAccessDenied]`

The gateway marks each tag with **`writable: false`** by default. The OPC UA server calls `set_writable(False)`, which clears the **CurrentWrite** access level. The server then correctly rejects client writes before they reach Modbus.

This is **not** an OPC UA security/login issue (anonymous access is fine with `SecurityPolicy=None`).

## How to enable writes

1. **Edit the tag** in `config/gateway.yaml` or **Tags → Edit** in the web UI.
2. Set **`writable: true`** (checkbox: *Writable from OPC UA*).
3. Use a **writable Modbus area**:
   - **Coils** (function 1) — e.g. address `00001`
   - **Holding registers** (function 3) — e.g. `40001`
   - **Not** input registers (function 4) or discrete inputs (function 2) — Modbus read-only.
4. **Restart or save** so config reloads (web save triggers reload automatically).
5. In UA Expert, write again (use correct type: Boolean for coils, number for registers).

## What the gateway does on a successful write

1. UA Expert sends OPC UA **Write** to the variable.
2. Server accepts (writable + access level).
3. Gateway **`write_tag`** → encode value → **Modbus write** to the PLC.
4. Tag database and OPC UA node update; next poll confirms value.

If Modbus write fails, check **Events** on the web UI or gateway log for a warning.

## YAML example (coil)

```yaml
- name: coil2
  device: SIm2
  function: 1
  address: 1
  datatype: bool
  writable: true
  poll_group: default
```

## Reads still work

`writable: false` tags are **read-only** in OPC UA (poll from Modbus → OPC UA). That is the normal mode for monitoring.
