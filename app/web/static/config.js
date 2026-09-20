async function apiGet(path) {
  const r = await fetch(path);
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || r.statusText);
  }
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || r.statusText);
  }
  return r.json();
}

async function apiDelete(path) {
  const r = await fetch(path, { method: 'DELETE' });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || r.statusText);
  }
  return r.json();
}

async function apiPut(path, body) {
  const r = await fetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || r.statusText);
  }
  return r.json();
}

async function loadPollGroupOptions(selectEl) {
  if (!selectEl) return;
  const groups = await apiGet('/api/config/poll-groups');
  selectEl.innerHTML = '';
  groups.forEach((g) => {
    const o = document.createElement('option');
    o.value = g.id;
    o.textContent = g.id + ' (' + g.interval_ms + ' ms)';
    selectEl.appendChild(o);
  });
}

function tagBodyFromForm(f) {
  return {
    name: f.name.value.trim(),
    device: f.device.value.trim(),
    function: parseInt(f.function.value, 10),
    address: parseInt(f.address.value, 10),
    register_count: parseInt(f.register_count.value, 10),
    datatype: f.datatype.value,
    gain: parseFloat(f.gain.value),
    offset: parseFloat(f.offset.value),
    engineering_unit: f.engineering_unit.value,
    poll_group: f.poll_group.value,
    enabled: f.enabled ? f.enabled.checked : true,
    writable: f.writable ? f.writable.checked : false,
  };
}

function showMsg(text, isError) {
  const el = document.getElementById('msg');
  if (!el) return;
  el.textContent = text;
  el.className = 'msg' + (isError ? ' error' : ' ok');
}

let _tagDefsCache = [];

function updateTagLiveCells(liveMap) {
  document.querySelectorAll('#tag-table tbody tr').forEach((tr) => {
    const name = tr.dataset.tagName;
    if (!name) return;
    const lv = liveMap[name] || {};
    const valCell = tr.querySelector('.live-value');
    const qCell = tr.querySelector('.live-quality');
    if (valCell) valCell.textContent = lv.value != null ? lv.value : '';
    if (qCell) qCell.textContent = lv.quality || '';
  });
}

async function loadDevices() {
  const table = document.querySelector('#dev-table tbody');
  if (!table) return;
  const devices = await apiGet('/api/config/modbus/devices');
  table.innerHTML = '';
  devices.forEach((d) => {
    const tr = document.createElement('tr');
    const hostPort = d.mode.includes('rtu')
      ? d.serial_port
      : d.host + ':' + d.port;
    tr.innerHTML =
      '<td>' + d.name + '</td><td>' + d.mode + '</td><td>' + hostPort +
      '</td><td>' + d.enabled + '</td>' +
      '<td><button type="button" data-edit="' + d.name + '">Edit</button> ' +
      '<button type="button" data-del="' + d.name + '">Delete</button></td>';
    table.appendChild(tr);
  });
  table.querySelectorAll('button[data-edit]').forEach((btn) => {
    btn.addEventListener('click', () => openDeviceEditor(btn.dataset.edit, devices));
  });
  table.querySelectorAll('button[data-del]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete device ' + btn.dataset.del + '?')) return;
      try {
        await apiDelete('/api/config/modbus/devices/' + encodeURIComponent(btn.dataset.del));
        showMsg('Device removed.');
        loadDevices();
      } catch (e) { showMsg(e.message, true); }
    });
  });
}

function openDeviceEditor(deviceName, devices) {
  const dlg = document.getElementById('dev-edit-dialog');
  const f = document.getElementById('dev-edit-form');
  if (!dlg || !f) return;
  const d = devices.find((x) => x.name === deviceName);
  if (!d) return;
  f.dataset.originalName = deviceName;
  f.name.value = d.name;
  f.mode.value = d.mode;
  f.host.value = d.host || '';
  f.port.value = d.port || 502;
  f.unit_id.value = d.unit_id || 1;
  f.serial_port.value = d.serial_port || 'COM3';
  f.address_base.value = d.address_base || 'one';
  if (f.enabled) f.enabled.checked = d.enabled !== false;
  dlg.showModal();
}

function deviceBodyFromForm(f) {
  return {
    name: f.name.value.trim(),
    mode: f.mode.value,
    host: f.host.value.trim(),
    port: parseInt(f.port.value, 10),
    unit_id: parseInt(f.unit_id.value, 10),
    serial_port: f.serial_port.value.trim(),
    address_base: f.address_base.value,
    enabled: f.enabled ? f.enabled.checked : true,
  };
}

async function loadDeviceNames(listId) {
  const list = document.getElementById(listId);
  if (!list) return;
  const devices = await apiGet('/api/config/modbus/devices');
  list.innerHTML = '';
  devices.forEach((d) => {
    const o = document.createElement('option');
    o.value = d.name;
    list.appendChild(o);
  });
}

async function loadTagDefinitions() {
  const table = document.querySelector('#tag-table tbody');
  if (!table) return;
  const defs = await apiGet('/api/config/tags/definitions');
  _tagDefsCache = defs;
  const live = await apiGet('/api/tags');
  const liveMap = liveTagMap(live);
  table.innerHTML = '';
  defs.forEach((t) => {
    const lv = liveMap[t.name] || {};
    const tr = document.createElement('tr');
    tr.dataset.tagName = t.name;
    tr.innerHTML =
      '<td>' + t.name + '</td><td>' + t.device + '</td><td>' + (t.address_display || t.address) +
      '</td><td>' + t.datatype + '</td><td class="live-value">' + (lv.value ?? '') +
      '</td><td class="live-quality">' + (lv.quality ?? '') + '</td>' +
      '<td><button type="button" data-edit="' + t.name + '">Edit</button> ' +
      '<button type="button" data-del="' + t.name + '">Delete</button></td>';
    table.appendChild(tr);
  });
  table.querySelectorAll('button[data-edit]').forEach((btn) => {
    btn.addEventListener('click', () => openTagEditor(btn.dataset.edit, _tagDefsCache));
  });
  table.querySelectorAll('button[data-del]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete tag ' + btn.dataset.del + '?')) return;
      try {
        await apiDelete('/api/config/tags/definitions/' + encodeURIComponent(btn.dataset.del));
        showMsg('Tag removed.');
        loadTagDefinitions();
      } catch (e) { showMsg(e.message, true); }
    });
  });
}

function refreshLiveTags() {
  if (document.getElementById('tags')) return;
  if (!document.querySelector('#tag-table')) return;
  if (typeof startLiveTags !== 'function') return;
  startLiveTags((live) => updateTagLiveCells(liveTagMap(live)));
}

function openTagEditor(tagName, defs) {
  const dlg = document.getElementById('tag-edit-dialog');
  const f = document.getElementById('tag-edit-form');
  if (!dlg || !f) return;
  const t = defs.find((x) => x.name === tagName);
  if (!t) return;
  f.dataset.originalName = tagName;
  f.name.value = t.name;
  f.device.value = t.device;
  f.function.value = String(t.function);
  f.address.value = t.address_display || t.address;
  f.register_count.value = t.register_count;
  f.datatype.value = t.datatype;
  f.gain.value = t.gain;
  f.offset.value = t.offset;
  f.engineering_unit.value = t.engineering_unit || '';
  loadPollGroupOptions(f.poll_group).then(() => {
    f.poll_group.value = t.poll_group || 'default';
  });
  if (f.enabled) f.enabled.checked = t.enabled !== false;
  if (f.writable) f.writable.checked = t.writable === true;
  dlg.showModal();
}
