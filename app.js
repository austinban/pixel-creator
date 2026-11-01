// Pixel Creator - a grid of cells, each either a colour or transparent (null).
// No build step, no dependencies: the whole editor is this file.

const MAX_DIM = 128;
const DISPLAY_MAX = 560; // tallest the canvas gets, in CSS pixels
const DISPLAY_MAX_WIDE = 1000; // widest, so a 128-wide sheet still has usable cells
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
let bgMode = 'checker';   // 'checker' (transparent grid) or 'solid'
let bgColor = '#ffffff';
// A rectangular selection. Until it is moved its pixels are still in the grid; once
// moved they are lifted out into `cells` and float above it until dropped.
let sel = null;          // { x, y, w, h, mask, cells | null }: a bounding box and which of its cells are selected
let selDrag = null;      // the pointer interaction in progress: 'marquee' or 'move'
let clipboard = null;    // { x, y, w, h, cells } from the last copy or cut
let antsTimer = null;    // drives the moving dotted border
// True while there is work that has not been saved (to a copy) or exported.
let dirty = false;
let overlay = 'off';   // which neighbouring frame to lay over this one at 50%: off, prev, next or both
const ZOOMS = [0.5, 0.75, 1, 1.5, 2, 3];   // the steps the − and + buttons move between
const ZOOM_MIN = 10;                       // percent, as typed into the box
const ZOOM_MAX = 800;
let zoom = 1;                              // multiple of the size that fits the window; 1 is "fit"
let cellSize = 1;

let undoStack = [];   // swapped per frame while editing a sheet, so each frame has its own history
let redoStack = [];
let drawing = false;
let pendingBefore = null; // snapshot held until a drag actually changes a pixel

/* ---------- model ---------- */

const idx = (x, y) => y * cols + x;

function snapshot() {
  return { cols, rows, data: pixels.slice() };
}

function pushHistory(before) {
  dirty = true;
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
  const availableWidth = Math.min(DISPLAY_MAX_WIDE, Math.max(120, stage.clientWidth - 24));  // 24 = .canvas-wrap padding
  const availableHeight = Math.min(DISPLAY_MAX, Math.max(120, window.innerHeight - 220));    // room for header + status
  const fit = Math.min(availableWidth / cols, availableHeight / rows);
  cellSize = Math.max(3, Math.floor(fit * zoom));
  el('zoomPct').value = Math.round(zoom * 100);
  el('zoomOut').disabled = zoom * 100 <= ZOOM_MIN;
  el('zoomIn').disabled = zoom * 100 >= ZOOM_MAX;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(cols * cellSize * dpr);
  canvas.height = Math.round(rows * cellSize * dpr);
  canvas.style.width = cols * cellSize + 'px';
  canvas.style.height = rows * cellSize + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function draw() {
  ctx.clearRect(0, 0, cols * cellSize, rows * cellSize);

  // Behind the art: a solid colour, or a checkerboard one square per cell so the
  // squares line up with the pixels. Display only; exports stay transparent.
  if (bgMode === 'solid') {
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, cols * cellSize, rows * cellSize);
  } else {
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        ctx.fillStyle = (x + y) % 2 ? '#20242c' : '#282d37';
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
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

  // Lifted pixels float above the grid until they are dropped.
  if (sel && sel.cells) {
    for (let j = 0; j < sel.h; j++) {
      for (let i = 0; i < sel.w; i++) {
        const c = sel.cells[j * sel.w + i];
        const x = sel.x + i;
        const y = sel.y + j;
        if (!c || x < 0 || y < 0 || x >= cols || y >= rows) continue;
        ctx.fillStyle = c;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
    }
  }

  // The neighbouring frame(s) over the top at half strength, so the difference
  // between frames shows exactly. Neighbours wrap, as the animation does.
  if (overlay !== 'off' && frames.length > 1) {
    const n = frames.length;
    const ghosts = new Set();
    if (overlay === 'prev' || overlay === 'both') ghosts.add((current - 1 + n) % n);
    if (overlay === 'next' || overlay === 'both') ghosts.add((current + 1) % n);
    ghosts.delete(current);
    ctx.globalAlpha = 0.5;
    ghosts.forEach((g) => {
      const frame = frames[g];
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          const c = frame[y * cols + x];
          if (!c) continue;
          ctx.fillStyle = c;
          ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
      }
    });
    ctx.globalAlpha = 1;
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

  if (sel) drawAnts();
  if (sel && sel.cells && frames.length) drawThumb(current);
}

// The dotted border: white and black dashes that crawl, so it reads on any colour.
function drawAnts() {
  const offset = (performance.now() / 70) % 8;
  ctx.save();
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  // Every edge between a selected cell and an unselected one, as one path.
  const path = new Path2D();
  const has = (i, j) => i >= 0 && j >= 0 && i < sel.w && j < sel.h && sel.mask[j * sel.w + i];
  for (let j = 0; j < sel.h; j++) {
    for (let i = 0; i < sel.w; i++) {
      if (!has(i, j)) continue;
      const x = (sel.x + i) * cellSize;
      const y = (sel.y + j) * cellSize;
      if (!has(i, j - 1)) { path.moveTo(x, y); path.lineTo(x + cellSize, y); }
      if (!has(i, j + 1)) { path.moveTo(x, y + cellSize); path.lineTo(x + cellSize, y + cellSize); }
      if (!has(i - 1, j)) { path.moveTo(x, y); path.lineTo(x, y + cellSize); }
      if (!has(i + 1, j)) { path.moveTo(x + cellSize, y); path.lineTo(x + cellSize, y + cellSize); }
    }
  }
  ctx.strokeStyle = '#ffffff';
  ctx.lineDashOffset = -offset;
  ctx.stroke(path);
  ctx.strokeStyle = '#000000';
  ctx.lineDashOffset = -offset + 4;
  ctx.stroke(path);
  ctx.restore();
}

function ensureAnts() {
  if (antsTimer || !sel) return;
  const tick = () => {
    if (!sel) { antsTimer = null; return; }
    draw();
    antsTimer = setTimeout(tick, 80);
  };
  antsTimer = setTimeout(tick, 80);
}

function updateStatus() {
  const filled = pixels.reduce((n, c) => (c ? n + 1 : n), 0);
  const where = frames.length > 1 ? `frame ${current + 1} of ${frames.length} · ` : '';
  el('status').textContent = `${where}${cols} × ${rows} · ${filled} pixel${filled === 1 ? '' : 's'} filled`;
  const scale = Number(el('scale').value);
  el('exportSize').textContent = editing
    ? `Saves back as a ${editing.w} × ${editing.h} sheet`
    : `PNG will be ${cols * scale} × ${rows * scale} px`;
  drawThumb(current);
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
  if (next !== 'select') commitSelection();
  tool = next;
  el('selectHint').hidden = next !== 'select';
  canvas.style.cursor = 'crosshair';
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

// The cell under the pointer even when it is off the grid, so a selection can be
// dragged partly (or wholly) past the edge.
function rawCellFromEvent(event) {
  const rect = canvas.getBoundingClientRect();
  return { x: Math.floor((event.clientX - rect.left) / cellSize), y: Math.floor((event.clientY - rect.top) / cellSize) };
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
  stopPlaying();   // drawing happens on the frame you are looking at

  if (tool === 'select') {
    // Cmd/Ctrl (or Shift) + drag adds another area to what is already selected.
    const add = event.metaKey || event.ctrlKey || event.shiftKey;
    const onSelected = selHas(cell.x, cell.y);   // add-click on a selected cell takes it back out
    if (add && sel) {
      if (sel.cells) { stampInto(pixels); sel.cells = null; }   // drop what was floating, keep the area
      selDrag = { mode: 'marquee', add: true, sub: onSelected, base: { x: sel.x, y: sel.y, w: sel.w, h: sel.h, mask: sel.mask.slice() }, ax: cell.x, ay: cell.y, moved: false };
    } else if (selHas(cell.x, cell.y)) {
      selDrag = { mode: 'move', ox: cell.x - sel.x, oy: cell.y - sel.y, moved: false };
    } else {
      commitSelection();
      selDrag = { mode: 'marquee', add: false, base: null, ax: cell.x, ay: cell.y, moved: false };
    }
    // A click selects the cell it lands on; dragging then stretches that into a rectangle.
    if (selDrag.mode === 'marquee') {
      const first = { x: cell.x, y: cell.y, w: 1, h: 1 };
      sel = selDrag.sub ? subtractSel(selDrag.base, first) : unionSel(selDrag.base, first);
      ensureAnts();
      draw();
    }
    return;
  }
  commitSelection();
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
  if (selDrag) { selectMove(event); return; }
  if (tool === 'select') {
    const over = cellFromEvent(event);
    canvas.style.cursor = over && selHas(over.x, over.y) ? 'move' : 'crosshair';
    return;
  }
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
  if (selDrag) {
    selDrag = null;
    draw();
  }
  drawing = false;
  pendingBefore = null;
  if (event && canvas.hasPointerCapture?.(event.pointerId)) {
    canvas.releasePointerCapture(event.pointerId);
  }
}

canvas.addEventListener('pointerup', endStroke);
canvas.addEventListener('pointercancel', endStroke);

/* ---------- selection ---------- */

function selectMove(event) {
  const raw = rawCellFromEvent(event);
  if (selDrag.mode === 'marquee') {
    const clampX = (v) => Math.min(cols - 1, Math.max(0, v));
    const clampY = (v) => Math.min(rows - 1, Math.max(0, v));
    const x0 = Math.min(clampX(selDrag.ax), clampX(raw.x));
    const y0 = Math.min(clampY(selDrag.ay), clampY(raw.y));
    const x1 = Math.max(clampX(selDrag.ax), clampX(raw.x));
    const y1 = Math.max(clampY(selDrag.ay), clampY(raw.y));
    if (raw.x !== selDrag.ax || raw.y !== selDrag.ay) selDrag.moved = true;
    const rect = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 };
    sel = selDrag.sub ? subtractSel(selDrag.base, rect) : unionSel(selDrag.base, rect);
    ensureAnts();
    draw();
    return;
  }
  const nx = raw.x - selDrag.ox;
  const ny = raw.y - selDrag.oy;
  if (nx === sel.x && ny === sel.y) return;
  liftSelection();
  sel.x = nx;
  sel.y = ny;
  selDrag.moved = true;
  draw();
}

// A selection is a bounding box plus a mask saying which of its cells are in it,
// so adding areas can make shapes that are not rectangles.
function selHas(cx, cy) {
  if (!sel) return false;
  const i = cx - sel.x;
  const j = cy - sel.y;
  return i >= 0 && j >= 0 && i < sel.w && j < sel.h && sel.mask[j * sel.w + i];
}

// The base selection (or nothing) plus a rectangle.
function unionSel(base, rect) {
  if (!base) return { ...rect, mask: new Array(rect.w * rect.h).fill(true), cells: null };
  const x0 = Math.min(base.x, rect.x);
  const y0 = Math.min(base.y, rect.y);
  const x1 = Math.max(base.x + base.w, rect.x + rect.w);
  const y1 = Math.max(base.y + base.h, rect.y + rect.h);
  const w = x1 - x0;
  const h = y1 - y0;
  const mask = new Array(w * h).fill(false);
  for (let j = 0; j < base.h; j++) {
    for (let i = 0; i < base.w; i++) {
      if (base.mask[j * base.w + i]) mask[(base.y - y0 + j) * w + (base.x - x0 + i)] = true;
    }
  }
  for (let j = 0; j < rect.h; j++) {
    for (let i = 0; i < rect.w; i++) mask[(rect.y - y0 + j) * w + (rect.x - x0 + i)] = true;
  }
  return { x: x0, y: y0, w, h, mask, cells: null };
}

// The base selection minus a rectangle, trimmed to what is left; null when nothing is.
function subtractSel(base, rect) {
  const mask = base.mask.slice();
  for (let j = 0; j < base.h; j++) {
    for (let i = 0; i < base.w; i++) {
      const x = base.x + i;
      const y = base.y + j;
      if (x >= rect.x && x < rect.x + rect.w && y >= rect.y && y < rect.y + rect.h) mask[j * base.w + i] = false;
    }
  }
  let x0 = base.w, y0 = base.h, x1 = -1, y1 = -1;
  for (let j = 0; j < base.h; j++) {
    for (let i = 0; i < base.w; i++) {
      if (!mask[j * base.w + i]) continue;
      x0 = Math.min(x0, i); y0 = Math.min(y0, j); x1 = Math.max(x1, i); y1 = Math.max(y1, j);
    }
  }
  if (x1 < 0) return null;
  const w = x1 - x0 + 1;
  const h = y1 - y0 + 1;
  const trimmed = new Array(w * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) trimmed[j * w + i] = mask[(y0 + j) * base.w + x0 + i];
  }
  return { x: base.x + x0, y: base.y + y0, w, h, mask: trimmed, cells: null };
}

// The selected pixels, with empty slots where the shape has a gap.
function extractRect(r) {
  const cells = [];
  for (let j = 0; j < r.h; j++) {
    for (let i = 0; i < r.w; i++) {
      const x = r.x + i;
      const y = r.y + j;
      cells.push(r.mask[j * r.w + i] && x >= 0 && y >= 0 && x < cols && y < rows ? pixels[idx(x, y)] : null);
    }
  }
  return cells;
}

// Empty every selected cell of the grid.
function clearSelected() {
  for (let j = 0; j < sel.h; j++) {
    for (let i = 0; i < sel.w; i++) {
      if (sel.mask[j * sel.w + i]) pixels[idx(sel.x + i, sel.y + j)] = null;
    }
  }
}

// Take the selected pixels out of the grid so they can float. The whole move,
// from here to the drop, is one undo step.
function liftSelection() {
  if (!sel || sel.cells) return;
  pushHistory(snapshot());
  sel.cells = extractRect(sel);
  clearSelected();
}

// Floating pixels written into a grid. Empty cells never erase what is underneath.
function stampInto(target) {
  for (let j = 0; j < sel.h; j++) {
    for (let i = 0; i < sel.w; i++) {
      const c = sel.cells[j * sel.w + i];
      const x = sel.x + i;
      const y = sel.y + j;
      if (c && x >= 0 && y >= 0 && x < cols && y < rows) target[y * cols + x] = c;
    }
  }
  return target;
}

// The grid as it looks right now, floating pixels included.
function composed() {
  return sel && sel.cells ? stampInto(pixels.slice()) : pixels;
}

// Drop the selection where it is. Safe to call whenever a selection might be live.
function commitSelection() {
  if (!sel) return;
  if (sel.cells) stampInto(pixels);
  sel = null;
  selDrag = null;
  draw();
  updateStatus();
}

function deleteSelection() {
  if (!sel) return;
  if (!sel.cells) {
    pushHistory(snapshot());
    clearSelected();
  }
  sel = null;   // lifted pixels are simply not dropped; their undo step already exists
  draw();
  updateStatus();
}

function copySelection() {
  if (!sel) return;
  clipboard = { x: sel.x, y: sel.y, w: sel.w, h: sel.h, mask: sel.mask.slice(), cells: sel.cells ? sel.cells.slice() : extractRect(sel) };
}

// Pasted pixels float where they were copied from, so copying on one frame and
// pasting on the next lands them in the same place, ready to nudge.
function pasteClipboard() {
  if (!clipboard) return;
  commitSelection();
  setTool('select');
  pushHistory(snapshot());
  sel = {
    x: Math.max(0, Math.min(clipboard.x, cols - clipboard.w)),
    y: Math.max(0, Math.min(clipboard.y, rows - clipboard.h)),
    w: clipboard.w, h: clipboard.h, mask: clipboard.mask.slice(), cells: clipboard.cells.slice(),
  };
  ensureAnts();
  draw();
}

function nudgeSelection(dx, dy) {
  liftSelection();
  sel.x += dx;
  sel.y += dy;
  draw();
}

/* ---------- export ---------- */

// One PNG of the given frames laid side by side. Nothing is painted onto the
// background, so every untouched cell exports as a fully transparent pixel.
function savePng(list, filename) {
  const scale = Number(el('scale').value);
  const out = document.createElement('canvas');
  out.width = cols * list.length * scale;
  out.height = rows * scale;
  const octx = out.getContext('2d');
  list.forEach((frame, n) => {
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const c = frame[y * cols + x];
        if (!c) continue;
        octx.fillStyle = c;
        octx.fillRect((n * cols + x) * scale, y * scale, scale, scale);
      }
    }
  });
  out.toBlob((blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, 'image/png');
}

function exportPng() {
  commitSelection();
  if (frames.length < 2) dirty = false;
  savePng([pixels], `pixel-art-${cols}x${rows}.png`);
}

// Every frame in a row, left to right, in order.
function exportSheet() {
  commitSelection();
  dirty = false;
  frames[current] = pixels;
  savePng(frames, `pixel-art-${cols}x${rows}-${frames.length}-frames.png`);
}

/* ---------- import ---------- */

const hex2 = (n) => n.toString(16).padStart(2, '0');

async function importImage(file) {
  commitSelection();
  const note = el('importNote');
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    note.textContent = `Couldn't read ${file.name} as an image.`;
    return;
  }
  if (bitmap.width > MAX_DIM || bitmap.height > MAX_DIM) {
    note.textContent = `${file.name} is ${bitmap.width} × ${bitmap.height}; the limit is ${MAX_DIM} × ${MAX_DIM}.`;
    return;
  }

  const probe = document.createElement('canvas');
  probe.width = bitmap.width;
  probe.height = bitmap.height;
  const pctx = probe.getContext('2d', { willReadFrequently: true });
  pctx.drawImage(bitmap, 0, 0);
  const { data } = pctx.getImageData(0, 0, bitmap.width, bitmap.height);

  // Cells are either a colour or empty, so partial transparency has to snap
  // one way: half-opaque and up counts as painted.
  const next = new Array(bitmap.width * bitmap.height).fill(null);
  const found = [];
  for (let i = 0; i < next.length; i++) {
    const o = i * 4;
    if (data[o + 3] < 128) continue;
    const hex = `#${hex2(data[o])}${hex2(data[o + 1])}${hex2(data[o + 2])}`;
    next[i] = hex;
    if (!found.includes(hex)) found.push(hex);
  }

  pushHistory(snapshot());
  cols = bitmap.width;
  rows = bitmap.height;
  pixels = next;
  el('cols').value = cols;
  el('rows').value = rows;
  found.forEach((hex) => {
    if (!palette.some((p) => p.toLowerCase() === hex)) palette.push(hex);
  });
  layout();
  draw();
  renderPalette();
  updateStatus();
  note.textContent = `Imported ${file.name}: ${cols} × ${rows}, ${found.length} colours added to the palette.`;
}

el('import').addEventListener('click', () => el('importFile').click());
el('importFile').addEventListener('change', (event) => {
  const [file] = event.target.files;
  event.target.value = ''; // lets the same file be chosen twice in a row
  if (file) importImage(file);
});

/* ---------- editing a character's pose ---------- */

const STORE_KEY = 'pixel-creator.characters';
const HANDOFF_KEY = 'pixel-creator.handoff';
let editing = null; // the pose handed over from the characters page, while there is one

function startEditing() {
  if (new URLSearchParams(window.location.search).get('edit') !== '1') return;
  let handoff = null;
  try { handoff = JSON.parse(localStorage.getItem(HANDOFF_KEY)); } catch { /* unreadable */ }
  // The size limit is per frame: a sheet of several frames can be wider than the grid.
  const layoutOf = (n, total) => (Number.isInteger(n) && n > 0 && total % n === 0 ? n : 1);
  const valid = handoff && Number.isInteger(handoff.w) && Number.isInteger(handoff.h)
    && handoff.w > 0 && handoff.h > 0 && Array.isArray(handoff.pixels)
    && handoff.pixels.length === handoff.w * handoff.h
    && handoff.w / layoutOf(handoff.frameCols, handoff.w) <= MAX_DIM
    && handoff.h / layoutOf(handoff.frameRows, handoff.h) <= MAX_DIM;
  el('editBanner').hidden = false;
  if (!valid) {
    el('editTitle').textContent = 'Nothing to edit';
    el('editNote').textContent = 'Open a pose from the characters page with "Edit in editor".';
    el('saveBack').hidden = true;
    return;
  }

  editing = handoff;

  // Split the sheet into its frames. One that doesn't say how it is laid out is a
  // single frame the size of the whole sheet.
  const fc = layoutOf(handoff.frameCols, handoff.w);
  const fr = layoutOf(handoff.frameRows, handoff.h);
  editing.frameCols = fc;
  editing.frameRows = fr;
  const fw = handoff.w / fc;
  const fh = handoff.h / fr;
  frames = [];
  for (let i = 0; i < fc * fr; i++) {
    const ox = (i % fc) * fw;
    const oy = Math.floor(i / fc) * fh;
    const frame = new Array(fw * fh);
    for (let y = 0; y < fh; y++) {
      for (let x = 0; x < fw; x++) frame[y * fw + x] = handoff.pixels[(oy + y) * handoff.w + ox + x];
    }
    frames.push(frame);
  }
  histories = frames.map(() => ({ undo: [], redo: [] }));
  current = 0;
  cols = fw;
  rows = fh;
  pixels = frames[0];
  undoStack = histories[0].undo;
  redoStack = histories[0].redo;
  el('cols').value = cols;
  el('rows').value = rows;
  el('editTitle').textContent = `${handoff.name} · ${handoff.label}`;
  // Whatever opened the editor says where its copies live and where to go back to.
  el('editBack').href = handoff.returnUrl || 'characters.html';
  el('editBack').textContent = handoff.returnLabel || 'Back to characters';
  [...new Set(handoff.pixels.filter(Boolean))].forEach((hex) => {
    if (!palette.some((p) => p.toLowerCase() === hex)) palette.push(hex);
  });
  buildFrameBar();

  // A saved pose has to match the sheet it came from, so the grid is fixed.
  ['cols', 'rows', 'resize', 'import'].forEach((id) => { el(id).disabled = true; });
  document.querySelectorAll('#presets .chip').forEach((chip) => { chip.disabled = true; });
}

/* ---------- frames ---------- */

let frames = [];       // every frame of the pose being edited, each cols × rows
let histories = [];    // undo / redo per frame
let current = 0;
let playTimer = null;

function buildFrameBar() {
  // A pose from the characters page keeps its sheet's layout, so frames can't be
  // added or removed there; freeform drawings always show the bar.
  el('frameBar').hidden = Boolean(editing) && frames.length < 2;
  // With a single frame only "Add frame" shows; the rest appears once there are several.
  document.querySelectorAll('.frame-multi').forEach((node) => { node.hidden = frames.length < 2; });
  el('frameAdd').hidden = Boolean(editing);
  el('frameDelete').hidden = Boolean(editing) || frames.length < 2;
  el('exportSheet').hidden = Boolean(editing) || frames.length < 2;
  el('exportSheet').title = `All ${frames.length} frames in one row`;
  lockSize();
  const strip = el('frameStrip');
  strip.textContent = '';
  frames.forEach((_, i) => {
    const b = document.createElement('button');
    b.className = 'frame-thumb';
    b.title = `Frame ${i + 1}`;
    b.setAttribute('aria-label', `Frame ${i + 1}`);
    const c = document.createElement('canvas');
    c.width = cols;
    c.height = rows;
    b.appendChild(c);
    b.addEventListener('click', () => { stopPlaying(); setFrame(i); });
    strip.appendChild(b);
  });
  frames.forEach((_, i) => drawThumb(i));
  markFrame();
}

function drawThumb(i) {
  const c = el('frameStrip').children[i] && el('frameStrip').children[i].firstChild;
  if (!c) return;
  if (c.width !== cols || c.height !== rows) { c.width = cols; c.height = rows; }
  const tctx = c.getContext('2d');
  tctx.clearRect(0, 0, c.width, c.height);
  const data = i === current ? composed() : frames[i];
  data.forEach((hex, n) => {
    if (!hex) return;
    tctx.fillStyle = hex;
    tctx.fillRect(n % cols, Math.floor(n / cols), 1, 1);
  });
}

function markFrame() {
  el('frameCopyPrev').disabled = current === 0;
  [...el('frameStrip').children].forEach((b, i) => b.classList.toggle('is-active', i === current));
  el('frameLabel').textContent = `Frame ${current + 1} of ${frames.length}`;
}

// Every frame shares one size, so it can't change while there are several.
function lockSize() {
  if (editing) return;
  const locked = frames.length > 1;
  ['cols', 'rows', 'resize', 'import'].forEach((id) => { el(id).disabled = locked; });
  document.querySelectorAll('#presets .chip').forEach((chip) => { chip.disabled = locked; });
  el('importNote').textContent = locked
    ? 'Canvas size is shared by all frames. Delete frames down to one to resize or import.'
    : 'Loads at 1 image pixel per cell, up to 128 × 128.';
}

// A new blank frame after the current one, which becomes the one you are editing.
function addFrame() {
  dirty = true;
  commitSelection();
  stopPlaying();
  frames[current] = pixels;
  const at = current + 1;
  frames.splice(at, 0, new Array(cols * rows).fill(null));
  histories.splice(at, 0, { undo: [], redo: [] });
  buildFrameBar();
  setFrame(at);
}

// Replace this frame with a copy of the one before it, as a starting point to change.
function copyPrevious() {
  if (frames.length < 2 || current === 0) return;
  commitSelection();
  stopPlaying();
  pushHistory(snapshot());
  pixels = frames[current - 1].slice();
  draw();
  updateStatus();
}

function deleteFrame() {
  if (editing || frames.length < 2) return;
  commitSelection();
  dirty = true;
  if (pixels.some(Boolean) && !window.confirm(`Delete frame ${current + 1}?`)) return;
  stopPlaying();
  frames.splice(current, 1);
  histories.splice(current, 1);
  current = Math.min(current, frames.length - 1);
  pixels = frames[current];
  undoStack = histories[current].undo;
  redoStack = histories[current].redo;
  buildFrameBar();
  draw();
  updateStatus();
  refreshHistoryButtons();
}

function setFrame(i) {
  const next = (i + frames.length) % frames.length;
  if (next === current) return;
  commitSelection();
  drawing = false;
  pendingBefore = null;
  frames[current] = pixels;
  current = next;
  pixels = frames[current];
  undoStack = histories[current].undo;
  redoStack = histories[current].redo;
  markFrame();
  draw();
  updateStatus();
  refreshHistoryButtons();
}

function stopPlaying() {
  if (!playTimer) return;
  clearInterval(playTimer);
  playTimer = null;
  el('framePlay').textContent = 'Play';
}

function startPlaying() {
  stopPlaying();
  if (frames.length < 2) return;
  el('framePlay').textContent = 'Pause';
  playTimer = setInterval(() => setFrame(current + 1), 1000 / Number(el('fps').value));
}

el('overlayMode').addEventListener('change', (event) => {
  overlay = event.target.value;
  draw();
});

el('frameAdd').addEventListener('click', addFrame);
el('frameDelete').addEventListener('click', deleteFrame);
el('frameCopyPrev').addEventListener('click', copyPrevious);
el('exportSheet').addEventListener('click', exportSheet);
el('framePrev').addEventListener('click', () => { stopPlaying(); setFrame(current - 1); });
el('frameNext').addEventListener('click', () => { stopPlaying(); setFrame(current + 1); });
el('framePlay').addEventListener('click', () => (playTimer ? stopPlaying() : startPlaying()));
el('fps').addEventListener('change', () => { if (playTimer) startPlaying(); });

// Pixels that still match one of the character's colours go back as that colour's
// role, so recolouring the character recolours them too; the rest are saved as drawn.
function saveToCharacter() {
  if (!editing) return;
  commitSelection();
  const note = el('editNote');
  if (cols !== editing.w / editing.frameCols || rows !== editing.h / editing.frameRows) {
    note.textContent = `The grid has to stay ${editing.w / editing.frameCols} × ${editing.h / editing.frameRows}.`;
    return;
  }
  frames[current] = pixels;
  let stored = null;
  const storeKey = editing.store || STORE_KEY;
  try { stored = JSON.parse(localStorage.getItem(storeKey)); } catch { /* unreadable */ }
  if (!stored || !Array.isArray(stored.items)) stored = { version: storeKey === STORE_KEY ? 3 : 1, items: [] };
  let item = editing.instanceId && stored.items.find((i) => i.id === editing.instanceId);
  if (!item && editing.instanceId) {
    note.textContent = 'That copy no longer exists. Open it again from where you started.';
    return;
  }
  // Opened from a base: a base never changes, so the first save makes a copy of it
  // (colours left out, so it starts from the base's own) and later saves go there.
  let made = false;
  if (!item) {
    const id = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    item = { id, name: `${editing.name} copy`, [editing.baseField || 'base']: editing.baseId, hue: {}, colors: {}, edits: {} };
    stored.items.push(item);
    editing.instanceId = id;
    made = true;
  }

  const roleOf = {};
  Object.entries(editing.roleColors).forEach(([char, hex]) => {
    if (!(hex.toLowerCase() in roleOf)) roleOf[hex.toLowerCase()] = char;
  });
  // Put the frames back together into the sheet, in the order they came out.
  const cells = new Array(editing.w * editing.h).fill('');
  frames.forEach((frame, i) => {
    const ox = (i % editing.frameCols) * cols;
    const oy = Math.floor(i / editing.frameCols) * rows;
    frame.forEach((c, n) => {
      if (!c) return;
      cells[(oy + Math.floor(n / cols)) * editing.w + ox + (n % cols)] = roleOf[c.toLowerCase()] || c.toLowerCase();
    });
  });
  item.edits = item.edits || {};
  item.edits[editing.unitId || editing.poseId] = { w: editing.w, h: editing.h, cells };
  stored.current = item.id;
  try {
    localStorage.setItem(storeKey, JSON.stringify(stored));
  } catch {
    note.textContent = 'Could not save: the browser storage is full or blocked.';
    return;
  }
  dirty = false;
  note.textContent = made ? `Saved to a new copy, "${item.name}". The base is unchanged.` : `Saved to ${item.name}.`;
}

el('saveBack').addEventListener('click', saveToCharacter);

/* ---------- controls ---------- */

el('resize').addEventListener('click', () => {
  commitSelection();
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
  commitSelection();
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

el('bgMode').addEventListener('change', (event) => {
  bgMode = event.target.value;
  el('bgColor').hidden = bgMode !== 'solid';
  draw();
});

el('bgColor').addEventListener('input', (event) => {
  bgColor = event.target.value;
  draw();
});

function setZoom(next) {
  zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(next * 100))) / 100;
  layout();
  draw();
}

// − and + move to the next preset, wherever a typed value has left the zoom.
const stepZoom = (dir) => setZoom(dir > 0
  ? ZOOMS.find((z) => z > zoom + 1e-6) || ZOOM_MAX / 100
  : [...ZOOMS].reverse().find((z) => z < zoom - 1e-6) || ZOOM_MIN / 100);

el('zoomOut').addEventListener('click', () => stepZoom(-1));
el('zoomIn').addEventListener('click', () => stepZoom(1));
el('zoomFit').addEventListener('click', () => setZoom(1));
el('zoomPct').addEventListener('change', (event) => {
  const pct = Number(event.target.value);
  setZoom(Number.isFinite(pct) && pct > 0 ? pct / 100 : zoom);   // junk snaps back
});

el('clear').addEventListener('click', () => {
  commitSelection();
  if (!pixels.some(Boolean)) return;
  pushHistory(snapshot());
  pixels = new Array(cols * rows).fill(null);
  draw();
  updateStatus();
});

el('undo').addEventListener('click', undo);
el('redo').addEventListener('click', redo);

const sizeLocked = (state) => frames.length > 1 && (state.cols !== cols || state.rows !== rows);

function undo() {
  commitSelection();
  const before = undoStack.pop();
  if (!before || sizeLocked(before)) { refreshHistoryButtons(); return; }
  redoStack.push(snapshot());
  applyState(before);
}

function redo() {
  commitSelection();
  const next = redoStack.pop();
  if (!next || sizeLocked(next)) { refreshHistoryButtons(); return; }
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
  if (sel && !event.metaKey && !event.ctrlKey && !event.altKey) {
    const dirs = { arrowleft: [-1, 0], arrowright: [1, 0], arrowup: [0, -1], arrowdown: [0, 1] };
    if (key === 'escape' || key === 'enter') { event.preventDefault(); commitSelection(); return; }
    if (key === 'delete' || key === 'backspace') { event.preventDefault(); deleteSelection(); return; }
    if (dirs[key]) { event.preventDefault(); nudgeSelection(...dirs[key]); return; }
  }
  if (frames.length > 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
    if (key === 'arrowleft' || key === 'a') { event.preventDefault(); stopPlaying(); setFrame(current - 1); return; }
    if (key === 'arrowright' || key === 'd') { event.preventDefault(); stopPlaying(); setFrame(current + 1); return; }
    if (key === 'o') {
      const modes = ['off', 'prev', 'next', 'both'];
      overlay = modes[(modes.indexOf(overlay) + 1) % modes.length];
      el('overlayMode').value = overlay;
      draw();
      return;
    }
    if (key === 'p' || key === ' ') {
      // Space would also "click" a focused button on release, so drop the focus first.
      if (key === ' ') { event.preventDefault(); document.activeElement.blur(); }
      playTimer ? stopPlaying() : startPlaying();
      return;
    }
  }
  if (!event.metaKey && !event.ctrlKey && !event.altKey) {
    if (key === '-') { stepZoom(-1); return; }
    if (key === '=' || key === '+') { stepZoom(1); return; }
  }
  const mod = event.metaKey || event.ctrlKey;
  if (mod && (key === 'c' || key === 'x') && sel) {
    event.preventDefault();
    copySelection();
    if (key === 'x') deleteSelection();
    return;
  }
  if (mod && key === 'v' && clipboard) {
    event.preventDefault();
    pasteClipboard();
    return;
  }
  const shortcuts = { b: 'pencil', e: 'eraser', g: 'fill', i: 'eyedropper', s: 'select' };
  if (shortcuts[key] && !mod) setTool(shortcuts[key]);
});

/* ---------- leaving the page ---------- */

// Nothing here saves on its own, so ask before a link, reload or closed tab throws
// away work. Browsers show their own wording for this prompt.
window.addEventListener('beforeunload', (event) => {
  if (!dirty) return;
  event.preventDefault();
  event.returnValue = '';
});

/* ---------- boot ---------- */

startEditing();
if (!editing) {
  frames = [pixels];
  histories = [{ undo: undoStack, redo: redoStack }];
  current = 0;
  buildFrameBar();
}
layout();
draw();
renderPalette();
setColor(color);
updateStatus();
refreshHistoryButtons();
