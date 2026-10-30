// Characters - the base poses are drawn in colour roles, not colours. A
// character is a role -> colour map, and every pose is recoloured from it.
// Characters are saved instances: copy one, change its colours, and open any of
// its poses in the editor to redraw them; the redrawn pose is stored on that
// character as an edit.

const STORE_KEY = 'pixel-creator.characters';
const OLD_KEY = 'pixel-creator.character';       // the single character stored before copies existed
const HANDOFF_KEY = 'pixel-creator.handoff';     // a pose on its way to the editor

// Character files saved before the roles followed the shared palette used
// these ids; each maps to the palette slot with the same colour.
const OLD_ROLE_IDS = {
  'skin-light': 'orange', skin: 'coral', 'skin-shadow': 'orchid', 'skin-pale': 'salmon', 'skin-warm': 'amber',
  'cloth-shadow': 'indigo', 'cloth-dark': 'blue', 'cloth-mid': 'teal', 'cloth-light': 'mint',
  'cloth-highlight': 'cream', 'cloth-grey': 'steel', 'cloth-bright': 'sky', 'cloth-deep': 'deep-teal',
  accent: 'yellow', 'mouth-dark': 'magenta-dark', mouth: 'magenta', 'mouth-bright': 'hot-pink',
};
const PLAY_MS = 150;
const GALLERY_SCALE = 3;
const STAGE_SCALE = 10;

const el = (id) => document.getElementById(id);
const data = window.BASE_POSES;

if (!data) {
  el('missing').hidden = false;
} else {
  boot();
}

function boot() {
  el('app').hidden = false;

  const { cell, roles, groups, poses, characters } = data;
  const baseColors = Object.fromEntries(roles.map((r) => [r.id, r.hex]));
  const rolesOf = (groupId) => roles.filter((r) => r.group === groupId);

  const roleChars = new Set(roles.map((r) => r.char));
  const baseById = (id) => characters.find((c) => c.id === id) || characters[0];
  const newId = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 8));

  let store = loadStore();
  let character = store.items.find((c) => c.id === store.current);
  let selected = poses.find((p) => p.id === 'chargingSE') || poses[0];
  let frame = 0;
  let playing = true;
  let timer = null;

  function fresh(baseId = characters[0].id) {
    return { id: newId(), name: baseById(baseId).label, base: baseId, hue: {}, colors: { ...baseColors }, edits: {} };
  }

  const frameCount = (pose) => pose.cols * pose.rows;

  /* ---------- colour ---------- */

  const toRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const toHex = (rgb) => '#' + rgb.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

  function shiftHue(hex, degrees) {
    const [r, g, b] = toRgb(hex).map((v) => v / 255);
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const l = (max + min) / 2;
    const d = max - min;
    let h = 0;
    let s = 0;
    if (d) {
      s = d / (1 - Math.abs(2 * l - 1));
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
    }
    h = (((h * 60 + degrees) % 360) + 360) % 360;
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = l - c / 2;
    const [r1, g1, b1] = [[c, x, 0], [x, c, 0], [0, c, x], [0, x, c], [x, 0, c], [c, 0, x]][Math.floor(h / 60) % 6];
    return toHex([(r1 + m) * 255, (g1 + m) * 255, (b1 + m) * 255]);
  }

  function setGroupHue(groupId, degrees) {
    character.hue[groupId] = degrees;
    rolesOf(groupId).forEach((r) => {
      character.colors[r.id] = shiftHue(baseColors[r.id], degrees);
    });
  }

  /* ---------- rendering ---------- */

  function rgbOf(ch) {
    const map = {};
    roles.forEach((r) => { map[r.char] = toRgb(ch.colors[r.id]); });
    return map;
  }

  // Paint every frame of a pose into one canvas, laid out like its source sheet.
  // A pose the character has edited is drawn from the edit, not from its base.
  function drawPose(canvas, pose, ch) {
    const w = pose.cols * cell;
    const h = pose.rows * cell;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    const image = ctx.createImageData(w, h);
    const rgb = rgbOf(ch);
    const edit = ch.edits[pose.id];
    if (edit) {
      edit.cells.forEach((value, i) => {
        if (!value) return;
        const c = value.length === 1 ? rgb[value] : toRgb(value);
        if (c) image.data.set([c[0], c[1], c[2], 255], i * 4);
      });
    } else {
      baseById(ch.base).frames[pose.id].forEach((lines, i) => {
        const ox = (i % pose.cols) * cell;
        const oy = Math.floor(i / pose.cols) * cell;
        lines.forEach((line, y) => {
          for (let x = 0; x < cell; x++) {
            const c = rgb[line[x]];
            if (!c) continue;
            image.data.set([c[0], c[1], c[2], 255], ((oy + y) * w + ox + x) * 4);
          }
        });
      });
    }
    ctx.putImageData(image, 0, 0);
  }

  function drawStage() {
    const canvas = el('stage');
    const size = cell * STAGE_SCALE;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;

    // A checkerboard keeps transparent cells visibly transparent.
    const half = STAGE_SCALE * 2;
    for (let y = 0; y * half < size; y++) {
      for (let x = 0; x * half < size; x++) {
        ctx.fillStyle = (x + y) % 2 ? '#20242c' : '#282d37';
        ctx.fillRect(x * half, y * half, half, half);
      }
    }

    const sheet = document.createElement('canvas');
    drawPose(sheet, selected, character);
    const sx = (frame % selected.cols) * cell;
    const sy = Math.floor(frame / selected.cols) * cell;
    ctx.drawImage(sheet, sx, sy, cell, cell, 0, 0, size, size);

    if (el('showGround').checked) {
      const y = (data.ground + 1) * STAGE_SCALE;
      ctx.fillStyle = 'rgba(110,168,254,0.7)';
      ctx.fillRect(0, y - 1, size, 2);
    }
  }

  function render() {
    document.querySelectorAll('.pose-card').forEach((card) => {
      const pose = poses.find((p) => p.id === card.dataset.id);
      drawPose(card.querySelector('canvas'), pose, character);
      card.classList.toggle('is-edited', Boolean(character.edits[pose.id]));
    });
    drawStage();
    const total = frameCount(selected);
    const edited = Boolean(character.edits[selected.id]);
    el('poseTitle').textContent = selected.label + (edited ? ' · edited' : '');
    el('poseMeta').textContent = total > 1
      ? `${selected.id} · frame ${frame + 1} of ${total}`
      : `${selected.id} · 1 frame`;
    el('play').hidden = total < 2;
    el('play').textContent = playing ? 'Pause' : 'Play';
    el('revertPose').hidden = !edited;
  }

  function syncControls() {
    refreshInstances();
    el('charName').value = character.name;
    el('baseSelect').value = character.base;
    groups.forEach((g) => {
      const slider = document.querySelector(`input[data-hue="${g.id}"]`);
      if (slider) slider.value = character.hue[g.id] || 0;
      const readout = document.querySelector(`[data-hue-readout="${g.id}"]`);
      if (readout) readout.textContent = `${Math.round(character.hue[g.id] || 0)}°`;
    });
    roles.forEach((r) => {
      const input = document.querySelector(`input[data-role="${r.id}"]`);
      if (input) input.value = character.colors[r.id];
    });
  }

  function changed() {
    syncControls();
    render();
    persist();
  }

  /* ---------- saved characters ---------- */

  function persist() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ version: 3, current: character.id, items: store.items }));
    } catch {
      el('charNote').textContent = 'Could not save: the browser storage is full or blocked.';
    }
  }

  function loadStore() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
      if (raw && Array.isArray(raw.items)) {
        const items = raw.items.map((item) => normalize(item, true)).filter(Boolean);
        if (items.length) return { current: items.some((i) => i.id === raw.current) ? raw.current : items[0].id, items };
      }
      const old = normalize(JSON.parse(localStorage.getItem(OLD_KEY) || 'null'), false);
      if (old) return { current: old.id, items: [old] };
    } catch { /* unreadable or blocked: start fresh */ }
    const first = fresh();
    return { current: first.id, items: [first] };
  }

  function refreshInstances() {
    const select = el('instanceSelect');
    select.textContent = '';
    store.items.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.name || 'Untitled';
      select.appendChild(option);
    });
    select.value = character.id;
    el('deleteChar').disabled = store.items.length < 2;
  }

  function switchTo(item) {
    character = item;
    store.current = item.id;
    changed();
  }

  el('instanceSelect').addEventListener('change', (event) => {
    switchTo(store.items.find((i) => i.id === event.target.value));
  });

  el('dupChar').addEventListener('click', () => {
    const copy = JSON.parse(JSON.stringify(character));
    copy.id = newId();
    copy.name = `${character.name} copy`;
    store.items.splice(store.items.indexOf(character) + 1, 0, copy);
    switchTo(copy);
    el('charNote').textContent = `Copied to "${copy.name}". Its colours and edits are its own now.`;
  });

  el('newChar').addEventListener('click', () => {
    const next = fresh(character.base);
    store.items.push(next);
    switchTo(next);
  });

  el('deleteChar').addEventListener('click', () => {
    if (store.items.length < 2 || !window.confirm(`Delete "${character.name}" and its edits?`)) return;
    const at = store.items.indexOf(character);
    store.items.splice(at, 1);
    switchTo(store.items[Math.min(at, store.items.length - 1)]);
  });

  // The editor saves into the same store from another page; pick its changes up.
  window.addEventListener('storage', (event) => {
    if (event.key !== STORE_KEY) return;
    store = loadStore();
    character = store.items.find((c) => c.id === store.current);
    syncControls();
    render();
  });

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
        character.colors[r.id] = input.value;
        changed();
      });
      swatches.appendChild(input);
    });
    section.appendChild(swatches);
    el('groups').appendChild(section);
  });

  characters.forEach((c) => {
    const option = document.createElement('option');
    option.value = c.id;
    option.textContent = c.label;
    el('baseSelect').appendChild(option);
  });

  el('baseSelect').addEventListener('change', (event) => {
    // A character still carrying its base's default name follows it to the new base.
    const renamed = character.name === baseById(character.base).label;
    character.base = event.target.value;
    if (renamed) character.name = baseById(character.base).label;
    changed();
  });

  el('charName').addEventListener('input', (event) => {
    character.name = event.target.value;
    el('instanceSelect').selectedOptions[0].textContent = character.name || 'Untitled';
    persist();
  });

  // Reset and Randomize change the colours only; the name and any edits stay.
  function resetColors() {
    character.colors = { ...baseColors };
    character.hue = {};
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

  /* ---------- gallery ---------- */

  poses.forEach((pose) => {
    const card = document.createElement('button');
    card.className = 'pose-card';
    card.dataset.id = pose.id;
    const canvas = document.createElement('canvas');
    canvas.style.width = pose.cols * cell * GALLERY_SCALE + 'px';
    canvas.style.height = pose.rows * cell * GALLERY_SCALE + 'px';
    const caption = document.createElement('span');
    caption.textContent = pose.label;
    card.append(canvas, caption);
    card.addEventListener('click', () => select(pose));
    el('gallery').appendChild(card);
  });

  function select(pose) {
    selected = pose;
    frame = 0;
    document.querySelectorAll('.pose-card').forEach((c) => {
      c.classList.toggle('is-active', c.dataset.id === pose.id);
    });
    startTimer();
    render();
  }

  function startTimer() {
    clearInterval(timer);
    timer = null;
    if (!playing || frameCount(selected) < 2) return;
    timer = setInterval(() => {
      frame = (frame + 1) % frameCount(selected);
      render();
    }, PLAY_MS);
  }

  el('play').addEventListener('click', () => {
    playing = !playing;
    startTimer();
    render();
  });

  el('showGround').addEventListener('change', render);
  el('groundRow').textContent = data.ground;

  /* ---------- editing a pose ---------- */

  // Hand the selected pose to the editor as plain colours, with the character's
  // role colours so the editor can tie matching pixels back to roles on save.
  el('editPose').addEventListener('click', () => {
    const sheet = document.createElement('canvas');
    drawPose(sheet, selected, character);
    const { data: px } = sheet.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, sheet.width, sheet.height);
    const pixels = [];
    for (let i = 0; i < px.length; i += 4) pixels.push(px[i + 3] ? toHex([px[i], px[i + 1], px[i + 2]]) : null);
    const roleColors = {};
    roles.forEach((r) => { roleColors[r.char] = character.colors[r.id]; });
    persist();
    try {
      localStorage.setItem(HANDOFF_KEY, JSON.stringify({
        instanceId: character.id, name: character.name, poseId: selected.id, label: selected.label,
        w: sheet.width, h: sheet.height, pixels, roleColors,
      }));
    } catch {
      el('charNote').textContent = 'Could not open the editor: the browser storage is full or blocked.';
      return;
    }
    window.location.href = 'index.html?edit=1';
  });

  el('revertPose').addEventListener('click', () => {
    delete character.edits[selected.id];
    changed();
    el('charNote').textContent = `${selected.label} is back to the base pose.`;
  });

  /* ---------- export, save, load ---------- */

  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  const slug = (text) => (text || 'character').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'character';

  async function pngBytes(ch, pose, scale) {
    const source = document.createElement('canvas');
    drawPose(source, pose, ch);
    const out = document.createElement('canvas');
    out.width = source.width * scale;
    out.height = source.height * scale;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(source, 0, 0, out.width, out.height);
    const blob = await new Promise((resolve) => out.toBlob(resolve, 'image/png'));
    return new Uint8Array(await blob.arrayBuffer());
  }

  el('exportPose').addEventListener('click', async () => {
    const bytes = await pngBytes(character, selected, Number(el('exportScale').value));
    download(new Blob([bytes], { type: 'image/png' }), `${slug(character.name)}-${selected.id}.png`);
  });

  // Every pose of each character, as one ZIP. With several characters each gets
  // a folder, and two that share a name are told apart with a number.
  async function exportSets(items, zipName) {
    const scale = Number(el('exportScale').value);
    const folders = new Map();
    const files = [];
    for (const ch of items) {
      let name = slug(ch.name);
      const used = folders.get(name) || 0;
      folders.set(name, used + 1);
      if (used) name = `${name}-${used + 1}`;
      for (const pose of poses) {
        const folder = items.length > 1 ? `${name}/` : '';
        files.push({ name: `${folder}${name}-${pose.id}.png`, data: await pngBytes(ch, pose, scale) });
      }
    }
    download(makeZip(files), zipName);
    el('charNote').textContent = `Exported ${files.length} PNGs in ${zipName}.`;
  }

  el('exportSet').addEventListener('click', () => exportSets([character], `${slug(character.name)}-set.zip`));
  el('exportAll').addEventListener('click', () => exportSets(store.items, 'characters.zip'));

  el('saveChar').addEventListener('click', () => {
    const { id, ...rest } = character;
    download(new Blob([JSON.stringify({ version: 3, ...rest }, null, 2)], { type: 'application/json' }), `${slug(character.name)}.json`);
  });

  // Loading a file adds a new character; it never replaces the one you have open.
  el('loadChar').addEventListener('click', () => el('loadFile').click());
  el('loadFile').addEventListener('change', async (event) => {
    const [file] = event.target.files;
    event.target.value = '';
    if (!file) return;
    let next = null;
    try { next = normalize(JSON.parse(await file.text()), false); } catch { /* not JSON */ }
    if (!next) {
      el('charNote').textContent = `${file.name} isn't a character file.`;
      return;
    }
    store.items.push(next);
    switchTo(next);
    el('charNote').textContent = `Loaded ${file.name} as "${next.name}".`;
  });

  // Anything missing falls back to the original colour, so older files keep working.
  function normalize(raw, keepId) {
    if (!raw || typeof raw !== 'object' || typeof raw.colors !== 'object' || !raw.colors) return null;
    const known = characters.find((c) => c.id === raw.base);
    const next = fresh((known || characters[0]).id);
    if (keepId && typeof raw.id === 'string') next.id = raw.id;
    next.name = typeof raw.name === 'string' ? raw.name : 'Loaded';
    const saved = { ...raw.colors };
    Object.entries(OLD_ROLE_IDS).forEach(([old, id]) => {
      if (old in saved && !(id in saved)) saved[id] = saved[old];
    });
    roles.forEach((r) => {
      const hex = saved[r.id];
      if (typeof hex === 'string' && /^#[0-9a-f]{6}$/i.test(hex)) next.colors[r.id] = hex.toLowerCase();
    });
    groups.forEach((g) => {
      const deg = raw.hue && Number(raw.hue[g.id]);
      if (Number.isFinite(deg)) next.hue[g.id] = deg;
    });
    poses.forEach((pose) => {
      const edit = raw.edits && raw.edits[pose.id];
      const size = pose.cols * cell * pose.rows * cell;
      const valid = (v) => typeof v === 'string' && (v === '' || (v.length === 1 && roleChars.has(v)) || /^#[0-9a-f]{6}$/.test(v));
      if (edit && Array.isArray(edit.cells) && edit.cells.length === size && edit.cells.every(valid)) {
        next.edits[pose.id] = { w: pose.cols * cell, h: pose.rows * cell, cells: edit.cells };
      }
    });
    return next;
  }

  /* ---------- boot ---------- */

  select(selected);
  syncControls();
}
