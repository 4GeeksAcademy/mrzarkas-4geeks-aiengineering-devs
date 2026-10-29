/** Shared DOM structure for filters and required/fixed select controls. */
export function createSelectField(labelText, id) {
  const label = document.createElement('label');
  label.className = 'field';
  const caption = document.createElement('span');
  caption.textContent = labelText;
  const select = document.createElement('select');
  select.id = id;
  label.append(caption, select);
  return { label, select };
}
