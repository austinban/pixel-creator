// Saving a character straight into the repo's sprites/ folder, so the game's sync script picks it up with no ZIP in between.
//
// It uses the File System Access API (Chromium only; the ZIP exports stay as the fallback). The browser asks for the sprites/ folder once and the
// handle is remembered, so after that it is one click. A set is written at 1x as sprites/<set>/<set>-<pose>.png, exactly like a generated set,
// with a pixel-creator.json beside the PNGs that says what it is. That file is also the guard: a folder is only ever overwritten if it already has
// one, so a copy named like a generated base (a copy called "ninja") can never replace the generated sprites/ninja/.

const SPRITES_DB = 'pixel-creator.files';
const SPRITES_HANDLE_KEY = 'sprites-dir';
const MANIFEST_NAME = 'pixel-creator.json';
const RESERVED_FOLDERS = ['assets', 'weapons', 'weapons-original'];     // folders of sprites/ that are not character sets

const canSaveToSprites = () => typeof window !== 'undefined' && typeof window.showDirectoryPicker === 'function';

function handleStore() {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open(SPRITES_DB, 1);
    open.onupgradeneeded = () => open.result.createObjectStore('handles');
    open.onsuccess = () => resolve(open.result);
    open.onerror = () => reject(open.error);
  });
}

async function rememberHandle(handle) {
  const db = await handleStore();
  await new Promise((resolve, reject) => {
    const tx = db.transaction('handles', 'readwrite');
    tx.objectStore('handles').put(handle, SPRITES_HANDLE_KEY);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}

async function rememberedHandle() {
  try {
    const db = await handleStore();
    return await new Promise((resolve) => {
      const req = db.transaction('handles').objectStore('handles').get(SPRITES_HANDLE_KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
    });
  } catch { return null; }
}

// The sprites/ folder: the remembered one if the browser still lets us write to it, else ask. Throws a plain Error with a message to show.
async function spritesFolder() {
  const kept = await rememberedHandle();
  if (kept) {
    let permission = await kept.queryPermission({ mode: 'readwrite' });
    if (permission !== 'granted') permission = await kept.requestPermission({ mode: 'readwrite' });
    if (permission === 'granted') return kept;
  }
  let picked;
  try {
    picked = await window.showDirectoryPicker({ id: 'pixel-creator-sprites', mode: 'readwrite' });
  } catch (error) {
    throw new Error(error && error.name === 'AbortError' ? 'Nothing was saved: no folder was chosen.' : `Could not open the folder: ${error.message}`);
  }
  if (picked.name !== 'sprites') throw new Error(`Choose the repo's sprites folder (you picked "${picked.name}").`);
  await rememberHandle(picked);
  return picked;
}

// May a set called `name` be written under sprites/? Returns '' if so, else the reason it may not.
async function setFolderProblem(sprites, name, generatedBases) {
  if (RESERVED_FOLDERS.includes(name)) return `"${name}" is not a character folder.`;
  if (generatedBases.includes(name)) return `"${name}" is a generated base: rename the copy first, or it would replace the base.`;
  let dir;
  try { dir = await sprites.getDirectoryHandle(name); } catch { return ''; }       // not there yet: free to make
  try { await dir.getFileHandle(MANIFEST_NAME); return ''; } catch { /* no manifest */ }
  return `sprites/${name} already exists and was not saved from here: rename the copy first.`;
}

// files: [{ name, data: Uint8Array }]. Writes them, and the manifest, into sprites/<name>/.
async function writeSetFolder(sprites, name, files, manifest) {
  const dir = await sprites.getDirectoryHandle(name, { create: true });
  const put = async (fileName, data) => {
    const handle = await dir.getFileHandle(fileName, { create: true });
    const stream = await handle.createWritable();
    await stream.write(data);
    await stream.close();
  };
  for (const file of files) await put(file.name, file.data);
  await put(MANIFEST_NAME, JSON.stringify(manifest, null, 2) + '\n');
}

if (typeof module !== 'undefined') module.exports = { setFolderProblem, writeSetFolder, MANIFEST_NAME, RESERVED_FOLDERS };
