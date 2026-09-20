# Desktop GUI (PyQt5)



Two desktop clients talk to Gateway Core over HTTP only (no pymodbus/asyncua in the GUI process).



| Version | Command | Package |

|---------|---------|---------|

| **v3 (default)** | `python -m app --gui` | `app/gui/` — PDF completion (in progress) |

| **v2 (frozen)** | `python -m app --gui-v2` | `app/gui_v2/` — [VERSION2_FREEZE.md](VERSION2_FREEZE.md) |

| **v1 (legacy)** | `python -m app --gui-v1` | `app/gui_v1/` — simple list navigation |



Design specification for v2: [GUI_V2_DESIGN_SPEC.md](GUI_V2_DESIGN_SPEC.md)



## Install and run



```bat

pip install -e ".[gui]"

python -m app --gui --config config\gateway.yaml

```



Legacy UI:



```bat

python -m app --gui-v1 --config config\gateway.yaml

```



The GUI starts the gateway (Modbus, OPC UA, REST/Web) in a **background thread**, then connects to `http://127.0.0.1:8080` (or your `web.host` / `web.port` from YAML).



## v2 navigation (summary)



- **Dashboard** — KPI tiles, device health, events, comm stats

- **Configuration** — wizard, gateway, Modbus devices, OPC UA, web server

- **Tags** — high-performance tag manager (model/view), mapping editor, import/export

- **Diagnostics** — Modbus analyzer, register viewer, OPC UA browser, communication trace

- **Events & alarms**, **Backup & versioning**, **Certificates**, **Users**, **System**



Themes: toolbar **Theme** cycles Dark → Light → System engineering palettes.



## vs browser UI



- Trend/history **charts** remain on the web UI (`/trends`, `/history`).

- Open `http://127.0.0.1:8080` alongside the desktop app when you need charts.



## Architecture



- `app/gui_shared/api_client.py` — REST helper (shared by v1 and v2)

- `app/gui/theme.py` — centralized QSS theme manager

- `app/gui/main_window.py` — v2 shell (sidebar, toolbar, status bar)

- `app/gui/pages/` — v2 screens

- `app/gui_v1/` — frozen v1 pages



See [COMPLETE_SYSTEM_REFERENCE.md](COMPLETE_SYSTEM_REFERENCE.md) for API details.


