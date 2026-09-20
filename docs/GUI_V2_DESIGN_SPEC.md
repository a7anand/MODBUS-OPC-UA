# GUI v2 — Industrial Engineering Workstation Design Specification

**Product line:** Modbus ↔ OPC UA Gateway  
**GUI v1:** `app/gui_v1/` — list navigation, functional CRUD (`--gui-v1`)  
**GUI v2:** `app/gui/` — SCADA-style workstation (`--gui`, default)

---

## 1. Wireframe (logical layout)

```
+------------------------------------------------------------------+
| [≡] Gateway Name                    [Toolbar: context actions]   |
+----------+-------------------------------------------------------+
| NAV      | Breadcrumb: Diagnostics > Communication Monitor       |
| (tree)   +-------------------------------------------------------+
|          |                                                       |
| DASHBOARD|              Main workspace (QStackedWidget)          |
| CONFIG ▼ |                                                       |
| TAGS ▼   |                                                       |
| DIAG ▼   |                                                       |
| EVENTS   |                                                       |
| ...      |                                                       |
|          +-------------------------------------------------------+
|          | [Optional QDock: trace detail / live values]          |
+----------+-------------------------------------------------------+
| Status: Gateway RUNNING | Modbus 5/6 | OPC UA OK | Tags 1248/7   |
+------------------------------------------------------------------+
```

---

## 2. Navigation structure

| Group | Screen ID | Title |
|-------|-----------|-------|
| — | `dashboard` | Dashboard |
| Configuration | `cfg_gateway` | Gateway |
| Configuration | `cfg_modbus` | Modbus Devices |
| Configuration | `cfg_opcua` | OPC UA |
| Configuration | `cfg_web` | Web Server |
| Tags | `tags_manager` | Tag Manager |
| Tags | `tags_mapping` | Mapping |
| Tags | `tags_import` | Import / Export |
| Diagnostics | `diag_modbus` | Modbus Diagnostic Tool |
| Diagnostics | `diag_registers` | Register Viewer |
| Diagnostics | `diag_opcua` | OPC UA Browser |
| Diagnostics | `diag_comm` | Communication Monitor |
| — | `events` | Events & Alarms |
| — | `backup` | Backup & Versioning |
| — | `simulators` | Simulators |
| — | `certificates` | Certificates |
| — | `users` | Users & Security |
| — | `system` | System Diagnostics |
| — | `cfg_wizard` | Configuration Wizard |

---

## 3. Screen hierarchy

```
MainWindow
├── EngineeringSidebar (QTreeWidget)
├── ContextToolBar (QToolBar)
├── BreadcrumbBar (QLabel)
├── WorkspaceStack (QStackedWidget)
│   ├── DashboardPage
│   ├── Config* pages
│   ├── TagManagerPage (QTableView + models)
│   ├── MappingEditorPage
│   ├── ModbusDiagnosticPage
│   ├── OpcUaBrowserPage
│   ├── CommunicationMonitorPage
│   └── …
├── DetailDock (QDockWidget, optional)
└── EngineeringStatusBar (QStatusBar)
```

---

## 4. Component library (`app/gui/widgets/`)

| Component | Purpose |
|-----------|---------|
| `KpiTile` | Compact KPI with icon + label + value + semantic state |
| `SectionHeader` | Uppercase section title with separator |
| `StatusBadge` | Icon + text + color (not color-only) |
| `EngineeringTableView` | Styled QTableView defaults |
| `SearchField` | Filter-as-you-type line edit |
| `PrimaryButton` / `SecondaryButton` | Button hierarchy via theme |

---

## 5. Theme specification (`app/gui/theme.py`)

| Token | Dark | Light |
|-------|------|-------|
| Background | `#1a1d21` | `#eef0f2` |
| Panel | `#23272e` | `#ffffff` |
| Border | `#3a3f47` | `#c8ccd0` |
| Text | `#e8eaed` | `#1a1d21` |
| Muted | `#9aa0a6` | `#5f6368` |
| Accent | `#4a9eff` | `#1565c0` |
| Good | `#3dba6c` | `#1e7e34` |
| Bad | `#e55353` | `#c62828` |
| Warning | `#e6a23c` | `#ef6c00` |

Themes: **Dark Engineering**, **Light Engineering**, **System** (follows OS).

---

## 6. Dashboard layout

Row 1: KPI tiles (Gateway, Uptime, Devices, Connected, Tags, Good/Bad/Uncertain, Comm errors).  
Row 2: `QSplitter` — Device health table | Tag quality summary.  
Row 3: Recent events | Communication stats.  
Row 4: System resources (when API available) | Recent errors | Active connections.

---

## 7. Tag Manager layout

Toolbar: Search, column filter, Add, Edit, Delete, Import, Export, Enable/Disable.  
Main: `QTableView` + `TagTableModel` + `QSortFilterProxyModel`.  
Frozen first column (tag name) via duplicate header view pattern.  
Context menu: copy, paste, bulk enable, open mapping.

Columns: Name, Description, Device, Protocol, Address, Data Type, Raw, Engineering, Unit, Quality, Timestamp, OPC UA Node, Direction, Poll Interval, Enabled.

Updates: merge live `/api/tags` into model by name — patch rows only.

---

## 8. Mapping Editor layout

Vertical pipeline diagram (SOURCE → Conversion → Scaling → Quality → DESTINATION).  
Side panel: validation messages, byte/word order, live test read/write.

---

## 9. Modbus Diagnostic layout

`QSplitter` horizontal: Connection (left) | Request builder + Response inspector (right).  
Response tabs: Raw HEX, Decoded, Registers, Bits, ASCII, Timing, Exception.

---

## 10. OPC UA Browser layout

Left: address space tree. Right: node attributes. Bottom: subscription monitor table.

---

## 11. Communication Monitor layout

Trace table (model/view) + filter bar + pause/resume/clear/export.  
Detail dock on double-click: full TX/RX hex.

---

## Implementation notes

- All I/O via `app/gui_shared/api_client.py` (REST only).
- Long operations use `ApiWorker` (`QThread`) — UI never blocks on Modbus/OPC UA.
- Gateway core starts in a daemon thread (same as v1).
