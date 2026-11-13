// Terrain - lays the ground tiles out as an isometric map. Land is a mix of grass
// cubes with trees, bushes and rocks scattered over it; water is a lake whose edge
// tiles are picked so the foam sits on the sides that touch land.
//
// Every tile is a 32 x 32 cube drawn on the same bottom corner. Its top face is a
// diamond 32 wide and 16 tall, so a step along either grid axis moves the drawing
// 16 across and 8 down.

const STEP_X = 16;
const STEP_Y = 8;
const TILE = 32;
const HEADROOM = 40;        // room above the map for trees and the like
const LEVEL_PX = 16;        // one level of height
const TOP_CENTRE_Y = 8;     // the middle of a cube's top face, from the top of its tile
const VIEW_SCALE = 4;        // the most the preview is blown up

const el = (id) => document.getElementById(id);
const data = window.ASSETS;
const SETS = window.SETS;

if (!data || !SETS) {
  el('missing').hidden = false;
} else {
  boot();
}

function boot() {
  el('app').hidden = false;

  const rgbOf = {};
  data.roles.forEach((r) => { rgbOf[r.char] = [1, 3, 5].map((i) => parseInt(r.hex.slice(i, i + 2), 16)); });
  const byId = Object.fromEntries(data.assets.map((a) => [a.id, a]));

  // The set picks the ground sheet, the grass, what is scattered over it and which rocks stand on it (assets/sets.js, from tools/sets.py). The corrupted
  // sheet has the same layout as the plain one, cell for cell, so a table of cells names the same piece on either.
  const setOf = () => SETS.sets[el('set').value] || SETS.sets[Object.keys(SETS.sets)[0]];
  const sheetOf = (set) => SETS.grounds[set.ground].sheet;
  const exists = (id) => Boolean(byId[id]);
  // A group's weight is shared out over its pieces, so a group of seven props is no likelier than a group of two.
  const tableOf = (set, layer) => set[layer].groups.flatMap((g) => {
    const ids = SETS.groups[g.group].ids.filter(exists);
    return ids.map((id) => [id, g.weight / ids.length]);
  });
  const grassOf = (set) => set.grass.filter((g) => exists(g.id)).map((g) => [g.id, g.weight]);

  // Water with foam on the sides that meet land. Each entry is the sides that have
  // foam, as a set of "NW" "NE" "SW" "SE" (screen directions); level water is a full
  // cube, sunken water sits eight rows lower.
  const WATER = {
    flush: [
      ['ground-0-2', []], ['ground-3-2', ['NE']], ['ground-2-3', ['NW']], ['ground-4-3', ['SE']], ['ground-3-4', ['SW']],
      ['ground-2-2', ['NW', 'NE']], ['ground-4-2', ['NE', 'SE']], ['ground-2-4', ['NW', 'SW']], ['ground-4-4', ['SW', 'SE']],
    ],
    sunken: [
      ['ground-1-2', []], ['ground-6-2', ['NE']], ['ground-5-3', ['NW']], ['ground-7-3', ['SE']], ['ground-6-4', ['SW']],
      ['ground-5-2', ['NW', 'NE']], ['ground-7-2', ['NE', 'SE']], ['ground-5-4', ['NW', 'SW']], ['ground-7-4', ['SW', 'SE']],
    ],
  };
  // The same water on the other sheet: ids differ only by the sheet's name.
  const waterOf = (set, level) => WATER[level].map(([id, sides]) => [id.replace(/^ground-/, `${sheetOf(set)}-`), sides]).filter(([id]) => exists(id));
  // Which neighbour sits on which side of a cell (x, y of the map grid).
  const SIDES = { NW: [-1, 0], NE: [0, -1], SW: [0, 1], SE: [1, 0] };

  /* ---------- drawing ---------- */

  // One frame of an asset (the bridge has four), drawn as is or flipped left to right.
  const frameCache = {};
  function frameCanvas(id, index, flip) {
    const key = `${id}:${index}:${flip}`;
    if (frameCache[key]) return frameCache[key];
    const asset = byId[id];
    const c = document.createElement('canvas');
    c.width = asset.w;
    c.height = asset.h;
    const ctx = c.getContext('2d');
    const image = ctx.createImageData(asset.w, asset.h);
    asset.frames[index].forEach((line, y) => {
      for (let x = 0; x < asset.w; x++) {
        const rgb = rgbOf[line[x]];
        if (rgb) image.data.set([rgb[0], rgb[1], rgb[2], 255], (y * asset.w + (flip ? asset.w - 1 - x : x)) * 4);
      }
    });
    ctx.putImageData(image, 0, 0);
    frameCache[key] = c;
    return c;
  }

  const cache = {};
  function tileCanvas(id) {
    if (cache[id]) return cache[id];
    const asset = byId[id];
    const c = document.createElement('canvas');
    c.width = asset.w;
    c.height = asset.h;
    const ctx = c.getContext('2d');
    const image = ctx.createImageData(asset.w, asset.h);
    asset.frames[0].forEach((line, y) => {
      for (let x = 0; x < asset.w; x++) {
        const rgb = rgbOf[line[x]];
        if (rgb) image.data.set([rgb[0], rgb[1], rgb[2], 255], (y * asset.w + x) * 4);
      }
    });
    ctx.putImageData(image, 0, 0);
    // Where the painted pixels end, so a prop can stand on the top face.
    const rows = asset.frames[0];
    const lowest = rows.reduce((last, row, y) => (row.replace(/\./g, '') ? y : last), 0);
    const xs = rows.flatMap((row) => [...row].map((ch, x) => (ch === '.' ? null : x)).filter((x) => x !== null));
    c.meta = { bottom: lowest, centre: (Math.min(...xs) + Math.max(...xs) + 1) / 2 };
    cache[id] = c;
    return c;
  }

  /* ---------- the map ---------- */

  // A small seeded random number generator, so a map can be remade from its seed.
  function rng(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const pick = (rand, table) => {
    const total = table.reduce((n, [, w]) => n + w, 0);
    let roll = rand() * total;
    for (const [id, w] of table) {
      roll -= w;
      if (roll < 0) return id;
    }
    return table[0][0];
  };

  // Lakes are a few soft blobs, always kept off the outer ring so land surrounds them.
  function makeWater(n, lake, rand) {
    const water = Array.from({ length: n }, () => new Array(n).fill(false));
    if (!lake) return water;
    const blobs = lake === 1 ? 1 : lake === 2 ? 2 : 3;
    const reach = (n / 2) * (lake === 1 ? 0.28 : lake === 2 ? 0.4 : 0.55);
    for (let b = 0; b < blobs; b++) {
      const cx = n * (0.3 + 0.4 * rand());
      const cy = n * (0.3 + 0.4 * rand());
      const r = reach * (0.7 + 0.5 * rand());
      for (let y = 1; y < n - 1; y++) {
        for (let x = 1; x < n - 1; x++) {
          const wobble = 0.82 + 0.36 * rand();
          if (Math.hypot(x - cx, y - cy) < r * wobble) water[y][x] = true;
        }
      }
    }
    // A cell with no water beside it is a puddle, not a lake; take those back out.
    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        if (!water[y][x]) continue;
        const near = Object.values(SIDES).filter(([dx, dy]) => water[y + dy] && water[y + dy][x + dx]).length;
        if (!near) water[y][x] = false;
      }
    }
    return water;
  }

  // The water tile whose foam best matches the sides that touch land.
  function waterTile(want, set, rand) {
    let best = [];
    let score = Infinity;
    set.forEach(([id, sides]) => {
      const miss = ['NW', 'NE', 'SW', 'SE'].filter((s) => want.includes(s) !== sides.includes(s)).length;
      if (miss < score) { score = miss; best = [id]; } else if (miss === score) best.push(id);
    });
    return best[Math.floor(rand() * best.length)];
  }

  // A bridge across the water: a straight run of water cells with land at both ends, along either grid axis. Its first and last
  // cells are slopes (the last one flipped) and the cells between are flat. It is only drawn over sunken water, since the deck
  // hangs a little below the land. Returns a map of 'x,y' to the bridge frame to draw there, and whether to flip it.
  const BRIDGE = 'bridge';
  const FLAT_NE_SW = 0, FLAT_NW_SE = 1, SLOPE_NE = 2, SLOPE_SE = 3;
  function makeBridge(n, isWater, rand) {
    const runs = [];
    for (let line = 1; line < n - 1; line++) {
      for (const along of ['x', 'y']) {
        const at = (i) => (along === 'x' ? [i, line] : [line, i]);
        let i = 1;
        while (i < n - 1) {
          const [x, y] = at(i);
          if (!isWater(x, y)) { i++; continue; }
          let j = i;
          while (j + 1 < n && isWater(...at(j + 1))) j++;
          const before = at(i - 1);
          const after = at(j + 1);
          const length = j - i + 1;
          if (j + 1 < n && !isWater(...before) && !isWater(...after) && length >= 2 && length <= 7) runs.push({ along, line, from: i, to: j, length });
          i = j + 1;
        }
      }
    }
    if (!runs.length) return null;
    const shortest = Math.min(...runs.map((r) => r.length));
    const choices = runs.filter((r) => r.length === shortest);
    const run = choices[Math.floor(rand() * choices.length)];
    const cells = new Map();
    for (let i = run.from; i <= run.to; i++) {
      const key = run.along === 'x' ? `${i},${run.line}` : `${run.line},${i}`;
      // Along x the bridge runs NW-SE (the first cell, nearest the NW land, takes the SE slope); along y it runs NE-SW (the
      // first cell, nearest the NE land, takes the SE slope flipped, and the last one the NE slope).
      if (run.along === 'x') {
        if (i === run.from) cells.set(key, { frame: SLOPE_SE, flip: false });
        else if (i === run.to) cells.set(key, { frame: SLOPE_NE, flip: true });
        else cells.set(key, { frame: FLAT_NW_SE, flip: false });
      } else if (i === run.from) cells.set(key, { frame: SLOPE_SE, flip: true });
      else if (i === run.to) cells.set(key, { frame: SLOPE_NE, flip: false });
      else cells.set(key, { frame: FLAT_NE_SW, flip: false });
    }
    return cells;
  }

  // The set's layers each name groups of pieces; a piece is an asset id, and an asset with several frames of kind `variants` is several looks of one piece.
  const footprintOf = (id) => (byId[id].footprint ? byId[id].footprint : { size: [1, 1], cells: [[0, 0]] });
  const isOneCell = (id) => footprintOf(id).cells.length === 1;
  const lookOf = (id, rand) => (byId[id].kind === 'variants' ? Math.floor(rand() * byId[id].frames.length) : 0);
  // Water in a sunken lake is one step (8 rows) below the land. A water prop (a dock, a stepping stone, pads, a boat) is drawn on the surface, a step down; a bridge is drawn on the gap's floor, a
  // level down, so its deck is level with the banks.
  const waterDrop = (id) => {
    if (el('level').value !== 'sunken') return 0;
    const a = id && byId[id];
    // A prop made for the water's surface (surface: 'water') stands on it: one step down. A bridge stands on the gap's floor, a level below the banks.
    return a && a.walkable && a.surface !== 'water' ? Math.round(a.levels * LEVEL_PX) : 8;
  };

  // Multi-cell pieces are planned before anything is drawn: each goes where every cell of its footprint is clear, and (on land) does not touch water. A piece is drawn
  // when the loop reaches its front-most cell, so it sits behind what is nearer and in front of what is further.
  function plan(table, count, n, rand, ok, taken, plans) {
    for (let tries = 0, placed = 0; placed < count && tries < count * 14 + 20; tries++) {
      const id = pick(rand, table);
      const [fx, fy] = footprintOf(id).size;
      if (fx > n || fy > n) continue;
      const bx = Math.floor(rand() * (n - fx + 1));
      const by = Math.floor(rand() * (n - fy + 1));
      const cells = footprintOf(id).cells.map(([i, j]) => [bx + i, by + j]);
      if (cells.some(([x, y]) => taken.has(`${x},${y}`) || !ok(x, y))) continue;
      cells.forEach(([x, y]) => taken.add(`${x},${y}`));
      const front = cells.reduce((best, c) => (c[0] + c[1] > best[0] + best[1] ? c : best), cells[0]);
      const key = `${front[0]},${front[1]}`;
      if (!plans.has(key)) plans.set(key, []);
      plans.get(key).push({ id, bx, by, fx, fy, look: lookOf(id, rand) });
      placed++;
    }
  }

  // Where the piece's anchor goes: the middle of its bounding box on the ground, from the tile at the box's back corner.
  function drawPlan(ctx, p, n, drop) {
    const asset = byId[p.id];
    const tx = (p.bx - p.by) * STEP_X + (n - 1) * STEP_X;
    const ty = (p.bx + p.by) * STEP_Y + HEADROOM + (drop || 0);
    const mx = tx + TILE / 2 + (STEP_X / 2) * (p.fx - p.fy);
    const my = ty + (STEP_Y / 2) * (p.fx + p.fy);
    ctx.drawImage(frameCanvas(p.id, p.look, false), Math.round(mx - asset.anchor.x), Math.round(my - asset.anchor.y));
  }

  // The newer bridges are whole pieces: a stone arch, planks or a corrupted one, 3 or 5 cells long along either axis, each covering exactly the water it crosses. Like
  // the old bridge, one goes where a straight run of water has land at both ends and its length is one the set's bridge group has; unlike it, the piece is one picture
  // that stands on the gap's floor a level below the banks, so its deck meets them.
  function makeSpan(set, n, isWater, rand) {
    const pieces = SETS.groups[set.bridge].ids.filter((id) => exists(id) && byId[id].run && byId[id].walkable);
    if (!pieces.length) return null;
    const runs = [];
    for (let line = 1; line < n - 1; line++) {
      for (const along of ['x', 'y']) {
        const at = (i) => (along === 'x' ? [i, line] : [line, i]);
        let i = 1;
        while (i < n - 1) {
          if (!isWater(...at(i))) { i++; continue; }
          let j = i;
          while (j + 1 < n && isWater(...at(j + 1))) j++;
          const length = j - i + 1;
          if (j + 1 < n && !isWater(...at(i - 1)) && !isWater(...at(j + 1)) && pieces.some((id) => byId[id].footprint.size[along === 'x' ? 0 : 1] === length && byId[id].run === along)) {
            runs.push({ along, line, from: i, length });
          }
          i = j + 1;
        }
      }
    }
    if (!runs.length) return null;
    const run = runs[Math.floor(rand() * runs.length)];
    const options = pieces.filter((id) => byId[id].run === run.along && byId[id].footprint.size[run.along === 'x' ? 0 : 1] === run.length);
    const id = options[Math.floor(rand() * options.length)];
    const [bx, by] = run.along === 'x' ? [run.from, run.line] : [run.line, run.from];
    const [fx, fy] = byId[id].footprint.size;
    const cells = new Set(byId[id].footprint.cells.map(([i, j]) => `${bx + i},${by + j}`));
    const front = byId[id].footprint.cells.map(([i, j]) => [bx + i, by + j]).reduce((best, c) => (c[0] + c[1] > best[0] + best[1] ? c : best));
    return { id, bx, by, fx, fy, cells, front: `${front[0]},${front[1]}`, look: 0 };
  }
  const drawSpan = (ctx, span, n) => drawPlan(ctx, span, n, waterDrop(span.id));

  // One piece scattered on a cell: a ground-sheet piece stands on the top face by its lowest pixel; any other asset by its anchor.
  function drawProp(ctx, id, sx, sy, look) {
    if (/^ground-/.test(id)) {
      const prop = tileCanvas(id);
      ctx.drawImage(prop, Math.round(sx + TILE / 2 - prop.meta.centre), sy + TOP_CENTRE_Y + 4 - prop.meta.bottom - 1);
    } else {
      const asset = byId[id];
      ctx.drawImage(frameCanvas(id, look || 0, false), sx + TILE / 2 - asset.anchor.x, sy + TOP_CENTRE_Y - asset.anchor.y);
    }
  }

  // Mycelium: veins that join. Each tile names the edges its vein leaves by (assets/data.js `decal.edges`, at the middle of an edge), so a walk of cells is
  // drawn by picking, for every cell, the tile whose edges are exactly the sides the walk uses there.
  const EDGE_OF = { NE: [0, -1], SE: [1, 0], SW: [0, 1], NW: [-1, 0] };
  const OPPOSITE = { NE: 'SW', SW: 'NE', SE: 'NW', NW: 'SE' };
  function veinTiles() {
    const table = new Map();
    Object.values(byId).forEach((a) => {
      if (a.decal && a.decal.edges && /^mycelium-/.test(a.id)) table.set([...a.decal.edges].map((e) => e.toUpperCase()).sort().join(','), a.id);
    });
    return table;
  }
  function planVeins(count, n, rand, ok, taken) {
    const tiles = veinTiles();
    const edges = new Map();                        // 'x,y' -> set of edges used
    const link = (x, y, side) => { const k = `${x},${y}`; if (!edges.has(k)) edges.set(k, new Set()); edges.get(k).add(side); };
    for (let v = 0; v < count; v++) {
      let x = Math.floor(rand() * n);
      let y = Math.floor(rand() * n);
      if (!ok(x, y) || taken.has(`${x},${y}`)) continue;
      let side = Object.keys(EDGE_OF)[Math.floor(rand() * 4)];
      const length = 3 + Math.floor(rand() * 5);
      for (let step = 0; step < length; step++) {
        const [dx, dy] = EDGE_OF[side];
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= n || ny >= n || !ok(nx, ny) || taken.has(`${nx},${ny}`)) break;
        link(x, y, side);
        link(nx, ny, OPPOSITE[side]);
        x = nx;
        y = ny;
        if (rand() < 0.35) side = Object.keys(EDGE_OF)[Math.floor(rand() * 4)]; else if (rand() < 0.2) break;
        if (side === OPPOSITE[[...edges.get(`${x},${y}`)][0]]) continue;
      }
    }
    const out = [];
    edges.forEach((set, key) => {
      const id = tiles.get([...set].sort().join(','));
      if (id) out.push({ key, id });
    });
    return out;
  }

  // The weather layer: a seeded roll for whether the set has any, then one overlay by weight, drawn tiled over the whole map at the middle of its opacity range.
  function pickWeather(set, rand) {
    const w = el('weather').value;
    if (w === 'none') return null;
    let id = null;
    if (w === 'set') {
      if (!set.weather || rand() >= set.weather.chance) return null;
      const table = tableOf(set, 'weather');
      if (!table.length) return null;
      id = pick(rand, table);
    } else if (exists(w)) id = w;
    return id;
  }
  function drawWeather(ctx, id, width, height, frame) {
    const a = byId[id];
    const [lo, hi] = a.weather.opacity;
    ctx.save();
    ctx.globalAlpha = (lo + hi) / 2;
    if (a.weather.blend === 'add') ctx.globalCompositeOperation = 'lighter';
    const tile = frameCanvas(id, frame % a.frames.length, false);
    for (let y = 0; y < height; y += a.h) for (let x = 0; x < width; x += a.w) ctx.drawImage(tile, x, y);
    ctx.restore();
  }

  function build() {
    const seed = Number(el('seed').value) || 0;
    const n = Number(el('size').value);
    const rand = rng(seed);
    const theme = setOf();
    const water = makeWater(n, Number(el('lake').value), rand);
    const waterTiles = waterOf(theme, el('level').value);
    const grass = grassOf(theme);
    const scatter = tableOf(theme, 'scatter').filter(([id]) => isOneCell(id));
    const withProps = el('props').checked;
    const isWater = (x, y) => Boolean(water[y] && water[y][x]);
    const isShore = (x, y) => Object.values(SIDES).some(([dx, dy]) => isWater(x + dx, y + dy));
    const waterCount = water.flat().filter(Boolean).length;
    // Its own random numbers, so adding a bridge never changes the rest of a map made from the same seed.
    const bridge = theme.bridge && el('bridge').checked && el('level').value === 'sunken' && byId[BRIDGE] && SETS.groups[theme.bridge].ids.includes(BRIDGE) ? makeBridge(n, isWater, rng(seed ^ 0x9e3779b9)) : null;
    const span = theme.bridge && el('bridge').checked && el('level').value === 'sunken' && !bridge ? makeSpan(theme, n, isWater, rng(seed ^ 0x9e3779b9)) : null;

    const taken = new Set();
    const landPlans = new Map();
    const waterPlans = new Map();
    const decalPlans = [];
    let veins = [];
    const wtaken = new Set();
    if (span) span.cells.forEach((c) => wtaken.add(c));
    if (withProps) {
      const features = tableOf(theme, 'features').filter(([id]) => byId[id].footprint);
      if (features.length) plan(features, Math.round((theme.features.per100 * n * n) / 100), n, rng(seed ^ 0x85ebca6b), (x, y) => !isWater(x, y) && !isShore(x, y), taken, landPlans);
      if (theme.water) {
        const inWater = tableOf(theme, 'water').filter(([id]) => byId[id].footprint);
        if (inWater.length && waterCount) plan(inWater, Math.round((theme.water.per100 * waterCount) / 100), n, rng(seed ^ 0x27d4eb2f), (x, y) => isWater(x, y), wtaken, waterPlans);
      }
      const dr = rng(seed ^ 0x165667b1);
      theme.decals.forEach((d) => {
        const ids = SETS.groups[d.group].ids.filter(exists);
        if (!ids.length) return;
        if (SETS.groups[d.group].joins === 'mycelium') {
          veins = planVeins(Math.max(1, Math.round((d.per100 * n * n) / 100)), n, dr, (x, y) => !isWater(x, y) && !isShore(x, y), taken);
          return;
        }
        const cellOk = d.on === 'water' ? (x, y) => isWater(x, y) && !wtaken.has(`${x},${y}`) : d.on === 'shore' ? (x, y) => !isWater(x, y) && isShore(x, y) : (x, y) => !isWater(x, y) && !isShore(x, y);
        const pool = d.on === 'water' ? waterCount : n * n;
        const single = ids.filter(isOneCell).map((id) => [id, 1]);
        const multi = ids.filter((id) => !isOneCell(id)).map((id) => [id, 1]);
        const decalTaken = new Set(taken);
        if (multi.length) {
          const plans = new Map();
          plan(multi, Math.max(1, Math.round((d.per100 * n * n) / 100)), n, dr, cellOk, decalTaken, plans);
          plans.forEach((list) => list.forEach((p) => decalPlans.push({ ...p, flat: true })));
          decalPlans.forEach((p) => footprintOf(p.id).cells.forEach(([i, j]) => taken.add(`${p.bx + i},${p.by + j}`)));
        }
        if (single.length) {
          for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
            if (cellOk(x, y) && !decalTaken.has(`${x},${y}`) && dr() < (d.per100 * 1) / 100 * (n * n) / Math.max(1, pool) * 0.5 + 0) decalPlans.push({ id: pick(dr, single), bx: x, by: y, fx: 1, fy: 1, look: 0, flat: true, water: d.on === 'water' });
          }
        }
      });
    }
    const weather = pickWeather(theme, rng(seed ^ 0xc2b2ae35));

    const width = n * 2 * STEP_X;
    const height = n * 2 * STEP_Y + TILE + HEADROOM;
    const art = document.createElement('canvas');
    art.width = width;
    art.height = height;
    const ctx = art.getContext('2d');
    const order = [];
    for (let d = 0; d <= (n - 1) * 2; d++) for (let x = 0; x < n; x++) if (d - x >= 0 && d - x < n) order.push([x, d - x]);
    const screen = (x, y) => [(x - y) * STEP_X + (n - 1) * STEP_X, (x + y) * STEP_Y + HEADROOM];

    let counts = { grass: 0, water: 0, props: 0, bridge: 0, rocks: 0, decals: 0 };
    const propRand = rng(seed ^ 0x9e3779b1);
    // Pass one: the ground, back to front (the water's foam is picked from the same random numbers as before).
    order.forEach(([x, y]) => {
      const [sx, sy] = screen(x, y);
      if (isWater(x, y)) {
        const want = Object.entries(SIDES).filter(([, [dx, dy]]) => !isWater(x + dx, y + dy) && x + dx >= 0 && y + dy >= 0 && x + dx < n && y + dy < n).map(([s]) => s);
        ctx.drawImage(tileCanvas(waterTile(want, waterTiles, rand)), sx, sy);
        counts.water++;
      } else {
        ctx.drawImage(tileCanvas(pick(rand, grass)), sx, sy);
        counts.grass++;
      }
    });
    // Pass two: flat things on the ground (veins, circles, pads), before anything stands on it.
    veins.forEach(({ key, id }) => {
      const [x, y] = key.split(',').map(Number);
      const [sx, sy] = screen(x, y);
      ctx.drawImage(frameCanvas(id, 0, false), sx + TILE / 2 - byId[id].anchor.x, sy + TOP_CENTRE_Y - byId[id].anchor.y);
      counts.decals++;
    });
    decalPlans.forEach((p) => { drawPlan(ctx, p, n, p.water ? waterDrop(p.id) : 0); counts.decals++; });
    // Pass three: things that stand, back to front.
    order.forEach(([x, y]) => {
      const [sx, sy] = screen(x, y);
      const key = `${x},${y}`;
      if (isWater(x, y)) {
        const spanned = bridge && bridge.get(key);
        if (spanned) {
          // The sprite's anchor is the middle of the land-level top face, 18 down from its top.
          ctx.drawImage(frameCanvas(BRIDGE, spanned.frame, spanned.flip), sx, sy + TOP_CENTRE_Y - byId[BRIDGE].anchor.y);
          counts.bridge++;
        }
        (waterPlans.get(key) || []).forEach((p) => { drawPlan(ctx, p, n, waterDrop(p.id)); counts.rocks++; });
      } else {
        // Props keep off the shore, so the foam stays visible, and thin out toward the middle.
        if (withProps && scatter.length && !isShore(x, y) && !taken.has(key) && propRand() < theme.scatter.density) {
          const id = pick(propRand, scatter);
          drawProp(ctx, id, sx, sy, lookOf(id, propRand));
          counts.props++;
        }
        (landPlans.get(key) || []).forEach((p) => { drawPlan(ctx, p, n, 0); counts.rocks++; });
      }
      if (span && span.front === key) { drawSpan(ctx, span, n); counts.bridge += span.cells.size; }
    });
    if (weather) drawWeather(ctx, weather, width, height, 0);
    return { art, counts, seed, n, theme, weather };
  }

  let current = null;

  function render() {
    current = build();
    const { art } = current;
    const view = el('map');
    // As big as fits the window (whole pixels only), and never smaller than true size.
    const room = el('map').closest('.stage').clientWidth - 40;
    const scale = Math.max(1, Math.min(VIEW_SCALE, Math.floor(room / art.width)));
    view.width = art.width * scale;
    view.height = art.height * scale;
    const ctx = view.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, view.width, view.height);
    ctx.drawImage(art, 0, 0, view.width, view.height);
    const { counts } = current;
    el('status').textContent = `${current.theme.label} · seed ${current.seed} · ${current.n} × ${current.n} · ${counts.grass} grass, ${counts.water} water, ${counts.props} props, ${counts.rocks} rocks, ${counts.decals} decals` + (counts.bridge ? `, a bridge of ${counts.bridge}` : '') + (current.weather ? `, ${current.weather.replace(/^weather-/, '')}` : '');
  }

  function regenerate() {
    el('seed').value = Math.floor(Math.random() * 1e6);
    render();
  }

  /* ---------- controls ---------- */

  // The set menu, with each set's own defaults (lake, water level, bridge) applied when it is picked.
  Object.entries(SETS.sets).forEach(([id, s]) => {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = `${s.label} (${s.ground})`;
    el('set').appendChild(option);
  });
  function applySet() {
    const theme = setOf();
    el('lake').value = String(theme.lake);
    el('level').value = theme.level;
    el('bridge').checked = Boolean(theme.bridge);
    el('bridge').disabled = !theme.bridge;
    el('setBlurb').textContent = theme.blurb;
  }
  el('set').addEventListener('change', () => { applySet(); render(); });
  el('regen').addEventListener('click', regenerate);
  ['seed', 'size', 'lake', 'level', 'props', 'bridge', 'weather'].forEach((id) => el(id).addEventListener('change', render));

  el('exportMap').addEventListener('click', () => {
    const scale = Number(el('exportScale').value);
    const out = document.createElement('canvas');
    out.width = current.art.width * scale;
    out.height = current.art.height * scale;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(current.art, 0, 0, out.width, out.height);
    out.toBlob((blob) => {
      download(blob, `terrain-${el('set').value}-${current.seed}.png`);
      el('note').textContent = `Saved terrain-${el('set').value}-${current.seed}.png at ${scale}×.`;
    }, 'image/png');
  });

  // A link can name its map: terrain.html?set=gravemoor&seed=7
  const params = new URLSearchParams(window.location.search);
  if (params.get('set') && SETS.sets[params.get('set')]) el('set').value = params.get('set');
  applySet();
  const fromLink = params.get('seed');
  if (fromLink !== null && fromLink !== '') {
    el('seed').value = fromLink;
    render();
  } else {
    regenerate();
  }
}
