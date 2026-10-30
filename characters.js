// Characters - the base poses are drawn in colour roles, not colours. A
// character is a role -> colour map, and every pose is recoloured from it.

const STORAGE_KEY = 'pixel-creator.character';
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

  const { cell, roles, groups, poses } = data;
  const baseColors = Object.fromEntries(roles.map((r) => [r.id, r.hex]));
  const rolesOf = (groupId) => roles.filter((r) => r.group === groupId);

  let character = fresh();
  let selected = poses.find((p) => p.id === 'chargingSE') || poses[0];
  let frame = 0;
  let playing = true;
  let timer = null;

  function fresh() {
    return { name: 'Cleric', hue: {}, colors: { ...baseColors } };
  }

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

  function rgbByChar() {
    const map = {};
    roles.forEach((r) => { map[r.char] = toRgb(character.colors[r.id]); });
    return map;
  }

  // Paint every frame of a pose into one canvas, laid out like its source sheet.
  function drawPose(canvas, pose, rgb) {
    const w = pose.cols * cell;
    const h = pose.rows * cell;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    const image = ctx.createImageData(w, h);
    pose.frames.forEach((lines, i) => {
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
    ctx.putImageData(image, 0, 0);
  }

  function drawStage(rgb) {
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
    drawPose(sheet, selected, rgb);
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
    const rgb = rgbByChar();
    document.querySelectorAll('.pose-card canvas').forEach((canvas) => {
      const pose = poses.find((p) => p.id === canvas.closest('.pose-card').dataset.id);
      drawPose(canvas, pose, rgb);
    });
    drawStage(rgb);
    const total = selected.frames.length;
    el('poseTitle').textContent = selected.label;
    el('poseMeta').textContent = total > 1
      ? `${selected.id} · frame ${frame + 1} of ${total}`
      : `${selected.id} · 1 frame`;
    el('play').hidden = total < 2;
    el('play').textContent = playing ? 'Pause' : 'Play';
  }

  function syncControls() {
    el('charName').value = character.name;
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
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(character)); } catch { /* storage full or blocked */ }
  }

  /* ---------- controls ---------- */

  groups.forEach((g) => {
    const section = document.createElement('section');
    section.className = 'group';
    const heading = document.createElement('h2');
    heading.textContent = g.label;
    section.appendChild(heading);

    if (g.id !== 'outline') {
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

  el('charName').addEventListener('input', (event) => {
    character.name = event.target.value;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(character)); } catch { /* ignore */ }
  });

  el('reset').addEventListener('click', () => {
    character = fresh();
    changed();
  });

  el('randomize').addEventListener('click', () => {
    character = fresh();
    character.name = 'Random';
    groups.forEach((g) => {
      if (g.id !== 'outline') setGroupHue(g.id, Math.floor(Math.random() * 360) - 180);
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
    if (!playing || selected.frames.length < 2) return;
    timer = setInterval(() => {
      frame = (frame + 1) % selected.frames.length;
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

  el('exportPose').addEventListener('click', () => {
    const scale = Number(el('exportScale').value);
    const source = document.createElement('canvas');
    drawPose(source, selected, rgbByChar());
    const out = document.createElement('canvas');
    out.width = source.width * scale;
    out.height = source.height * scale;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(source, 0, 0, out.width, out.height);
    out.toBlob((blob) => download(blob, `${slug(character.name)}-${selected.id}.png`), 'image/png');
  });

  el('saveChar').addEventListener('click', () => {
    const json = JSON.stringify({ version: 1, ...character }, null, 2);
    download(new Blob([json], { type: 'application/json' }), `${slug(character.name)}.json`);
  });

  el('loadChar').addEventListener('click', () => el('loadFile').click());
  el('loadFile').addEventListener('change', async (event) => {
    const [file] = event.target.files;
    event.target.value = '';
    if (!file) return;
    const next = parseCharacter(await file.text());
    if (!next) {
      el('charNote').textContent = `${file.name} isn't a character file.`;
      return;
    }
    character = next;
    el('charNote').textContent = `Loaded ${file.name}.`;
    changed();
  });

  // Anything missing falls back to the original colour, so older files keep working.
  function parseCharacter(text) {
    let raw;
    try { raw = JSON.parse(text); } catch { return null; }
    if (!raw || typeof raw !== 'object' || typeof raw.colors !== 'object' || !raw.colors) return null;
    const next = fresh();
    next.name = typeof raw.name === 'string' ? raw.name : 'Loaded';
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

  /* ---------- boot ---------- */

  try {
    const saved = parseCharacter(localStorage.getItem(STORAGE_KEY) || '');
    if (saved) character = saved;
  } catch { /* storage blocked */ }

  select(selected);
  syncControls();
}
