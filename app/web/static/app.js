(function () {
  const statusEl = document.getElementById("status");
  const tagsBody = document.querySelector("#tags tbody");
  const eventsEl = document.getElementById("events");
  const sparkCharts = {};

  if (!statusEl || !tagsBody) return;

  function render(data) {
    const uptime = data.status && data.status.health ? data.status.health.uptime_sec : 0;
    statusEl.textContent = "Running — " + Math.round(uptime) + "s uptime";
    const trends = data.trends || {};
    tagsBody.innerHTML = "";
    (data.tags || []).forEach(function (t) {
      const tr = document.createElement("tr");
      const canvasId = "spark-" + t.name.replace(/[^a-zA-Z0-9]/g, "_");
      tr.innerHTML =
        "<td>" + t.name + "</td><td>" + (t.device || "") + "</td><td>" +
        (t.value != null ? t.value : "—") + "</td><td>" + t.quality + "</td>" +
        '<td><canvas id="' + canvasId + '" width="120" height="40"></canvas></td>';
      tagsBody.appendChild(tr);
      drawSpark(canvasId, trends[t.name] || []);
    });
    if (eventsEl) {
      eventsEl.innerHTML = "";
      (data.events || []).forEach(function (e) {
        const li = document.createElement("li");
        li.textContent = e.severity + ": " + e.message;
        eventsEl.appendChild(li);
      });
    }
  }

  function drawSpark(canvasId, points) {
    if (!window.Chart || !points.length) return;
    const el = document.getElementById(canvasId);
    if (!el) return;
    if (sparkCharts[canvasId]) {
      sparkCharts[canvasId].destroy();
    }
    sparkCharts[canvasId] = new Chart(el, {
      type: "line",
      data: {
        labels: points.map(function () { return ""; }),
        datasets: [{
          data: points.map(function (p) { return p.v; }),
          borderColor: "#8ab4f8",
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
        }],
      },
      options: {
        animation: false,
        responsive: false,
        plugins: { legend: { display: false } },
        scales: { x: { display: false }, y: { display: false } },
      },
    });
  }

  function pollRest() {
    return Promise.all([
      fetch("/api/status").then(function (r) { return r.json(); }),
      fetch("/api/tags").then(function (r) { return r.json(); }),
      fetch("/api/events").then(function (r) { return r.json(); }),
      fetch("/api/trends").then(function (r) { return r.json(); }),
    ])
      .then(function (parts) {
        render({
          status: parts[0],
          tags: parts[1],
          events: parts[2],
          trends: parts[3],
        });
      })
      .catch(function () {
        statusEl.textContent = "REST poll failed — is the gateway running?";
      });
  }

  function startPolling() {
    statusEl.textContent = "Live updates via REST (install websockets package for WebSocket)";
    pollRest();
    setInterval(pollRest, 2000);
  }

  pollRest();

  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  let ws;
  try {
    ws = new WebSocket(proto + "//" + location.host + "/ws");
  } catch (err) {
    startPolling();
    return;
  }

  ws.onopen = function () {
    statusEl.textContent = "WebSocket connected";
    pollRest();
  };
  ws.onmessage = function (ev) {
    render(JSON.parse(ev.data));
  };
  ws.onerror = function () {
    ws.close();
  };
  ws.onclose = function () {
    if (!ws._usedPolling) {
      ws._usedPolling = true;
      startPolling();
    }
  };
})();
