// Characters - the base poses are drawn in colour roles, not colours. A
// character is a role -> colour map, and every pose is recoloured from it.
// A base never changes. Pick one and change anything, and the change goes into a
// new saved copy (see copies.js). Copies keep their own colours, and any of their
// poses can be opened in the editor to redraw; the redrawn pose is stored on that
// copy as an edit.

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

  // Each base shows as a read-only entry. It is never saved and never mutated:
  // every change goes through edit(), which swaps it for a copy first.
  const baseViews = {};
  function viewOf(baseId) {
    if (!baseViews[baseId]) baseViews[baseId] = baseView({ ...fresh(baseId), id: baseRefOf(baseId) });
    return baseViews[baseId];
  }

  let store = loadStore();
  let character = resolve(store.current);
  let selected = poses.find((p) => p.id === 'chargingSE') || poses[0];
  let frame = 0;
  let playing = true;
  let timer = null;

  function fresh(baseId = characters[0].id) {
    return { id: newId(), name: baseById(baseId).label, base: baseId, hue: {}, colors: { ...baseColors }, edits: {} };
  }

  function resolve(ref) {
    if (isBaseRef(ref)) return viewOf(baseById(baseIdOf(ref)).id);
    return store.items.find((c) => c.id === ref) || viewOf(characters[0].id);
  }

  const frameCount = (pose) => pose.cols * pose.rows;

  /* ---------- colour ---------- */

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

  /* ---------- weapons ---------- */

  // Weapons are assets in the Weapons category: one strip of four frames per facing, each frame
  // in the cell of the attack frame it goes with. Choosing one draws its frame behind the
  // character's, as in the game, so you can see how it sits against the hand frame by frame.
  const weaponAssets = ((window.ASSETS && window.ASSETS.assets) || []).filter((a) => a.weapon && !a.animation);   // a weapon with its own animation (the bow) is not for the attack
  const defaultRgb = Object.fromEntries(roles.map((r) => [r.char, toRgb(r.hex)]));
  let weapon = 'none';   // 'none', a weapon's name, or 'copy:<id>' for one of your saved copies

  function weaponCopies() {
    try {
      const raw = JSON.parse(localStorage.getItem('pixel-creator.assets') || 'null');
      return (raw && Array.isArray(raw.items) ? raw.items : []).filter((i) => weaponAssets.some((a) => a.id === i.asset));
    } catch { return []; }
  }

  function refreshWeapons() {
    const select = el('weapon');
    select.textContent = '';
    const add = (value, text, parent) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = text;
      parent.appendChild(option);
    };
    add('none', 'None', select);
    const names = [...new Set(weaponAssets.map((a) => a.weapon))];
    names.forEach((n) => add(n, weaponAssets.find((a) => a.weapon === n).label.replace(/ (NE|SE)$/, ''), select));
    const copies = weaponCopies();
    if (copies.length) {
      const group = document.createElement('optgroup');
      group.label = 'Your copies';
      copies.forEach((c) => add(`copy:${c.id}`, c.name || 'Untitled', group));
      select.appendChild(group);
    }
    if (![...select.options].some((o) => o.value === weapon)) weapon = 'none';
    select.value = weapon;
    el('weaponRow').hidden = !weaponAssets.length;
  }

  // The weapon asset (and the colours and edit of a copy) that goes with a pose, if any.
  function weaponFor(pose) {
    if (weapon === 'none' || pose.action !== 'attack') return null;
    let name = weapon;
    let copy = null;
    if (weapon.startsWith('copy:')) {
      copy = weaponCopies().find((c) => c.id === weapon.slice(5));
      if (!copy) return null;
      name = weaponAssets.find((a) => a.id === copy.asset).weapon;
    }
    const asset = weaponAssets.find((a) => a.weapon === name && a.facing === pose.facing);
    if (!asset) return null;
    // A copy is of one facing's strip; for the other facing the original weapon is used.
    const own = copy && copy.asset === asset.id ? copy : null;
    const rgb = { ...defaultRgb };
    if (own) {
      const map = (window.ASSETS.roles || roles).reduce((m, r) => { m[r.char] = toRgb(own.colors[r.id] || r.hex); return m; }, {});
      Object.assign(rgb, map);
    }
    return { asset, rgb, edit: own && own.edits ? own.edits[asset.id] : null };
  }

  // The weapon's four frames as one canvas, laid out like the attack pose's sheet.
  function weaponSheet(found) {
    const { asset, rgb, edit } = found;
    const w = asset.w * asset.cols;
    const h = asset.h * asset.rows;
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    const image = ctx.createImageData(w, h);
    if (edit) {
      edit.cells.forEach((value, i) => {
        if (!value) return;
        const col = value.length === 1 ? rgb[value] : toRgb(value);
        if (col) image.data.set([col[0], col[1], col[2], 255], i * 4);
      });
    } else {
      asset.frames.forEach((lines, f) => {
        const ox = (f % asset.cols) * asset.w;
        const oy = Math.floor(f / asset.cols) * asset.h;
        lines.forEach((line, y) => {
          for (let x = 0; x < asset.w; x++) {
            const col = rgb[line[x]];
            if (col) image.data.set([col[0], col[1], col[2], 255], ((oy + y) * w + ox + x) * 4);
          }
        });
      });
    }
    ctx.putImageData(image, 0, 0);
    return c;
  }

  // Paint every frame of a pose into one canvas, laid out like its source sheet.
  // A pose the character has edited is drawn from the edit, not from its base. With
  // `withWeapon`, the chosen weapon is drawn behind an attack pose. A weapon's cell is bigger than a
  // character's, so each frame grows to the weapon's size with the character in the middle of it.
  // Not every base has every pose: the bow draw is only for the people built from the 3D model.
  const hasPose = (ch, pose) => Boolean(baseById(ch.base).frames[pose.id]);

  function drawPose(canvas, pose, ch, withWeapon = false) {
    if (!hasPose(ch, pose)) { canvas.width = canvas.height = 0; return; }
    const found = withWeapon && weaponFor(pose);
    const pad = found ? (found.asset.w - cell) / 2 : 0;
    const out = cell + 2 * pad;                    // the size of one frame on the canvas
    const w = pose.cols * out;
    const h = pose.rows * out;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    const image = ctx.createImageData(w, h);
    const rgb = rgbOf(ch);
    const put = (frameIndex, x, y, c) => {
      const px = (frameIndex % pose.cols) * out + pad + x;
      const py = Math.floor(frameIndex / pose.cols) * out + pad + y;
      image.data.set([c[0], c[1], c[2], 255], (py * w + px) * 4);
    };
    const edit = ch.edits[pose.id];
    if (edit) {
      const sheetW = pose.cols * cell;
      edit.cells.forEach((value, i) => {
        if (!value) return;
        const c = value.length === 1 ? rgb[value] : toRgb(value);
        if (!c) return;
        const x = i % sheetW;
        const y = Math.floor(i / sheetW);
        put(Math.floor(y / cell) * pose.cols + Math.floor(x / cell), x % cell, y % cell, c);
      });
    } else {
      baseById(ch.base).frames[pose.id].forEach((lines, i) => {
        lines.forEach((line, y) => {
          for (let x = 0; x < cell; x++) {
            const c = rgb[line[x]];
            if (c) put(i, x, y, c);
          }
        });
      });
    }
    // The weapon goes behind the character, as it does in the game: the hand and the body cover it.
    const figure = document.createElement('canvas');
    figure.width = w;
    figure.height = h;
    figure.getContext('2d').putImageData(image, 0, 0);
    if (found) ctx.drawImage(weaponSheet(found), 0, 0);
    ctx.drawImage(figure, 0, 0);
    return { out, pad };
  }

  function drawStage() {
    const canvas = el('stage');
    const sheet = document.createElement('canvas');
    const { out, pad } = drawPose(sheet, selected, character, true);
    const size = out * STAGE_SCALE;
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

    const sx = (frame % selected.cols) * out;
    const sy = Math.floor(frame / selected.cols) * out;
    ctx.drawImage(sheet, sx, sy, out, out, 0, 0, size, size);

    if (el('showGround').checked) {
      const y = (pad + data.ground + 1) * STAGE_SCALE;
      ctx.fillStyle = 'rgba(110,168,254,0.7)';
      ctx.fillRect(0, y - 1, size, 2);
    }
  }

  function render() {
    if (!hasPose(character, selected)) selected = poses.find((p) => p.id === 'chargingSE') || poses[0];
    document.querySelectorAll('.pose-card').forEach((card) => {
      const pose = poses.find((p) => p.id === card.dataset.id);
      card.hidden = !hasPose(character, pose);
      if (card.hidden) return;
      const cardCanvas = card.querySelector('canvas');
      drawPose(cardCanvas, pose, character, true);
      // A bigger frame (with a weapon) keeps the same scale, so the card grows with it.
      cardCanvas.style.width = cardCanvas.width * GALLERY_SCALE + 'px';
      cardCanvas.style.height = cardCanvas.height * GALLERY_SCALE + 'px';
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
    el('stepPrev').hidden = total < 2;
    el('stepNext').hidden = total < 2;
    el('play').textContent = playing ? 'Pause' : 'Play';
    const shown = weaponFor(selected);
    el('weaponNote').textContent = weapon === 'none' ? ''
      : shown ? `${shown.asset.label} over frame ${frame + 1}.`
        : selected.action === 'attack' ? 'No strip for this facing.' : 'The weapon shows on the attack poses.';
    el('revertPose').hidden = !edited;
  }

  function syncControls() {
    refreshInstances();
    el('charName').value = character.name;
    el('browseNow').textContent = character.name || 'Untitled';
    el('baseSelect').value = character.base;
    el('charName').disabled = character.readOnly;
    el('reset').disabled = character.readOnly;
    if (character.readOnly) {
      el('charNote').textContent = `${character.name} is a base and never changes. Change anything to save it as your own copy.`;
    }
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
        // Everything already saved is a copy, however it got there.
        const items = raw.items.map((item) => normalize(item, true)).filter(Boolean);
        const known = items.some((i) => i.id === raw.current) || (isBaseRef(raw.current) && characters.some((c) => c.id === baseIdOf(raw.current)));
        return { current: known ? raw.current : (items.length ? items[0].id : baseRefOf(characters[0].id)), items };
      }
      const old = normalize(JSON.parse(localStorage.getItem(OLD_KEY) || 'null'), false);
      if (old) return { current: old.id, items: [old] };
    } catch { /* unreadable or blocked: start fresh */ }
    return { current: baseRefOf(characters[0].id), items: [] };
  }

  function refreshInstances() {
    fillPicker(el('instanceSelect'), characters, store.items, character.id);
    el('deleteChar').disabled = character.readOnly;
  }

  // Call before changing the selected character. A base is swapped for a new copy
  // of itself, so the change lands there and the base stays as it was.
  function edit() {
    if (!character.readOnly) return;
    const copy = copyOf(character, newId(), `${character.name} copy`);
    store.items.push(copy);
    character = copy;
    store.current = copy.id;
    el('charNote').textContent = `Saved as "${copy.name}". The base is unchanged.`;
  }

  function switchTo(item, how = 'replace') {
    character = item;
    store.current = item.id;
    changed();
    syncUrl(how);
  }

  el('instanceSelect').addEventListener('change', (event) => {
    switchTo(resolve(event.target.value));
  });

  el('dupChar').addEventListener('click', () => {
    const copy = copyOf(character, newId(), `${character.name} copy`);
    const at = store.items.indexOf(character);
    store.items.splice(at < 0 ? store.items.length : at + 1, 0, copy);
    switchTo(copy);
    el('charNote').textContent = `Copied to "${copy.name}". Its colours and edits are its own now.`;
  });

  el('newChar').addEventListener('click', () => {
    const next = fresh(character.base);
    store.items.push(next);
    switchTo(next);
  });

  el('deleteChar').addEventListener('click', () => {
    if (character.readOnly || !window.confirm(`Delete "${character.name}" and its edits?`)) return;
    const at = store.items.indexOf(character);
    store.items.splice(at, 1);
    // Fall back to a neighbouring copy, or to the base it came from.
    switchTo(store.items.length ? store.items[Math.min(at, store.items.length - 1)] : viewOf(character.base));
  });

  // The editor saves into the same store from another page; pick its changes up.
  window.addEventListener('storage', (event) => {
    if (event.key === 'pixel-creator.assets') refreshWeapons();
    if (event.key !== STORE_KEY) return;
    store = loadStore();
    character = resolve(store.current);
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
        character.colors[r.id] = input.value;
        changed();
      });
      swatches.appendChild(input);
    });
    section.appendChild(swatches);
    el('groups').appendChild(section);
  });

  // The bases, in two groups: the people (humanoids) and the creatures. A base's `kind` says which; one without is a person.
  [['humanoid', 'Humanoids'], ['creature', 'Creatures']].forEach(([kind, title]) => {
    const group = characters.filter((c) => (c.kind || 'humanoid') === kind);
    if (!group.length) return;
    const optgroup = document.createElement('optgroup');
    optgroup.label = `${title} (${group.length})`;
    group.forEach((c) => {
      const option = document.createElement('option');
      option.value = c.id;
      option.textContent = c.label;
      optgroup.appendChild(option);
    });
    el('baseSelect').appendChild(optgroup);
  });

  el('baseSelect').addEventListener('change', (event) => {
    // On a base this just looks at another base; on a copy it moves the copy to it.
    if (character.readOnly) {
      switchTo(viewOf(event.target.value));
      return;
    }
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
    if (character.readOnly) return;
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

  // Step through the frames by hand, which pauses the animation.
  function step(by) {
    const total = frameCount(selected);
    if (total < 2) return;
    playing = false;
    frame = (frame + by + total) % total;
    startTimer();
    render();
  }
  el('stepPrev').addEventListener('click', () => step(-1));
  el('stepNext').addEventListener('click', () => step(1));
  document.addEventListener('keydown', (event) => {
    if (event.target.matches('input, select, textarea') || event.metaKey || event.ctrlKey || event.altKey) return;
    if (el('app').classList.contains('browsing')) return;
    const key = event.key.toLowerCase();
    if (key === 'arrowleft' || key === 'a') { event.preventDefault(); step(-1); }
    if (key === 'arrowright' || key === 'd') { event.preventDefault(); step(1); }
  });

  // Choosing a weapon takes you to an attack pose, since that is where it shows.
  el('weapon').addEventListener('change', (event) => {
    weapon = event.target.value;
    if (weapon !== 'none' && selected.action !== 'attack') select(poses.find((p) => p.id === 'attackSE') || selected);
    else render();
  });
  el('groundRow').textContent = data.ground;

  /* ---------- browse ---------- */

  // A small picture of every base and every copy, in its own colours, to pick from.
  const BASES = 'Bases';
  const COPIES = 'Your copies';
  const THUMB_POSE = poses.find((p) => p.id === 'chargingSE') || poses[0];
  const THUMB_SCALE = 2;
  let browseCat = 'All';

  function thumb(ch) {
    const sheet = document.createElement('canvas');
    drawPose(sheet, THUMB_POSE, ch);
    const out = document.createElement('canvas');
    out.width = cell * THUMB_SCALE;
    out.height = cell * THUMB_SCALE;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(sheet, 0, 0, cell, cell, 0, 0, out.width, out.height);   // the first frame
    return out;
  }

  function browseCard(label, ch, isCurrent, open) {
    const card = document.createElement('button');
    card.className = 'browse-card' + (isCurrent ? ' is-active' : '');
    card.title = label;
    card.setAttribute('aria-label', label);
    card.appendChild(thumb(ch));
    card.addEventListener('click', open);
    card.addEventListener('mouseenter', () => { el('browseName').textContent = label; });
    card.addEventListener('focus', () => { el('browseName').textContent = label; });
    return card;
  }

  function renderBrowse() {
    const query = el('browseSearch').value.trim().toLowerCase();
    const matches = (label) => !query || label.toLowerCase().includes(query);

    const chips = el('browseCats');
    chips.textContent = '';
    const names = ['All', BASES, ...(store.items.length ? [COPIES] : [])];
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

    if (browseCat === 'All' || browseCat === BASES) {
      section(BASES, characters
        .filter((b) => matches(b.label))
        .map((b) => browseCard(b.label, viewOf(b.id), character.readOnly && character.base === b.id, () => { switchTo(viewOf(b.id), 'none'); closeBrowse(); })));
    }
    if (browseCat === 'All' || browseCat === COPIES) {
      section(COPIES, store.items
        .filter((c) => matches(c.name || ''))
        .map((c) => browseCard(c.name || 'Untitled', c, c.id === character.id, () => { switchTo(c, 'none'); closeBrowse(); })));
    }
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

  // The address says what the page is showing: the browse grid (no ?item=), or one character (?item=ID). Going into one from the grid, or
  // back to the grid, is a step in the browser's history, so Back returns to what was on screen before; Forward goes on again.
  const browsing = () => el('app').classList.contains('browsing');
  function addressNow() {
    const url = new URL(window.location.href);
    url.search = '';
    url.hash = '';
    if (!browsing()) url.searchParams.set('item', character.id);
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
        store: STORE_KEY, baseField: 'base', returnUrl: 'characters.html?open=1', returnLabel: 'Back to characters',
        unitId: selected.id,
        instanceId: character.readOnly ? null : character.id, baseId: character.base,
        name: character.name, poseId: selected.id, label: selected.label,
        w: sheet.width, h: sheet.height, frameCols: selected.cols, frameRows: selected.rows, pixels, roleColors,
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

  // What a set says about itself, for the game: written beside the PNGs of "Export for the game" and "Save to sprites/".
  const gameManifest = (ch, name) => ({ format: 1, kind: 'character', set: name, base: ch.base, scale: 1, cell: [cell, cell] });

  // The poses a character has, as PNG files named <name>-<pose>.png.
  async function setFiles(ch, name, scale, folder = '') {
    const files = [];
    for (const pose of poses) {
      if (!hasPose(ch, pose)) continue;
      files.push({ name: `${folder}${name}-${pose.id}.png`, data: await pngBytes(ch, pose, scale) });
    }
    return files;
  }

  // Names for a list of characters: two that share a name are told apart with a number.
  function uniqueNames(items) {
    const used = new Map();
    return items.map((ch) => {
      let name = slug(ch.name);
      const count = used.get(name) || 0;
      used.set(name, count + 1);
      return count ? `${name}-${count + 1}` : name;
    });
  }

  // Every pose of each character, as one ZIP. With several characters each gets a folder. `forGame` makes it 1x, whatever
  // the size menu says, and puts a pixel-creator.json in each set (the ZIP's root for one character, the folder for several).
  async function exportSets(items, zipName, forGame = false) {
    const scale = forGame ? 1 : Number(el('exportScale').value);
    const names = uniqueNames(items);
    const files = [];
    for (const [i, ch] of items.entries()) {
      const folder = items.length > 1 ? `${names[i]}/` : '';
      files.push(...await setFiles(ch, names[i], scale, folder));
      if (forGame) files.push({ name: `${folder}pixel-creator.json`, data: new TextEncoder().encode(JSON.stringify(gameManifest(ch, names[i]), null, 2) + '\n') });
    }
    download(makeZip(files), zipName);
    el('charNote').textContent = `Exported ${files.length} files in ${zipName}${forGame ? ' (1x, with pixel-creator.json)' : ''}.`;
  }

  el('exportSet').addEventListener('click', () => exportSets([character], `${slug(character.name)}-set.zip`));
  el('exportAll').addEventListener('click', () => {
    if (!store.items.length) { el('charNote').textContent = 'No saved copies yet. Change a base to make one.'; return; }
    exportSets(store.items, 'characters.zip');
  });
  el('exportGame').addEventListener('click', () => exportSets([character], `${slug(character.name)}-for-game.zip`, true));

  // Straight into the repo's sprites/ folder (Chromium), at 1x, where the game's sync script reads it. See sprites-save.js.
  if (!canSaveToSprites()) {
    el('saveSprites').disabled = true;
    el('saveSprites').title = 'Needs a Chromium browser (Chrome, Edge). Use "Export for the game" instead.';
  }
  el('saveSprites').addEventListener('click', async () => {
    const note = (text) => { el('charNote').textContent = text; };
    const name = slug(character.name);
    try {
      const sprites = await spritesFolder();
      const problem = await setFolderProblem(sprites, name, characters.map((c) => c.id));
      if (problem) { note(problem); return; }
      const files = await setFiles(character, name, 1);
      await writeSetFolder(sprites, name, files, gameManifest(character, name));
      note(`Saved ${files.length} poses to sprites/${name}/ at 1x. Run the game's sync script to pick them up.`);
    } catch (error) {
      note(error.message || String(error));
    }
  });

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

  refreshWeapons();
  select(selected);
  syncControls();

  // Arriving on the page starts in the browse view. Coming back from the editor
  // (?open=1) goes straight to the character you were working on instead.
  const asked = new URLSearchParams(window.location.search);
  if (asked.get('item')) {
    switchTo(resolve(asked.get('item')), 'replace');          // a link to one character opens on it
  } else if (asked.get('open') !== '1') {
    openBrowse('replace');
  } else {
    syncUrl('replace');
  }
}
