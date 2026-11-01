// Bases and copies - shared by the characters and assets pages.
//
// A base (a character base, an asset) is never edited. It shows in the picker as
// a read-only entry; the first time you change anything while it is selected, the
// change goes into a new saved copy and that copy becomes the selection. A copy
// saves itself as you edit, and you can keep as many as you like. Saved copies
// from before this model are all just copies.

const BASE_PREFIX = 'base:';

const isBaseRef = (ref) => typeof ref === 'string' && ref.startsWith(BASE_PREFIX);
const baseRefOf = (baseId) => BASE_PREFIX + baseId;
const baseIdOf = (ref) => ref.slice(BASE_PREFIX.length);

// A throwaway, read-only stand-in for a base. It is never added to the store.
function baseView(item) {
  return { ...item, readOnly: true };
}

// A saved copy of anything: its own id, none of the read-only flag.
function copyOf(source, id, name) {
  const { readOnly, ...rest } = JSON.parse(JSON.stringify(source));
  return { ...rest, id, name };
}

// Fill a picker with the bases (read-only) above the saved copies.
function fillPicker(select, bases, copies, currentId) {
  select.textContent = '';
  const group = (label, entries) => {
    if (!entries.length) return;
    const optgroup = document.createElement('optgroup');
    optgroup.label = label;
    entries.forEach(([value, text]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = text;
      optgroup.appendChild(option);
    });
    select.appendChild(optgroup);
  };
  group('Bases (never change)', bases.map((b) => [baseRefOf(b.id), b.label]));
  group('Your copies', copies.map((c) => [c.id, c.name || 'Untitled']));
  select.value = currentId;
}
