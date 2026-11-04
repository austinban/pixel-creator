// Assets - things that aren't characters, painted in the same colour roles, so
// they recolour the same way. An asset itself never changes: change anything and
// the change goes into a new saved copy (see copies.js), each with its own colours,
// so a copy per player can sit above whoever's turn it is.

const STORE_KEY = 'pixel-creator.assets';
const HANDOFF_KEY = 'pixel-creator.handoff';     // an asset on its way to the editor
const STAGE_SCALE = 12;
const SHEET_SCALE = 3;
const OVER_SCALE = 8;
const OVER_GAP = 2;        // rows between the asset's tip and the top of a head
const CHARACTER_CELL = 32;
const OVER_SIZE = { w: 48, h: 64 };          // an asset hanging above a character
const BESIDE_SIZE = { w: 64, h: 32 };        // an asset standing next to one, on the same ground
const BESIDE_AT = { asset: 0, character: 28 };

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
  const roleChars = new Set(roles.map((r) => r.char));
  const rolesOf = (groupId) => roles.filter((r) => r.group === groupId);
  const assetById = (id) => assets.find((a) => a.id === id) || assets[0];
  const isVariants = (asset) => asset.kind === 'variants';
  // Only an asset with several frames that turn one after another plays.
  const isAnimated = (asset) => asset.frames.length > 1 && !isVariants(asset);
  const newId = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 8));

  // Each asset shows as a read-only entry, never saved and never mutated: every
  // change goes through edit(), which swaps it for a copy first.
  const baseViews = {};
  function viewOf(assetId) {
    if (!baseViews[assetId]) baseViews[assetId] = baseView({ ...fresh(assetId), id: baseRefOf(assetId) });
    return baseViews[assetId];
  }

  let store = loadStore();
  let item = resolve(store.current);
  let frame = 0;
  let playing = true;
  let timer = null;

  function fresh(assetId = assets[0].id) {
    return { id: newId(), name: assetById(assetId).label, asset: assetId, hue: {}, colors: { ...baseColors }, edits: {} };
  }

  /* ---------- saved items ---------- */

  function resolve(ref) {
    if (isBaseRef(ref)) return viewOf(assetById(baseIdOf(ref)).id);
    return store.items.find((i) => i.id === ref) || viewOf(assets[0].id);
  }

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
    // Redrawn sheets, one per asset: kept only if they still fit the asset's layout.
    const valid = (v) => typeof v === 'string' && (v === '' || (v.length === 1 && roleChars.has(v)) || /^#[0-9a-f]{6}$/.test(v));
    assets.forEach((a) => {
      const edit = raw.edits && raw.edits[a.id];
      const size = a.w * a.cols * a.h * a.rows;
      if (edit && Array.isArray(edit.cells) && edit.cells.length === size && edit.cells.every(valid)) {
        next.edits[a.id] = { w: a.w * a.cols, h: a.h * a.rows, cells: edit.cells };
      }
    });
    return next;
  }

  function loadStore() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
      if (raw && Array.isArray(raw.items)) {
        // Everything already saved is a copy, however it got there.
        const items = raw.items.map(normalize).filter(Boolean);
        const known = items.some((i) => i.id === raw.current) || (isBaseRef(raw.current) && assets.some((a) => a.id === baseIdOf(raw.current)));
        return { current: known ? raw.current : (items.length ? items[0].id : baseRefOf(assets[0].id)), items };
      }
    } catch { /* unreadable or blocked: start fresh */ }
    return { current: baseRefOf(assets[0].id), items: [] };
  }

  function persist() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ version: 1, current: item.id, items: store.items }));
    } catch {
      el('note').textContent = 'Could not save: the browser storage is full or blocked.';
    }
  }

  function refreshItems() {
    fillPicker(el('instanceSelect'), item.readOnly ? [assetById(item.asset)] : [], store.items, item.id);
    el('deleteItem').disabled = item.readOnly;
  }

  // Call before changing the selected item. An asset is swapped for a new copy of
  // itself, so the change lands there and the asset stays as it was.
  function edit() {
    if (!item.readOnly) return;
    const copy = copyOf(item, newId(), `${item.name} copy`);
    store.items.push(copy);
    item = copy;
    store.current = copy.id;
    el('note').textContent = `Saved as "${copy.name}". The original is unchanged.`;
  }

  function switchTo(next, how = 'replace') {
    item = next;
    store.current = next.id;
    frame = 0;
    useAssetSpeed();
    changed();
    startTimer();
    syncUrl(how);
  }

  el('instanceSelect').addEventListener('change', (event) => switchTo(resolve(event.target.value)));

  el('dupItem').addEventListener('click', () => {
    const copy = copyOf(item, newId(), `${item.name} copy`);
    const at = store.items.indexOf(item);
    store.items.splice(at < 0 ? store.items.length : at + 1, 0, copy);
    switchTo(copy);
    el('note').textContent = `Copied to "${copy.name}". Its colours are its own now.`;
  });

  el('newItem').addEventListener('click', () => {
    const next = fresh(item.asset);
    store.items.push(next);
    switchTo(next);
  });

  el('deleteItem').addEventListener('click', () => {
    if (item.readOnly || !window.confirm(`Delete "${item.name}"?`)) return;
    const at = store.items.indexOf(item);
    store.items.splice(at, 1);
    // Fall back to a neighbouring copy, or to the asset it came from.
    switchTo(store.items.length ? store.items[Math.min(at, store.items.length - 1)] : viewOf(item.asset));
  });

  el('itemName').addEventListener('input', (event) => {
    item.name = event.target.value;
    el('instanceSelect').selectedOptions[0].textContent = item.name || 'Untitled';
    persist();
  });

  window.addEventListener('storage', (event) => {
    if (event.key === 'pixel-creator.characters') { refreshSwing(); render(); }
    if (event.key !== STORE_KEY) return;
    store = loadStore();
    item = resolve(store.current);
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
  // An asset the copy has redrawn is drawn from that edit, not from the original.
  const editOf = (it) => it.edits && it.edits[it.asset];

  function frameImage(ctx, asset, index, rgb, edit) {
    const image = ctx.createImageData(asset.w, asset.h);
    // A see-through asset (a tile overlay) is painted at its own opacity, so it tints what is under it.
    const alpha = Math.round(255 * (asset.opacity === undefined ? 1 : asset.opacity));
    if (edit) {
      const ox = (index % asset.cols) * asset.w;
      const oy = Math.floor(index / asset.cols) * asset.h;
      for (let y = 0; y < asset.h; y++) {
        for (let x = 0; x < asset.w; x++) {
          const v = edit.cells[(oy + y) * edit.w + ox + x];
          if (!v) continue;
          const c = v.length === 1 ? rgb[v] : toRgb(v);
          if (c) image.data.set([c[0], c[1], c[2], alpha], (y * asset.w + x) * 4);
        }
      }
      return image;
    }
    asset.frames[index].forEach((line, y) => {
      for (let x = 0; x < asset.w; x++) {
        const c = rgb[line[x]];
        if (c) image.data.set([c[0], c[1], c[2], alpha], (y * asset.w + x) * 4);
      }
    });
    return image;
  }

  function frameCanvas(asset, index, rgb, edit) {
    const canvas = document.createElement('canvas');
    canvas.width = asset.w;
    canvas.height = asset.h;
    const ctx = canvas.getContext('2d');
    ctx.putImageData(frameImage(ctx, asset, index, rgb, edit), 0, 0);
    return canvas;
  }

  // All the frames laid out in a sheet, like the characters' pose sheets.
  function sheetCanvas(asset, rgb, edit) {
    const canvas = document.createElement('canvas');
    canvas.width = asset.w * asset.cols;
    canvas.height = asset.h * asset.rows;
    const ctx = canvas.getContext('2d');
    asset.frames.forEach((_, i) => {
      ctx.drawImage(frameCanvas(asset, i, rgb, edit), (i % asset.cols) * asset.w, Math.floor(i / asset.cols) * asset.h);
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
    ctx.drawImage(frameCanvas(asset, frame, rgb, editOf(item)), 0, 0, canvas.width, canvas.height);
  }

  function drawSheet(asset, rgb) {
    const canvas = el('sheet');
    const scaled = SHEET_SCALE;
    canvas.width = asset.w * asset.cols * scaled;
    canvas.height = asset.h * asset.rows * scaled;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, scaled * 2);
    ctx.drawImage(sheetCanvas(asset, rgb, editOf(item)), 0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#6ea8fe';
    ctx.lineWidth = 2;
    ctx.strokeRect((frame % asset.cols) * asset.w * scaled + 1, Math.floor(frame / asset.cols) * asset.h * scaled + 1, asset.w * scaled - 2, asset.h * scaled - 2);
  }

  // The character frame for the view, as plain pixels, and where its head is.
  function characterFigure(frameIndex) {
    const poses = window.BASE_POSES;
    const base = poses.characters.find((c) => c.id === el('overBase').value);
    const pose = poses.poses.find((p) => p.id === el('overPose').value);
    const frames = base.frames[pose.id] || base.frames.chargingSE;     // a base without that pose stands
    const lines = frames[frameIndex % frames.length];
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
    return { canvas: figure, headTop, headCentre: topCells.reduce((s, x) => s + x, 0) / topCells.length + 0.5 };
  }

  // The asset in use beside a character: hanging above the head, or standing on the ground.
  function drawOver(asset, rgb) {
    const canvas = el('overCanvas');
    const size = asset.place === 'ground' ? BESIDE_SIZE : OVER_SIZE;
    canvas.width = size.w * OVER_SCALE;
    canvas.height = size.h * OVER_SCALE;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, OVER_SCALE * 2);
    const at = (x, y, source, w, h) => ctx.drawImage(source, x * OVER_SCALE, y * OVER_SCALE, w * OVER_SCALE, h * OVER_SCALE);

    if (asset.place === 'ground') {
      // Same cell, same ground row: they share a baseline and a scale.
      const figure = characterFigure(0);
      at(BESIDE_AT.asset, 0, frameCanvas(asset, frame, rgb, editOf(item)), asset.w, asset.h);
      at(BESIDE_AT.character, 0, figure.canvas, CHARACTER_CELL, CHARACTER_CELL);
      ctx.fillStyle = 'rgba(110,168,254,0.45)';
      ctx.fillRect(0, asset.anchor.y * OVER_SCALE - 1, canvas.width, 2);
      el('overNote').textContent = 'Standing on the same ground row as the character, at the same scale. The line marks the ground; an asset\u2019s anchor is where its base meets it.';
    } else {
      const figure = characterFigure(frame);
      const left = (OVER_SIZE.w - CHARACTER_CELL) / 2;
      const topOfCell = OVER_SIZE.h - CHARACTER_CELL;
      at(left, topOfCell, figure.canvas, CHARACTER_CELL, CHARACTER_CELL);
      const x0 = Math.round(left + figure.headCentre - asset.anchor.x);
      const y0 = topOfCell + figure.headTop - OVER_GAP - asset.anchor.y;
      at(x0, y0, frameCanvas(asset, frame, rgb, editOf(item)), asset.w, asset.h);
      el('overNote').textContent = 'Centred over the head, with its tip two rows above it at rest (one to three as it bobs). In your game, place each frame so its anchor sits where you want that tip.';
    }
  }

  /* ---------- a weapon with a character's animation ---------- */

  // A weapon strip is one facing of an attack: four frames, each in a cell bigger than a
  // character's, with the character in the middle. So the weapon can be shown over that
  // character's attack, one frame at a time, in step with the weapon's own frames.
  const SWING_SCALE = 8;

  function swingCharacters() {
    const bases = window.BASE_POSES ? window.BASE_POSES.characters : [];
    let copies = [];
    try {
      const raw = JSON.parse(localStorage.getItem('pixel-creator.characters') || 'null');
      copies = raw && Array.isArray(raw.items) ? raw.items : [];
    } catch { /* unreadable */ }
    return { bases, copies };
  }

  function refreshSwing() {
    const select = el('swingChar');
    const keep = select.value;
    select.textContent = '';
    const add = (value, text, parent) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = text;
      parent.appendChild(option);
    };
    add('none', 'None', select);
    const { bases, copies } = swingCharacters();
    const g1 = document.createElement('optgroup');
    g1.label = 'Characters';
    bases.forEach((b) => add(`base:${b.id}`, b.label, g1));
    select.appendChild(g1);
    if (copies.length) {
      const g2 = document.createElement('optgroup');
      g2.label = 'Your copies';
      copies.forEach((c) => add(`copy:${c.id}`, c.name || 'Untitled', g2));
      select.appendChild(g2);
    }
    select.value = [...select.options].some((o) => o.value === keep) ? keep : 'none';
  }

  function drawSwing(asset, rgb) {
    const choice = el('swingChar').value;
    const canvas = el('swingCanvas');
    const note = el('swingNote');
    // A weapon with its own animation (the bow) goes over that animation's frames, in the colours of the
    // chosen character; any other goes over the character's attack.
    const poseId = `attack${asset.facing}`;
    const { bases, copies } = swingCharacters();
    const copy = choice.startsWith('copy:') ? copies.find((c) => c.id === choice.slice(5)) : null;
    const base = bases.find((b) => b.id === (copy ? copy.base : choice.slice(5)));
    const poseData = asset.animation ? (base ? { label: 'bow draw', cols: 4 } : null) : window.BASE_POSES.poses.find((p) => p.id === poseId);
    const animFor = (who) => assetById(`${asset.animation}-${who}-${asset.facing.toLowerCase()}`);
    const anim = asset.animation && base ? (animFor(base.id) || animFor('slim')) : null;
    if (choice === 'none' || !base || !poseData || (!anim && !base.frames[poseId])) {
      canvas.width = canvas.height = 0;
      canvas.hidden = true;
      note.textContent = choice === 'none' ? 'Pick a character to see this weapon over its attack, one frame at a time.' : 'That character has no attack for this facing.';
      return;
    }
    canvas.hidden = false;
    const cell = window.BASE_POSES.cell;
    const pad = (asset.w - cell) / 2;
    canvas.width = asset.w * SWING_SCALE;
    canvas.height = asset.h * SWING_SCALE;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    checker(ctx, canvas.width, canvas.height, SWING_SCALE * 2);

    // The character's frame, in its own colours (and its own redraw, if it has one).
    const chRgb = {};
    window.BASE_POSES.roles.forEach((r) => { chRgb[r.char] = toRgb(copy ? (copy.colors[r.id] || r.hex) : r.hex); });
    const figure = document.createElement('canvas');
    figure.width = figure.height = cell;
    const fctx = figure.getContext('2d');
    const image = fctx.createImageData(cell, cell);
    const edit = !anim && copy && copy.edits && copy.edits[poseId];
    if (edit) {
      const sheetW = poseData.cols * cell;
      for (let y = 0; y < cell; y++) {
        for (let x = 0; x < cell; x++) {
          const v = edit.cells[y * sheetW + frame * cell + x];
          if (!v) continue;
          const c = v.length === 1 ? chRgb[v] : toRgb(v);
          if (c) image.data.set([c[0], c[1], c[2], 255], (y * cell + x) * 4);
        }
      }
    } else {
      (anim ? anim.frames[frame] : base.frames[poseId][frame]).forEach((line, y) => {
        for (let x = 0; x < cell; x++) {
          const c = chRgb[line[x]];
          if (c) image.data.set([c[0], c[1], c[2], 255], (y * cell + x) * 4);
        }
      });
    }
    fctx.putImageData(image, 0, 0);
    // The weapon goes behind the character, as it does in the game, in the colours (and any
    // redraw) of the one being viewed; the character is drawn over it.
    ctx.drawImage(frameCanvas(asset, frame, rgb, editOf(item)), 0, 0, canvas.width, canvas.height);
    ctx.drawImage(figure, pad * SWING_SCALE, pad * SWING_SCALE, cell * SWING_SCALE, cell * SWING_SCALE);
    note.textContent = `${asset.label} behind ${copy ? (copy.name || 'Untitled') : base.label}'s ${poseData.label.toLowerCase()}, frame ${frame + 1} of ${asset.frames.length}.`;
  }

  function render() {
    const asset = assetById(item.asset);
    const rgb = rgbOf(item);
    drawStage(asset, rgb);
    drawSheet(asset, rgb);
    // A weapon can be shown over a character's matching attack, frame by frame.
    const showSwing = Boolean(window.BASE_POSES) && Boolean(asset.weapon);
    el('swing').hidden = !showSwing;
    if (showSwing) drawSwing(asset, rgb);
    // Props that stand beside a character get that view; ground tiles don't.
    const showOver = Boolean(window.BASE_POSES) && asset.place !== 'none';
    el('over').hidden = !showOver;
    if (showOver) drawOver(asset, rgb);
    const variants = isVariants(asset);
    const animated = isAnimated(asset);
    const edited = Boolean(editOf(item));
    el('assetTitle').textContent = (variants ? `${asset.label}: ${asset.names[frame]}` : asset.label) + (edited ? ' · edited' : '');
    el('revertAsset').hidden = !edited;
    const where = asset.category ? `${asset.category} · ` : '';
    el('assetMeta').textContent = asset.frames.length < 2
      ? `${where}${asset.id} · ${asset.w} × ${asset.h}`
      : variants
        ? `${where}${asset.id} · variant ${frame + 1} of ${asset.frames.length} · ${asset.w} × ${asset.h}`
        : `${where}${asset.id} · frame ${frame + 1} of ${asset.frames.length} · ${asset.w} × ${asset.h}`;
    el('anchorNote').textContent = asset.place === 'ground'
      ? `Anchor: x ${asset.anchor.x}, y ${asset.anchor.y}: the middle of the base, on the ground. Click a variant below to switch.`
      : asset.place === 'above'
        ? `Anchor: x ${asset.anchor.x}, y ${asset.anchor.y}: the tip at rest. Place that point where the tip should hang; the bob moves it one row either way.`
        : '';
    el('play').hidden = !animated;
    el('speedRow').hidden = !animated;
    el('play').textContent = playing ? 'Pause' : 'Play';
  }

  function syncControls() {
    refreshItems();
    el('browseNow').textContent = assetById(item.asset).label;
    el('itemName').value = item.name;
    el('itemName').disabled = item.readOnly;
    el('reset').disabled = item.readOnly;
    if (item.readOnly) {
      el('note').textContent = `${item.name} is the original and never changes. Change anything to save it as your own copy.`;
    }
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
    if (frame >= assetById(item.asset).frames.length) frame = 0;
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
        edit();
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
        edit();
        item.colors[r.id] = input.value;
        changed();
      });
      swatches.appendChild(input);
    });
    section.appendChild(swatches);
    el('groups').appendChild(section);
  });

  // Reset and Randomize change the colours only; the name stays.
  function resetColors() {
    item.colors = { ...baseColors };
    item.hue = {};
  }

  el('reset').addEventListener('click', () => {
    if (item.readOnly) return;
    resetColors();
    changed();
  });

  el('randomize').addEventListener('click', () => {
    edit();
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
    const asset = assetById(item.asset);
    if (!playing || !isAnimated(asset)) return;
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
    const fps = assetById(item.asset).fps;
    if (fps) el('fps').value = String(fps);
  }

  // Click a frame in the filmstrip to look at it; for variants that is how you choose one.
  el('sheet').addEventListener('click', (event) => {
    const asset = assetById(item.asset);
    const rect = el('sheet').getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * el('sheet').width;
    const y = ((event.clientY - rect.top) / rect.height) * el('sheet').height;
    const index = Math.floor(y / (asset.h * SHEET_SCALE)) * asset.cols + Math.floor(x / (asset.w * SHEET_SCALE));
    if (index < 0 || index >= asset.frames.length) return;
    frame = index;
    render();
    if (isAnimated(asset)) startTimer();   // carry on from the frame you picked
  });

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

  /* ---------- browse ---------- */

  // A small picture of every asset, in its own colours, to pick from. Bases are
  // grouped by category; copies get a group of their own.
  const COPIES = 'Your copies';
  let browseCat = 'All';
  const categories = data.categories || [...new Set(assets.map((a) => a.category || 'Assets'))];

  function thumb(asset, source) {
    const rgb = source ? rgbOf(source) : defaultRgb;
    const scaleUp = Math.max(1, Math.floor(72 / Math.max(asset.w, asset.h)));
    const out = document.createElement('canvas');
    out.width = asset.w * scaleUp;
    out.height = asset.h * scaleUp;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(frameCanvas(asset, 0, rgb, source ? editOf(source) : null), 0, 0, out.width, out.height);
    return out;
  }

  function browseCard(label, asset, source, isCurrent, open) {
    const card = document.createElement('button');
    card.className = 'browse-card' + (isCurrent ? ' is-active' : '');
    card.title = label;
    card.setAttribute('aria-label', label);
    card.appendChild(thumb(asset, source));
    card.addEventListener('click', open);
    card.addEventListener('mouseenter', () => { el('browseName').textContent = label; });
    card.addEventListener('focus', () => { el('browseName').textContent = label; });
    return card;
  }

  function renderBrowse() {
    const query = el('browseSearch').value.trim().toLowerCase();
    const matches = (label, cat) => (!query || label.toLowerCase().includes(query) || cat.toLowerCase().includes(query));

    const chips = el('browseCats');
    chips.textContent = '';
    const names = ['All', ...categories, ...(store.items.length ? [COPIES] : [])];
    if (!names.includes(browseCat)) browseCat = 'All';
    names.forEach((name) => {
      const chip = document.createElement('button');
      chip.className = 'chip' + (name === browseCat ? ' is-active' : '');
      chip.textContent = name;
      chip.addEventListener('click', () => { browseCat = name; renderBrowse(); });
      chips.appendChild(chip);
    });

    const grid = el('browseGrid');
    grid.textContent = '';
    const section = (title, cards) => {
      if (!cards.length) return;
      const group = document.createElement('section');
      group.className = 'browse-group';
      const heading = document.createElement('h3');
      heading.textContent = `${title} (${cards.length})`;
      const row = document.createElement('div');
      row.className = 'browse-row';
      cards.forEach((c) => row.appendChild(c));
      group.append(heading, row);
      grid.appendChild(group);
    };

    if (browseCat === 'All' || browseCat === COPIES) {
      section(COPIES, store.items
        .filter((c) => matches(c.name || '', COPIES))
        .map((c) => browseCard(c.name || 'Untitled', assetById(c.asset), c, c.id === item.id, () => { switchTo(c, 'none'); closeBrowse(); })));
    }
    categories.forEach((cat) => {
      if (browseCat !== 'All' && browseCat !== cat) return;
      section(cat, assets
        .filter((a) => (a.category || 'Assets') === cat && matches(a.label, cat))
        .map((a) => browseCard(a.label, a, null, item.readOnly && item.asset === a.id, () => { switchTo(viewOf(a.id), 'none'); closeBrowse(); })));
    });
    if (!grid.children.length) grid.textContent = 'Nothing matches that search.';
  }

  function openBrowse(how = 'push') {
    el('app').classList.add('browsing');
    syncUrl(how);
    el('browseName').textContent = '';
    browseCat = 'All';          // each visit starts from everything
    el('browseSearch').value = '';
    renderBrowse();
    el('browseSearch').focus();
  }

  function closeBrowse(how = 'push') {
    el('app').classList.remove('browsing');
    syncUrl(how);
  }

  /* ---------- the address bar ---------- */

  // The address says what the page is showing: the browse grid (no ?item=), or one asset (?item=ID). Going into one from the grid, or
  // back to the grid, is a step in the browser's history, so Back returns to what was on screen before; Forward goes on again.
  const browsing = () => el('app').classList.contains('browsing');
  function addressNow() {
    const url = new URL(window.location.href);
    url.search = '';
    url.hash = '';
    if (!browsing()) url.searchParams.set('item', item.id);
    return url.toString();
  }

  // how: 'push' adds a step, 'replace' fixes the current one, 'none' leaves the address alone.
  function syncUrl(how = 'push') {
    if (how === 'none') return;
    const next = addressNow();
    if (next !== window.location.href) window.history[how + 'State'](null, '', next);
  }

  // Back and Forward: show whatever the address now says.
  window.addEventListener('popstate', () => {
    const ref = new URLSearchParams(window.location.search).get('item');
    if (ref) {
      switchTo(resolve(ref), 'none');
      closeBrowse('none');
    } else {
      openBrowse('none');
    }
  });

  el('browseBtn').addEventListener('click', () => (el('app').classList.contains('browsing') ? closeBrowse() : openBrowse()));
  el('browseClose').addEventListener('click', closeBrowse);
  el('browseSearch').addEventListener('input', renderBrowse);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && el('app').classList.contains('browsing')) closeBrowse();
  });

  el('swingChar').addEventListener('change', render);
  refreshSwing();

  /* ---------- editing ---------- */

  // Hand the whole sheet to the editor as plain colours, with the copy's role
  // colours so the editor can tie matching pixels back to roles on save. From an
  // original, the editor makes the copy when you save.
  el('editAsset').addEventListener('click', () => {
    const asset = assetById(item.asset);
    const sheet = sheetCanvas(asset, rgbOf(item), editOf(item));
    const { data: px } = sheet.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, sheet.width, sheet.height);
    const pixels = [];
    for (let i = 0; i < px.length; i += 4) pixels.push(px[i + 3] ? toHex([px[i], px[i + 1], px[i + 2]]) : null);
    const roleColors = {};
    roles.forEach((r) => { roleColors[r.char] = item.colors[r.id]; });
    persist();
    try {
      localStorage.setItem(HANDOFF_KEY, JSON.stringify({
        store: STORE_KEY, baseField: 'asset', returnUrl: 'assets.html?open=1', returnLabel: 'Back to assets',
        instanceId: item.readOnly ? null : item.id, baseId: item.asset, name: item.name,
        unitId: asset.id, label: asset.label,
        w: sheet.width, h: sheet.height, frameCols: asset.cols, frameRows: asset.rows, pixels, roleColors,
      }));
    } catch {
      el('note').textContent = 'Could not open the editor: the browser storage is full or blocked.';
      return;
    }
    window.location.href = 'index.html?edit=1';
  });

  el('revertAsset').addEventListener('click', () => {
    delete item.edits[item.asset];
    changed();
    el('note').textContent = `${assetById(item.asset).label} is back to the original.`;
  });

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
    const bytes = await pngBytes(sheetCanvas(asset, rgbOf(item), editOf(item)), scale());
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
      files.push({ name: `${folder}${name}-sheet.png`, data: await pngBytes(sheetCanvas(asset, rgb, editOf(it)), scale()) });
      for (let i = 0; i < asset.frames.length; i++) {
        const label = asset.names ? slug(asset.names[i]) : String(i + 1).padStart(2, '0');
        files.push({ name: `${folder}${name}-${label}.png`, data: await pngBytes(frameCanvas(asset, i, rgb, editOf(it)), scale()) });
      }
    }
    download(makeZip(files), zipName);
    el('note').textContent = `Exported ${files.length} PNGs in ${zipName}.`;
  }

  el('exportFrames').addEventListener('click', () => exportSets([item], `${slug(item.name)}-frames.zip`));
  el('exportAll').addEventListener('click', () => {
    if (!store.items.length) { el('note').textContent = 'No saved copies yet. Change an asset to make one.'; return; }
    exportSets(store.items, 'assets.zip');
  });

  /* ---------- boot ---------- */

  useAssetSpeed();
  syncControls();
  render();
  startTimer();

  // Arriving on the page starts in the browse view. Coming back from the editor
  // (?open=1) goes straight to the asset you were working on instead.
  const asked = new URLSearchParams(window.location.search);
  if (asked.get('item')) {
    switchTo(resolve(asked.get('item')), 'replace');          // a link to one asset opens on it
  } else if (asked.get('open') !== '1') {
    openBrowse('replace');
  } else {
    syncUrl('replace');
  }
}
