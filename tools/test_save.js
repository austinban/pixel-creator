// Checks the sprites/ save guard with in-memory folders (the real picker needs a browser). Run: node tools/test_save.js
const assert = require('assert');
const { setFolderProblem, writeSetFolder, MANIFEST_NAME } = require('../sprites-save.js');

class Dir {
  constructor() { this.dirs = new Map(); this.files = new Map(); }
  async getDirectoryHandle(name, { create } = {}) {
    if (!this.dirs.has(name)) { if (!create) throw new Error('NotFoundError'); this.dirs.set(name, new Dir()); }
    return this.dirs.get(name);
  }
  async getFileHandle(name, { create } = {}) {
    if (!this.files.has(name)) { if (!create) throw new Error('NotFoundError'); this.files.set(name, null); }
    return { createWritable: async () => ({ write: async (d) => { this.files.set(name, d); }, close: async () => {} }) };
  }
}

(async () => {
  const sprites = new Dir();
  (await sprites.getDirectoryHandle('ninja', { create: true })).files.set('ninja-walkingSE.png', 'generated');      // a generated set: PNGs, no manifest
  (await sprites.getDirectoryHandle('bones', { create: true })).files.set('bones-walkingSE.png', 'generated');      // generated, and not in the list of bases
  const bases = ['ninja', 'human'];

  assert.match(await setFolderProblem(sprites, 'ninja', bases), /generated base/);          // named like a base
  assert.match(await setFolderProblem(sprites, 'weapons', bases), /not a character/);       // not a character folder
  assert.match(await setFolderProblem(sprites, 'bones', bases), /not saved from here/);     // exists, no manifest of ours
  assert.strictEqual(await setFolderProblem(sprites, 'red-ninja', bases), '');              // free

  // writing makes the folder, with the PNGs and the manifest; after that it may be overwritten
  await writeSetFolder(sprites, 'red-ninja', [{ name: 'red-ninja-attackSE.png', data: new Uint8Array([1]) }], { format: 1, set: 'red-ninja' });
  const made = await sprites.getDirectoryHandle('red-ninja');
  assert.ok(made.files.has('red-ninja-attackSE.png') && made.files.has(MANIFEST_NAME));
  assert.strictEqual(JSON.parse(made.files.get(MANIFEST_NAME)).set, 'red-ninja');
  assert.strictEqual(await setFolderProblem(sprites, 'red-ninja', bases), '');

  // and the generated sets were never touched
  assert.strictEqual((await sprites.getDirectoryHandle('ninja')).files.get('ninja-walkingSE.png'), 'generated');
  console.log('save guard: ok');
})().catch((e) => { console.error(e); process.exit(1); });
