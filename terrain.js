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
const TOP_CENTRE_Y = 8;     // the middle of a cube's top face, from the top of its tile
const VIEW_SCALE = 4;        // the most the preview is blown up

const el = (id) => document.getElementById(id);
const data = window.ASSETS;

if (!data) {
  el('missing').hidden = false;
} else {
  boot();
}

function boot() {
  el('app').hidden = false;

  const rgbOf = {};
  data.roles.forEach((r) => { rgbOf[r.char] = [1, 3, 5].map((i) => parseInt(r.hex.slice(i, i + 2), 16)); });
  const byId = Object.fromEntries(data.assets.map((a) => [a.id, a]));

  // Grass: mostly plain, with a few that have a dirt patch or stepping stones.
  const GRASS = [
    ['ground-0-0', 10],                                   // plain
    ['ground-9-1', 2],                                    // a patch of dirt
    ['ground-8-7', 1], ['ground-10-9', 1], ['ground-10-7', 1], ['ground-9-8', 1], ['ground-8-9', 1],   // stepping stones
  ];
  // Things that stand on the grass.
  const PROPS = [
    ['ground-1-3', 3],                    // pine tree
    ['ground-0-3', 3],                    // bush
    ['ground-0-4', 2], ['ground-0-5', 2], // rocks
    ['ground-1-5', 1],                    // stump
    ['ground-2-8', 2], ['ground-4-8', 2], // flowers
  ];

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
  // Which neighbour sits on which side of a cell (x, y of the map grid).
  const SIDES = { NW: [-1, 0], NE: [0, -1], SW: [0, 1], SE: [1, 0] };

  /* ---------- drawing ---------- */

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

  function build() {
    const seed = Number(el('seed').value) || 0;
    const n = Number(el('size').value);
    const rand = rng(seed);
    const water = makeWater(n, Number(el('lake').value), rand);
    const set = WATER[el('level').value];
    const withProps = el('props').checked;
    const isWater = (x, y) => Boolean(water[y] && water[y][x]);

    const width = n * 2 * STEP_X;
    const height = n * 2 * STEP_Y + TILE + HEADROOM;
    const art = document.createElement('canvas');
    art.width = width;
    art.height = height;
    const ctx = art.getContext('2d');

    let counts = { grass: 0, water: 0, props: 0 };
    // Back to front: the cells furthest from the viewer first.
    for (let d = 0; d <= (n - 1) * 2; d++) {
      for (let x = 0; x < n; x++) {
        const y = d - x;
        if (y < 0 || y >= n) continue;
        const sx = (x - y) * STEP_X + (n - 1) * STEP_X;
        const sy = (x + y) * STEP_Y + HEADROOM;
        if (isWater(x, y)) {
          const want = Object.entries(SIDES).filter(([, [dx, dy]]) => !isWater(x + dx, y + dy) && x + dx >= 0 && y + dy >= 0 && x + dx < n && y + dy < n).map(([s]) => s);
          ctx.drawImage(tileCanvas(waterTile(want, set, rand)), sx, sy);
          counts.water++;
        } else {
          ctx.drawImage(tileCanvas(pick(rand, GRASS)), sx, sy);
          counts.grass++;
          // Props keep off the shore, so the foam stays visible, and thin out toward the middle.
          const shore = Object.values(SIDES).some(([dx, dy]) => isWater(x + dx, y + dy));
          if (withProps && !shore && rand() < 0.22) {
            const prop = tileCanvas(pick(rand, PROPS));
            ctx.drawImage(prop, Math.round(sx + TILE / 2 - prop.meta.centre), sy + TOP_CENTRE_Y + 4 - prop.meta.bottom - 1);
            counts.props++;
          }
        }
      }
    }
    return { art, counts, seed, n };
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
    el('status').textContent = `Seed ${current.seed} · ${current.n} × ${current.n} · ${counts.grass} grass, ${counts.water} water, ${counts.props} props`;
  }

  function regenerate() {
    el('seed').value = Math.floor(Math.random() * 1e6);
    render();
  }

  /* ---------- controls ---------- */

  el('regen').addEventListener('click', regenerate);
  ['seed', 'size', 'lake', 'level', 'props'].forEach((id) => el(id).addEventListener('change', render));

  el('exportMap').addEventListener('click', () => {
    const scale = Number(el('exportScale').value);
    const out = document.createElement('canvas');
    out.width = current.art.width * scale;
    out.height = current.art.height * scale;
    const ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(current.art, 0, 0, out.width, out.height);
    out.toBlob((blob) => {
      download(blob, `terrain-${current.seed}.png`);
      el('note').textContent = `Saved terrain-${current.seed}.png at ${scale}×.`;
    }, 'image/png');
  });

  regenerate();
}
