// Assets - things that aren't characters, painted in the same colour roles, so
// they recolour the same way. Each saved item is one asset with its own colours,
// so a copy per player can sit above whoever's turn it is.

const STORE_KEY = 'pixel-creator.assets';
const STAGE_SCALE = 12;
const SHEET_SCALE = 3;
const OVER_SCALE = 8;
const OVER_GAP = 2;        // rows between the asset's tip and the top of a head
const CHARACTER_CELL = 32;
const OVER_SIZE = { w: 48, h: 64 };

const el = (id) => document.getElementById(id);
const data = window.ASSETS;

if (!data) {
  el('missing').hidden = false;
} else {
  boot();
}

function boot() {
  el('app').hidden = false;

  const { roles, groups, assets } = data;
  const baseColors = Object.fromEntries(roles.map((r) => [r.id, r.hex]));
  const defaultRgb = Object.fromEntries(roles.map((r) => [r.char, toRgb(r.hex)]));
  const rolesOf = (groupId) => roles.filter((r) => r.group === groupId);
  const assetById = (id) => assets.find((a) => a.id === id) || assets[0];
  const newId = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 8));

  let store = loadStore();
  let item = store.items.find((i) => i.id === store.current);
  let frame = 0;
  let playing = true;
  let timer = null;

  function fresh(assetId = assets[0].id) {
    return { id: newId(), name: assetById(assetId).label, asset: assetId, hue: {}, colors: { ...baseColors } };
  }

  /* ---------- saved items ---------- */

  function normalize(raw) {
    if (!raw || typeof raw !== 'object' || typeof raw.colors !== 'object' || !raw.colors) return null;
    const next = fresh(assetById(raw.asset).id);
    if (typeof raw.id === 'string') next.id = raw.id;
    if (typeof raw.name === 'string') next.name = raw.name;
    roles.forEach((r) => {
      const hex = raw.colors[r.id];
      if (typeof hex === 'string' && /^#[0-9a-f]{6}$/i.test(hex)) next.colors[r.id] = hex.toLowerCase();
    });
    groups.forEach((g) => {
      const deg = raw.hue && Number(raw.hue[g.id]);
      if (Number.isFinite(deg)) next.hue[g.id] = deg;
    });
    return next;
  }

  function loadStore() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
      if (raw && Array.isArray(raw.items)) {
        const items = raw.items.map(normalize).filter(Boolean);
        if (items.length) return { current: items.some((i) => i.id === raw.current) ? raw.current : items[0].id, items };
      }
    } catch { /* unreadable or blocked: start fresh */ }
    const first = fresh();
    return { current: first.id, items: [first] };
  }

  function persist() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ version: 1, current: item.id, items: store.items }));
    } catch {
      el('note').textContent = 'Could not save: the browser storage is full or blocked.';
    }
  }

  function refreshItems() {
    const select = el('instanceSelect');
    select.textContent = '';
    store.items.forEach((i) => {
      const option = document.createElement('option');
      option.value = i.id;
      option.textContent = i.name || 'Untitled';
      select.appendChild(option);
    });
    select.value = item.id;
    el('deleteItem').disabled = store.items.length < 2;
  }

  function switchTo(next) {
    item = next;
    store.current = next.id;
    changed();
  }

  el('instanceSelect').addEventListener('change', (event) => switchTo(store.items.find((i) => i.id === event.target.value)));

  el('dupItem').addEventListener('click', () => {
    const copy = JSON.parse(JSON.stringify(item));
    copy.id = newId();
    copy.name = `${item.name} copy`;
    store.items.splice(store.items.indexOf(item) + 1, 0, copy);
    switchTo(copy);
    el('note').textContent = `Copied to "${copy.name}". Its colours are its own now.`;
  });

  el('newItem').addEventListener('click', () => {
    const next = fresh(item.asset);
    store.items.push(next);
    switchTo(next);
  });

  el('deleteItem').addEventListener('click', () => {
    if (store.items.length < 2 || !window.confirm(`Delete "${item.name}"?`)) return;
    const at = store.items.indexOf(item);
    store.items.splice(at, 1);
    switchTo(store.items[Math.min(at, store.items.length - 1)]);
  });

  el('itemName').addEventListener('input', (event) => {
    item.name = event.target.value;
    el('instanceSelect').selectedOptions[0].textContent = item.name || 'Untitled';
    persist();
  });

  window.addEventListener('storage', (event) => {
    if (event.key !== STORE_KEY) return;
    store = loadStore();
    item = store.items.find((i) => i.id === store.current);
    syncControls();
    render();
  });

  /* ---------- colour ---------- */

  function rgbOf(source) {
    const map = {};
    roles.forEach((r) => { map[r.char] = toRgb(source.colors[r.id]); });
    return map;
  }

  function setGroupHue(groupId, degrees) {
    item.hue[groupId] = degrees;
    rolesOf(groupId).forEach((r) => {
      item.colors[r.id] = shiftHue(baseColors[r.id], degrees);
    });
  }

  /* ---------- rendering ---------- */

  // One frame of an asset as pixels, in the given colours.
  function frameImage(ctx, asset, index, rgb) {
    const image = ctx.createImageData(asset.w, asset.h);
    asset.frames[index].forEach((line, y) => {
      for (let x = 0; x < asset.w; x++) {
        const c = rgb[line[x]];
        if (c) image.data.set([c[0], c[1], c[2], 255], (y * asset.w + x) * 4);
      }
    });
    return image;
  }

  function frameCanvas(asset, index, rgb) {
    const canvas = document.createElement('canvas');
    canvas.width = asset.w;
    canvas.height = asset.h;
    const ctx = canvas.getContext('2d');
    ctx.putImageData(frameImage(ctx, asset, index, rgb), 0, 0);
    return canvas;
  }

  // All the frames laid out in a sheet, like the characters' pose sheets.
  function sheetCanvas(asset, rgb) {
    const canvas = document.createElement('canvas');
    canvas.width = asset.w * asset.cols;
    canvas.height = asset.h * asset.rows;
    const ctx = canvas.getContext('2d');
    asset.frames.forEach((_, i) => {
      ctx.drawImage(frameCanvas(asset, i, rgb), (i % asset.cols) * asset.w, Math.floor(i / asset.cols) * asset.h);
    });
    return canvas;
  }

  function checker(ctx, w, h, size) {
    for (let y = 0; y * size < h; y++) {
      for (let x = 0; x * size < w; x++) {
        ctx.fillStyle = (x + y) % 2 ? '#20242c' : '#282d37';
        ctx.fillRect(x * size, y * size, size, size);
      }
    }
  }

  function drawStage(asset, rgb) {
    const canvas = el('stage');
    canvas.width = asset.w * STAGE_SCALE;
    canvas.height = asset.h * STAGE_SCALE;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, STAGE_SCALE * 2);
    ctx.drawImage(frameCanvas(asset, frame, rgb), 0, 0, canvas.width, canvas.height);
  }

  function drawSheet(asset, rgb) {
    const canvas = el('sheet');
    const scaled = SHEET_SCALE;
    canvas.width = asset.w * asset.cols * scaled;
    canvas.height = asset.h * asset.rows * scaled;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, scaled * 2);
    ctx.drawImage(sheetCanvas(asset, rgb), 0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#6ea8fe';
    ctx.lineWidth = 2;
    ctx.strokeRect((frame % asset.cols) * asset.w * scaled + 1, Math.floor(frame / asset.cols) * asset.h * scaled + 1, asset.w * scaled - 2, asset.h * scaled - 2);
  }

  // The asset hovering above a character's head, as it would in play.
  function drawOver(asset, rgb) {
    const poses = window.BASE_POSES;
    const canvas = el('overCanvas');
    canvas.width = OVER_SIZE.w * OVER_SCALE;
    canvas.height = OVER_SIZE.h * OVER_SCALE;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, OVER_SCALE * 2);

    const base = poses.characters.find((c) => c.id === el('overBase').value);
    const pose = poses.poses.find((p) => p.id === el('overPose').value);
    const frames = base.frames[pose.id];
    const lines = frames[frame % frames.length];
    const left = (OVER_SIZE.w - CHARACTER_CELL) / 2;
    const topOfCell = OVER_SIZE.h - CHARACTER_CELL;

    const figure = document.createElement('canvas');
    figure.width = CHARACTER_CELL;
    figure.height = CHARACTER_CELL;
    const fctx = figure.getContext('2d');
    const image = fctx.createImageData(CHARACTER_CELL, CHARACTER_CELL);
    let headTop = null;
    const topCells = [];
    lines.forEach((line, y) => {
      for (let x = 0; x < CHARACTER_CELL; x++) {
        const c = defaultRgb[line[x]];
        if (!c) continue;
        image.data.set([c[0], c[1], c[2], 255], (y * CHARACTER_CELL + x) * 4);
        if (headTop === null) headTop = y;
        if (y <= headTop + 2) topCells.push(x);
      }
    });
    fctx.putImageData(image, 0, 0);
    ctx.drawImage(figure, left * OVER_SCALE, topOfCell * OVER_SCALE, CHARACTER_CELL * OVER_SCALE, CHARACTER_CELL * OVER_SCALE);

    const headCentre = left + topCells.reduce((a, b) => a + b, 0) / topCells.length + 0.5;
    const x0 = Math.round(headCentre - asset.anchor.x);
    const y0 = topOfCell + headTop - OVER_GAP - asset.anchor.y;
    ctx.drawImage(frameCanvas(asset, frame, rgb), x0 * OVER_SCALE, y0 * OVER_SCALE, asset.w * OVER_SCALE, asset.h * OVER_SCALE);
  }

  function render() {
    const asset = assetById(item.asset);
    const rgb = rgbOf(item);
    drawStage(asset, rgb);
    drawSheet(asset, rgb);
    if (window.BASE_POSES) drawOver(asset, rgb);
    el('assetTitle').textContent = asset.label;
    el('assetMeta').textContent = `${asset.id} · frame ${frame + 1} of ${asset.frames.length} · ${asset.w} × ${asset.h}`;
    el('anchorNote').textContent = `Anchor: x ${asset.anchor.x}, y ${asset.anchor.y}: the tip at rest. Place that point where the tip should hang; the bob moves it one row either way.`;
    el('play').textContent = playing ? 'Pause' : 'Play';
  }

  function syncControls() {
    refreshItems();
    el('assetSelect').value = item.asset;
    el('itemName').value = item.name;
    groups.forEach((g) => {
      const slider = document.querySelector(`input[data-hue="${g.id}"]`);
      if (slider) slider.value = item.hue[g.id] || 0;
      const readout = document.querySelector(`[data-hue-readout="${g.id}"]`);
      if (readout) readout.textContent = `${Math.round(item.hue[g.id] || 0)}°`;
    });
    roles.forEach((r) => {
      const input = document.querySelector(`input[data-role="${r.id}"]`);
      if (input) input.value = item.colors[r.id];
    });
  }

  function changed() {
    syncControls();
    render();
    persist();
  }

  /* ---------- controls ---------- */

  groups.forEach((g) => {
    const section = document.createElement('section');
    section.className = 'group';
    const heading = document.createElement('h2');
    heading.textContent = g.label;
    section.appendChild(heading);

    if (g.hue) {
      const row = document.createElement('label');
      row.className = 'hue';
      row.innerHTML = '<span>Hue</span><input type="range" min="-180" max="180" step="1" value="0"><span class="mono" data-hue-readout></span>';
      const slider = row.querySelector('input');
      slider.dataset.hue = g.id;
      row.querySelector('[data-hue-readout]').dataset.hueReadout = g.id;
      slider.addEventListener('input', () => {
        setGroupHue(g.id, Number(slider.value));
        changed();
      });
      section.appendChild(row);
    }

    const swatches = document.createElement('div');
    swatches.className = 'role-swatches';
    rolesOf(g.id).forEach((r) => {
      const input = document.createElement('input');
      input.type = 'color';
      input.dataset.role = r.id;
      input.title = r.label;
      input.setAttribute('aria-label', r.label);
      input.addEventListener('input', () => {
        item.colors[r.id] = input.value;
        changed();
      });
      swatches.appendChild(input);
    });
    section.appendChild(swatches);
    el('groups').appendChild(section);
  });

  assets.forEach((a) => {
    const option = document.createElement('option');
    option.value = a.id;
    option.textContent = a.label;
    el('assetSelect').appendChild(option);
  });

  el('assetSelect').addEventListener('change', (event) => {
    // An item still carrying its asset's default name follows it to the new asset.
    const renamed = item.name === assetById(item.asset).label;
    item.asset = event.target.value;
    if (renamed) item.name = assetById(item.asset).label;
    frame = 0;
    useAssetSpeed();
    changed();
    startTimer();
  });

  // Reset and Randomize change the colours only; the name stays.
  function resetColors() {
    item.colors = { ...baseColors };
    item.hue = {};
  }

  el('reset').addEventListener('click', () => {
    resetColors();
    changed();
  });

  el('randomize').addEventListener('click', () => {
    resetColors();
    groups.forEach((g) => {
      if (g.hue) setGroupHue(g.id, Math.floor(Math.random() * 360) - 180);
    });
    changed();
  });

  /* ---------- animation ---------- */

  function startTimer() {
    clearInterval(timer);
    timer = null;
    if (!playing) return;
    const asset = assetById(item.asset);
    timer = setInterval(() => {
      frame = (frame + 1) % asset.frames.length;
      render();
    }, 1000 / Number(el('fps').value));
  }

  el('play').addEventListener('click', () => {
    playing = !playing;
    startTimer();
    render();
  });
  el('fps').addEventListener('change', startTimer);

  // Each asset says how fast it is meant to run; start there.
  function useAssetSpeed() {
    el('fps').value = String(assetById(item.asset).fps);
  }

  /* ---------- over a character ---------- */

  if (window.BASE_POSES) {
    window.BASE_POSES.characters.forEach((c) => {
      const option = document.createElement('option');
      option.value = c.id;
      option.textContent = c.label;
      el('overBase').appendChild(option);
    });
    window.BASE_POSES.poses.forEach((p) => {
      const option = document.createElement('option');
      option.value = p.id;
      option.textContent = p.label;
      el('overPose').appendChild(option);
    });
    el('overPose').value = 'walkingSE';
    el('overBase').addEventListener('change', render);
    el('overPose').addEventListener('change', render);
  } else {
    el('over').hidden = true;
  }

  /* ---------- export ---------- */

  async function pngBytes(canvas, scale) {
    const out = document.createElement('canvas');
    out.width = canvas.width * scale;
    out.height = canvas.height * scale;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(canvas, 0, 0, out.width, out.height);
    const blob = await new Promise((resolve) => out.toBlob(resolve, 'image/png'));
    return new Uint8Array(await blob.arrayBuffer());
  }

  const scale = () => Number(el('exportScale').value);

  el('exportSheet').addEventListener('click', async () => {
    const asset = assetById(item.asset);
    const bytes = await pngBytes(sheetCanvas(asset, rgbOf(item)), scale());
    download(new Blob([bytes], { type: 'image/png' }), `${slug(item.name)}-sheet.png`);
  });

  // The sheet plus every frame on its own. With several items each gets a folder,
  // and two that share a name are told apart with a number.
  async function exportSets(items, zipName) {
    const folders = new Map();
    const files = [];
    for (const it of items) {
      const asset = assetById(it.asset);
      const rgb = rgbOf(it);
      let name = slug(it.name);
      const used = folders.get(name) || 0;
      folders.set(name, used + 1);
      if (used) name = `${name}-${used + 1}`;
      const folder = items.length > 1 ? `${name}/` : '';
      files.push({ name: `${folder}${name}-sheet.png`, data: await pngBytes(sheetCanvas(asset, rgb), scale()) });
      for (let i = 0; i < asset.frames.length; i++) {
        files.push({ name: `${folder}${name}-${String(i + 1).padStart(2, '0')}.png`, data: await pngBytes(frameCanvas(asset, i, rgb), scale()) });
      }
    }
    download(makeZip(files), zipName);
    el('note').textContent = `Exported ${files.length} PNGs in ${zipName}.`;
  }

  el('exportFrames').addEventListener('click', () => exportSets([item], `${slug(item.name)}-frames.zip`));
  el('exportAll').addEventListener('click', () => exportSets(store.items, 'assets.zip'));

  /* ---------- boot ---------- */

  useAssetSpeed();
  syncControls();
  render();
  startTimer();
}
