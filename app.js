// Pixel Creator - a grid of cells, each either a colour or transparent (null).
// No build step, no dependencies: the whole editor is this file.

const MAX_DIM = 128;
const DISPLAY_MAX = 560; // longest on-screen edge of the canvas, in CSS pixels
const MAX_HISTORY = 100;

const DEFAULT_PALETTE = [
  '#000000', '#ffffff', '#e06c75', '#d19a66',
  '#e5c07b', '#98c379', '#56b6c2', '#61afef',
  '#c678dd', '#be5046', '#8b5a2b', '#3d9970',
  '#2f6f9f', '#6b4fa0', '#8a8f98', '#3a3f4b',
];

const el = (id) => document.getElementById(id);

const canvas = el('grid');
const ctx = canvas.getContext('2d');

let cols = 16;
let rows = 16;
let pixels = new Array(cols * rows).fill(null);
let palette = DEFAULT_PALETTE.slice();
let color = '#111111';
let tool = 'pencil';
let showGrid = true;
let cellSize = 1;

const undoStack = [];
const redoStack = [];
let drawing = false;
let pendingBefore = null; // snapshot held until a drag actually changes a pixel

/* ---------- model ---------- */

const idx = (x, y) => y * cols + x;

function snapshot() {
  return { cols, rows, data: pixels.slice() };
}

function pushHistory(before) {
  undoStack.push(before);
  if (undoStack.length > MAX_HISTORY) undoStack.shift();
  redoStack.length = 0;
  refreshHistoryButtons();
}

function resize(nextCols, nextRows) {
  const next = new Array(nextCols * nextRows).fill(null);
  for (let y = 0; y < Math.min(rows, nextRows); y++) {
    for (let x = 0; x < Math.min(cols, nextCols); x++) {
      next[y * nextCols + x] = pixels[idx(x, y)];
    }
  }
  cols = nextCols;
  rows = nextRows;
  pixels = next;
  layout();
  draw();
  updateStatus();
}

function floodFill(x, y, nextColor) {
  const target = pixels[idx(x, y)];
  if (target === nextColor) return false;
  const queue = [[x, y]];
  while (queue.length) {
    const [cx, cy] = queue.pop();
    if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) continue;
    if (pixels[idx(cx, cy)] !== target) continue;
    pixels[idx(cx, cy)] = nextColor;
    queue.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
  }
  return true;
}

/* ---------- rendering ---------- */

function layout() {
  // Fit the longest edge into whatever room the stage has, so the canvas never
  // overflows a narrow window.
  const stage = document.querySelector('.stage');
  const available = Math.min(
    DISPLAY_MAX,
    Math.max(120, stage.clientWidth - 24),      // 24 = .canvas-wrap padding
    Math.max(120, window.innerHeight - 220)     // leave room for header + status
  );
  cellSize = Math.max(3, Math.floor(available / Math.max(cols, rows)));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(cols * cellSize * dpr);
  canvas.height = Math.round(rows * cellSize * dpr);
  canvas.style.width = cols * cellSize + 'px';
  canvas.style.height = rows * cellSize + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function draw() {
  ctx.clearRect(0, 0, cols * cellSize, rows * cellSize);

  // Checkerboard behind the art, so transparent cells read as transparent.
  const half = Math.max(2, Math.floor(cellSize / 2));
  for (let y = 0; y * half < rows * cellSize; y++) {
    for (let x = 0; x * half < cols * cellSize; x++) {
      ctx.fillStyle = (x + y) % 2 ? '#20242c' : '#282d37';
      ctx.fillRect(x * half, y * half, half, half);
    }
  }

  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const c = pixels[idx(x, y)];
      if (!c) continue;
      ctx.fillStyle = c;
      ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
    }
  }

  if (showGrid && cellSize >= 6) {
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= cols; x++) {
      ctx.moveTo(x * cellSize + 0.5, 0);
      ctx.lineTo(x * cellSize + 0.5, rows * cellSize);
    }
    for (let y = 0; y <= rows; y++) {
      ctx.moveTo(0, y * cellSize + 0.5);
      ctx.lineTo(cols * cellSize, y * cellSize + 0.5);
    }
    ctx.stroke();
  }
}

function updateStatus() {
  const filled = pixels.reduce((n, c) => (c ? n + 1 : n), 0);
  el('status').textContent = `${cols} × ${rows} · ${filled} pixel${filled === 1 ? '' : 's'} filled`;
  const scale = Number(el('scale').value);
  el('exportSize').textContent = `PNG will be ${cols * scale} × ${rows * scale} px`;
}

function refreshHistoryButtons() {
  el('undo').disabled = undoStack.length === 0;
  el('redo').disabled = redoStack.length === 0;
}

function renderPalette() {
  const wrap = el('swatches');
  wrap.textContent = '';
  palette.forEach((hex) => {
    const b = document.createElement('button');
    b.className = 'swatch' + (hex.toLowerCase() === color.toLowerCase() ? ' is-active' : '');
    b.style.background = hex;
    b.title = hex;
    b.setAttribute('aria-label', hex);
    b.addEventListener('click', () => setColor(hex));
    wrap.appendChild(b);
  });
}

function setColor(hex) {
  color = hex;
  el('picker').value = hex;
  el('currentColor').textContent = hex;
  if (tool === 'eraser' || tool === 'eyedropper') setTool('pencil');
  renderPalette();
}

function setTool(next) {
  tool = next;
  document.querySelectorAll('#tools .chip').forEach((chip) => {
    chip.classList.toggle('is-active', chip.dataset.tool === next);
  });
}

/* ---------- pointer input ---------- */

function cellFromEvent(event) {
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - rect.left) / cellSize);
  const y = Math.floor((event.clientY - rect.top) / cellSize);
  if (x < 0 || y < 0 || x >= cols || y >= rows) return null;
  return { x, y };
}

function paint(cell) {
  const current = pixels[idx(cell.x, cell.y)];
  const next = tool === 'eraser' ? null : color;
  if (current === next) return false;
  pixels[idx(cell.x, cell.y)] = next;
  return true;
}

canvas.addEventListener('pointerdown', (event) => {
  const cell = cellFromEvent(event);
  if (!cell) return;
  // Capture keeps a drag alive if the pointer leaves the canvas; not every
  // pointer id can be captured, and failing to is not worth aborting over.
  try { canvas.setPointerCapture(event.pointerId); } catch { /* not capturable */ }

  if (tool === 'eyedropper') {
    const hex = pixels[idx(cell.x, cell.y)];
    if (hex) setColor(hex);
    return;
  }

  const before = snapshot();
  const changed = tool === 'fill'
    ? floodFill(cell.x, cell.y, color)
    : paint(cell);

  if (changed) {
    pushHistory(before);
    draw();
    updateStatus();
  }
  // Pencil and eraser keep painting while the pointer is down; the whole drag
  // is one undo step, so the snapshot above covers it. If the first cell was
  // already the target colour nothing was recorded yet, so hold the snapshot
  // until some later cell in the drag does change.
  if (tool === 'pencil' || tool === 'eraser') {
    drawing = true;
    pendingBefore = changed ? null : before;
  }
});

canvas.addEventListener('pointermove', (event) => {
  if (!drawing) return;
  const cell = cellFromEvent(event);
  if (!cell) return;
  if (!paint(cell)) return;
  if (pendingBefore) {
    pushHistory(pendingBefore);
    pendingBefore = null;
  }
  draw();
  updateStatus();
});

function endStroke(event) {
  drawing = false;
  pendingBefore = null;
  if (event && canvas.hasPointerCapture?.(event.pointerId)) {
    canvas.releasePointerCapture(event.pointerId);
  }
}

canvas.addEventListener('pointerup', endStroke);
canvas.addEventListener('pointercancel', endStroke);

/* ---------- export ---------- */

function exportPng() {
  const scale = Number(el('scale').value);
  const out = document.createElement('canvas');
  out.width = cols * scale;
  out.height = rows * scale;
  const octx = out.getContext('2d');

  // Nothing is painted onto the background, so every untouched cell exports
  // as a fully transparent pixel.
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const c = pixels[idx(x, y)];
      if (!c) continue;
      octx.fillStyle = c;
      octx.fillRect(x * scale, y * scale, scale, scale);
    }
  }

  out.toBlob((blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pixel-art-${cols}x${rows}.png`;
    a.click();
    URL.revokeObjectURL(url);
  }, 'image/png');
}

/* ---------- controls ---------- */

el('resize').addEventListener('click', () => {
  const nextCols = clampDim(el('cols').value);
  const nextRows = clampDim(el('rows').value);
  el('cols').value = nextCols;
  el('rows').value = nextRows;
  if (nextCols === cols && nextRows === rows) return;
  pushHistory(snapshot());
  resize(nextCols, nextRows);
});

function clampDim(value) {
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return 16;
  return Math.min(MAX_DIM, Math.max(1, n));
}

el('presets').addEventListener('click', (event) => {
  const size = Number(event.target.dataset.size);
  if (!size) return;
  el('cols').value = size;
  el('rows').value = size;
  pushHistory(snapshot());
  resize(size, size);
});

el('tools').addEventListener('click', (event) => {
  const chip = event.target.closest('.chip');
  if (chip) setTool(chip.dataset.tool);
});

el('picker').addEventListener('input', (event) => setColor(event.target.value));

el('addSwatch').addEventListener('click', () => {
  const hex = el('picker').value.toLowerCase();
  if (!palette.some((p) => p.toLowerCase() === hex)) palette.push(hex);
  setColor(hex);
});

el('showGrid').addEventListener('change', (event) => {
  showGrid = event.target.checked;
  draw();
});

el('clear').addEventListener('click', () => {
  if (!pixels.some(Boolean)) return;
  pushHistory(snapshot());
  pixels = new Array(cols * rows).fill(null);
  draw();
  updateStatus();
});

el('undo').addEventListener('click', undo);
el('redo').addEventListener('click', redo);

function undo() {
  const before = undoStack.pop();
  if (!before) return;
  redoStack.push(snapshot());
  applyState(before);
}

function redo() {
  const next = redoStack.pop();
  if (!next) return;
  undoStack.push(snapshot());
  applyState(next);
}

function applyState(state) {
  const resized = state.cols !== cols || state.rows !== rows;
  cols = state.cols;
  rows = state.rows;
  pixels = state.data.slice();
  if (resized) {
    el('cols').value = cols;
    el('rows').value = rows;
    layout();
  }
  draw();
  updateStatus();
  refreshHistoryButtons();
}

window.addEventListener('resize', () => {
  layout();
  draw();
});

el('scale').addEventListener('change', updateStatus);
el('export').addEventListener('click', exportPng);

document.addEventListener('keydown', (event) => {
  if (event.target.matches('input, select, textarea')) return;
  const key = event.key.toLowerCase();
  if ((event.metaKey || event.ctrlKey) && key === 'z') {
    event.preventDefault();
    event.shiftKey ? redo() : undo();
    return;
  }
  const shortcuts = { b: 'pencil', e: 'eraser', g: 'fill', i: 'eyedropper' };
  if (shortcuts[key]) setTool(shortcuts[key]);
});

/* ---------- boot ---------- */

layout();
draw();
renderPalette();
setColor(color);
updateStatus();
refreshHistoryButtons();
