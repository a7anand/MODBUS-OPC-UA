/** Shared live tag polling interval (ms) — keep at or below fastest poll group. */
const LIVE_TAG_POLL_MS = 750;

async function fetchLiveTags() {
  const r = await fetch('/api/tags');
  if (!r.ok) throw new Error('tags fetch failed');
  return r.json();
}

function liveTagMap(tags) {
  const m = {};
  tags.forEach((t) => { m[t.name] = t; });
  return m;
}

function startLiveTags(onUpdate) {
  const tick = () => {
    fetchLiveTags()
      .then(onUpdate)
      .catch(() => {});
  };
  tick();
  return setInterval(tick, LIVE_TAG_POLL_MS);
}
