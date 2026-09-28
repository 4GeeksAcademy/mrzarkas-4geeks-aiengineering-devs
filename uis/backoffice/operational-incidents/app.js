const PAGE_SIZE = 20;
const app = document.querySelector('#app');
const connectionForm = document.querySelector('#connectionForm');
const connectionMessage = document.querySelector('#connectionMessage');
const disconnectButton = document.querySelector('#disconnectButton');

const session = { apiUrl: '', token: '', claims: null, catalogs: {}, references: {} };
const catalogNames = ['incidentStatus', 'severity', 'entryChannel', 'incidentType'];

function setMessage(text, kind = '') {
  connectionMessage.textContent = text;
  connectionMessage.className = `inline-message${kind ? ` ${kind}` : ''}`;
}

function decodeClaims(token) {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(payload.padEnd(Math.ceil(payload.length / 4) * 4, '='));
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(decoded, char => char.charCodeAt(0))));
  } catch {
    return null;
  }
}

function hasReadDetail() {
  return ['admin', 'technology', 'compliance', 'responsibleArea'].includes(session.claims?.role);
}

function canEditOwnArea() {
  return session.claims?.role === 'responsibleArea' && Boolean(session.claims?.area_id);
}

function canEditGenerally() {
  return ['admin', 'technology'].includes(session.claims?.role);
}

async function api(path, options = {}) {
  const response = await fetch(`${session.apiUrl}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${session.token}`,
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let detail = `Error HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* keep generic status */ }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

function showConnectionState(connected) {
  connectionForm.hidden = connected;
  disconnectButton.hidden = !connected;
  document.querySelector('#apiUrl').disabled = connected;
}

async function connect(apiUrl, token) {
  session.apiUrl = apiUrl.replace(/\/+$/, '');
  session.token = token;
  session.claims = decodeClaims(token);
  session.catalogs = {};
  session.references = {};

  if (!session.claims?.role) throw new Error('El JWT no contiene un claim role legible.');
  if (session.claims.role === 'responsibleArea' && !session.claims.area_id) {
    throw new Error('El JWT responsibleArea no contiene area_id.');
  }

  // Direction has summary-only access and lacks catalog/reference capabilities.
  if (session.claims.role !== 'direction') {
    await Promise.all([
      ...catalogNames.map(async name => { session.catalogs[name] = await api(`/catalogs/${name}`); }),
      ...['clinics', 'jurisdictions', 'affected-systems', 'responsible-areas'].map(async name => {
        const result = await api(`/management/reference-data/${name}?offset=0&limit=100`);
        session.references[name] = result.items ?? [];
      }),
    ]);
  }
  showConnectionState(true);
  setMessage(`Conectado como ${session.claims.role}. Los controles de la interfaz no sustituyen los permisos de la API.`, 'success');
  await renderRoute();
}

function disconnect() {
  session.apiUrl = '';
  session.token = '';
  session.claims = null;
  session.catalogs = {};
  session.references = {};
  document.querySelector('#token').value = '';
  showConnectionState(false);
  setMessage('Desconectado. El token se ha eliminado de memoria.');
  app.replaceChildren();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function option(label, value = '') {
  const item = document.createElement('option');
  item.value = value;
  item.textContent = label;
  return item;
}

function selectField(labelText, id, items, selected = '') {
  const label = element('label', 'field');
  label.append(element('span', '', labelText));
  const select = document.createElement('select');
  select.id = id;
  select.append(option('Todos'));
  for (const item of items) {
    const entry = option(item.label, item.id);
    entry.selected = item.id === selected;
    select.append(entry);
  }
  label.append(select);
  return label;
}

function labelFor(catalogName, id) {
  return session.catalogs[catalogName]?.values?.find(item => item.id === id)?.label ?? '—';
}

function referenceLabel(resource, id) {
  return session.references[resource]?.find(item => item.id === id)?.label ?? '—';
}

function makePill(text, tone = '') {
  return element('span', `pill${tone ? ` ${tone}` : ''}`, text);
}

function dateLabel(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function routeParts() {
  const route = location.hash.replace(/^#\/?/, '').split('?')[0];
  return route ? route.split('/').filter(Boolean) : ['incidents'];
}

function routeQuery() {
  const query = location.hash.includes('?') ? location.hash.split('?').slice(1).join('?') : '';
  return new URLSearchParams(query);
}

function showError(error, heading = 'No se pudo completar la operación') {
  app.replaceChildren();
  const panel = element('section', 'panel error-state');
  panel.append(element('h2', '', heading), element('p', '', error.message));
  if (error.status === 401) panel.append(element('p', '', 'Revisa el JWT y vuelve a conectar.'));
  if (error.status === 403) panel.append(element('p', '', 'La API ha denegado la acción por permisos o por alcance del recurso.'));
  const back = element('a', 'button button-secondary', 'Volver a incidencias');
  back.href = '#/incidents';
  panel.append(back);
  app.append(panel);
}

async function renderRoute() {
  if (!session.token) {
    app.replaceChildren();
    const empty = element('section', 'panel empty-state');
    empty.append(element('h1', '', 'Incidencias operativas'), element('p', '', 'Conecta con la API usando un JWT de desarrollo para consultar incidencias sintéticas.'));
    app.append(empty);
    return;
  }
  const [section, id] = routeParts();
  if (section !== 'incidents' || !id) return renderList();
  if (id === 'new') return renderNotImplemented();
  return renderDetail(id);
}

function renderNotImplemented() {
  app.replaceChildren();
  const panel = element('section', 'panel empty-state');
  panel.append(element('h1', '', 'Alta de incidencias'), element('p', '', 'Este incremento cubre la lista y la edición limitada de incidencias existentes.'));
  const back = element('a', 'button button-secondary', 'Volver a incidencias');
  back.href = '#/incidents';
  panel.append(back);
  app.append(panel);
}

async function renderList() {
  app.replaceChildren(element('p', 'loading-state', 'Cargando incidencias…'));
  const url = routeQuery();
  const offset = Math.max(0, Number(url.get('offset')) || 0);
  const statusId = url.get('status') ?? '';
  const severityId = url.get('severity') ?? '';
  const areaId = url.get('area') ?? '';
  const params = new URLSearchParams({ offset: String(offset), limit: String(PAGE_SIZE) });
  if (statusId) params.set('status_value_id', statusId);
  if (severityId) params.set('severity_value_id', severityId);
  if (areaId && session.claims.role !== 'responsibleArea') params.set('responsible_area_id', areaId);

  try {
    const data = await api(`/incidents?${params}`);
    const heading = element('div', 'page-heading');
    const title = element('div');
    title.append(element('p', 'eyebrow', 'Operaciones'), element('h1', '', 'Incidencias'), element('p', '', `${data.total} resultado${data.total === 1 ? '' : 's'} en el ámbito autorizado.`));
    heading.append(title);
    app.replaceChildren(heading);

    const filters = element('form', 'panel filters');
    filters.append(
      selectField('Estado', 'statusFilter', session.catalogs.incidentStatus?.values ?? [], statusId),
      selectField('Severidad', 'severityFilter', session.catalogs.severity?.values ?? [], severityId),
    );
    if (session.claims.role !== 'responsibleArea') {
      filters.append(selectField('Área responsable', 'areaFilter', (session.references['responsible-areas'] ?? []).filter(area => area.is_active), areaId));
    }
    const apply = element('button', 'button button-primary', 'Aplicar filtros');
    apply.type = 'submit';
    filters.append(apply);
    filters.addEventListener('submit', event => {
      event.preventDefault();
      const next = routeQuery();
      next.delete('offset');
      const newStatus = document.querySelector('#statusFilter').value;
      const newSeverity = document.querySelector('#severityFilter').value;
      const newArea = document.querySelector('#areaFilter')?.value;
      if (newStatus) next.set('status', newStatus);
      if (newSeverity) next.set('severity', newSeverity);
      if (newArea) next.set('area', newArea);
      location.hash = `/incidents${next.size ? `?${next}` : ''}`;
    });
    app.append(filters);

    const panel = element('section', 'panel');
    if (!data.items.length) {
      panel.append(element('div', 'empty-state', 'No hay incidencias para los filtros seleccionados.'));
    } else {
      const wrap = element('div', 'table-wrap');
      const table = document.createElement('table');
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      for (const label of ['Incidencia', 'Estado', 'Severidad', 'Área responsable', 'Clínica', 'Actualizada']) headerRow.append(element('th', '', label));
      thead.append(headerRow);
      const tbody = document.createElement('tbody');
      for (const incident of data.items) {
        const row = document.createElement('tr');
        const incidentCell = document.createElement('td');
        const link = element('a', 'incident-link', incident.incident_identifier);
        link.href = `#/incidents/${encodeURIComponent(incident.id)}`;
        if (!hasReadDetail()) {
          link.removeAttribute('href');
          link.setAttribute('aria-disabled', 'true');
          link.title = 'Este rol sólo puede consultar el resumen';
        }
        incidentCell.append(link, element('span', 'secondary-text', incident.title));
        row.append(incidentCell);
        row.append(makeCell(makePill(labelFor('incidentStatus', incident.status_value_id))));
        const severityKey = session.catalogs.severity?.values?.find(item => item.id === incident.severity_value_id)?.key ?? '';
        row.append(makeCell(makePill(labelFor('severity', incident.severity_value_id), severityKey)));
        row.append(makeCell(element('span', '', referenceLabel('responsible-areas', incident.responsible_area_id))));
        row.append(makeCell(element('span', '', referenceLabel('clinics', incident.clinic_id))));
        row.append(makeCell(element('span', '', dateLabel(incident.updated_at))));
        tbody.append(row);
      }
      table.append(thead, tbody);
      wrap.append(table);
      panel.append(wrap);
    }
    const footer = element('div', 'table-footer');
    footer.append(element('span', '', `Mostrando ${data.items.length ? offset + 1 : 0}–${offset + data.items.length} de ${data.total}`));
    const pagination = element('div', 'pagination');
    const previous = element('button', 'button button-secondary button-small', 'Anterior');
    previous.type = 'button';
    previous.disabled = offset === 0;
    previous.addEventListener('click', () => navigateList(offset - PAGE_SIZE));
    const next = element('button', 'button button-secondary button-small', 'Siguiente');
    next.type = 'button';
    next.disabled = offset + data.items.length >= data.total;
    next.addEventListener('click', () => navigateList(offset + PAGE_SIZE));
    pagination.append(previous, next);
    footer.append(pagination);
    panel.append(footer);
    app.append(panel);
  } catch (error) {
    showError(error, 'No se pudieron cargar las incidencias');
  }
}

function makeCell(child) {
  const cell = document.createElement('td');
  cell.append(child);
  return cell;
}

function navigateList(offset) {
  const query = routeQuery();
  if (offset > 0) query.set('offset', String(offset));
  else query.delete('offset');
  location.hash = `/incidents${query.size ? `?${query}` : ''}`;
}

function addReadonlyItem(grid, label, value) {
  const item = element('div', 'readonly-item');
  const term = element('dt', '', label);
  const description = element('dd', '', value || '—');
  item.append(term, description);
  grid.append(item);
}

async function renderDetail(id) {
  if (!hasReadDetail()) {
    showError(Object.assign(new Error('Tu rol puede consultar el resumen, pero no el detalle de incidencias.'), { status: 403 }), 'Detalle no disponible');
    return;
  }
  app.replaceChildren(element('p', 'loading-state', 'Cargando detalle…'));
  try {
    const incident = await api(`/incidents/${encodeURIComponent(id)}`);
    const back = element('p', 'breadcrumbs');
    const backLink = element('a', '', '← Volver a incidencias');
    backLink.href = '#/incidents';
    back.append(backLink);
    const heading = element('div', 'page-heading');
    const title = element('div');
    title.append(element('p', 'eyebrow', incident.incident_identifier), element('h1', 'incident-title', incident.title), element('p', 'incident-subtitle', `Creada ${dateLabel(incident.created_at)}`));
    heading.append(title);
    const detailGrid = element('div', 'detail-grid');
    const summary = element('section', 'detail-card');
    summary.append(element('h2', '', 'Resumen operativo'));
    const facts = element('dl', 'readonly-grid');
    addReadonlyItem(facts, 'Estado', labelFor('incidentStatus', incident.status_value_id));
    addReadonlyItem(facts, 'Severidad', labelFor('severity', incident.severity_value_id));
    addReadonlyItem(facts, 'Área responsable', referenceLabel('responsible-areas', incident.responsible_area_id));
    addReadonlyItem(facts, 'Clínica', referenceLabel('clinics', incident.clinic_id));
    addReadonlyItem(facts, 'Jurisdicción', referenceLabel('jurisdictions', incident.jurisdiction_id));
    addReadonlyItem(facts, 'Sistema afectado', referenceLabel('affected-systems', incident.affected_system_id));
    addReadonlyItem(facts, 'Canal de entrada', labelFor('entryChannel', incident.entry_channel_value_id));
    addReadonlyItem(facts, 'Tipo', labelFor('incidentType', incident.incident_type_value_id));
    addReadonlyItem(facts, 'Última actualización', dateLabel(incident.updated_at));
    summary.append(facts);

    const editor = element('section', 'detail-card');
    const ownAreaMatches = session.claims.role !== 'responsibleArea' || incident.responsible_area_id === session.claims.area_id;
    const canEdit = ownAreaMatches && (canEditGenerally() || canEditOwnArea());
    if (!canEdit) {
      editor.append(element('h2', '', 'Descripción'), element('p', '', incident.description));
      if (session.claims.role === 'responsibleArea') {
        editor.append(element('p', 'access-notice', 'La edición de título y descripción sólo está disponible cuando esta incidencia pertenece al área asignada a tu cuenta.'));
      } else {
        editor.append(element('p', 'access-notice', 'Tu perfil puede consultar esta incidencia, pero no tiene permiso de edición.'));
      }
    } else {
      editor.append(element('h2', '', 'Editar incidencia'));
      const form = element('form', 'edit-form');
      const titleLabel = element('label', 'field');
      titleLabel.append(element('span', '', 'Título'));
      const titleInput = document.createElement('input');
      titleInput.name = 'title';
      titleInput.required = true;
      titleInput.maxLength = 200;
      titleInput.value = incident.title;
      titleLabel.append(titleInput, element('span', 'field-hint', 'Máximo 200 caracteres. Describe el problema operativo sin datos de pacientes.'));
      const descriptionLabel = element('label', 'field');
      descriptionLabel.append(element('span', '', 'Descripción'));
      const description = document.createElement('textarea');
      description.name = 'description';
      description.required = true;
      description.maxLength = 10000;
      description.value = incident.description;
      descriptionLabel.append(description, element('span', 'field-hint', 'Máximo 10.000 caracteres. No incluyas información de salud protegida (PHI).'));
      const notice = element('div', 'privacy-notice', 'No incluyas nombres, identificadores, diagnósticos, notas clínicas ni capturas con datos de pacientes. Si detectas posible PHI, no la reproduzcas y sigue el procedimiento interno de escalado.');
      const feedback = element('p', 'feedback');
      feedback.setAttribute('role', 'status');
      const actions = element('div', 'form-actions');
      const cancel = element('a', 'button button-secondary', 'Cancelar');
      cancel.href = '#/incidents';
      const save = element('button', 'button button-primary', 'Guardar cambios');
      save.type = 'submit';
      actions.append(cancel, save);
      form.append(titleLabel, descriptionLabel, notice, feedback, actions);
      form.addEventListener('submit', async event => {
        event.preventDefault();
        save.disabled = true;
        feedback.className = 'feedback';
        feedback.textContent = 'Guardando…';
        try {
          const updated = await api(`/incidents/${encodeURIComponent(id)}`, {
            method: 'PATCH',
            body: JSON.stringify({ title: titleInput.value.trim(), description: description.value.trim() }),
          });
          feedback.className = 'feedback success';
          feedback.textContent = 'Cambios guardados.';
          setMessage('La API confirmó la actualización de la incidencia.', 'success');
          await renderDetail(updated.id);
        } catch (error) {
          feedback.className = 'feedback error';
          feedback.textContent = error.status === 403
            ? 'La API ha denegado la edición. Comprueba el permiso y el área responsable.'
            : error.status === 422
              ? 'La API rechazó los datos. Revisa los límites de texto y los campos requeridos.'
              : error.message;
          save.disabled = false;
        }
      });
      editor.append(form);
    }
    detailGrid.append(summary, editor);
    app.replaceChildren(back, heading, detailGrid);
  } catch (error) {
    showError(error, 'No se pudo cargar el detalle');
  }
}

connectionForm.addEventListener('submit', async event => {
  event.preventDefault();
  const apiUrl = document.querySelector('#apiUrl').value.trim();
  const token = document.querySelector('#token').value.trim();
  try {
    setMessage('Validando token y cargando catálogos…');
    await connect(apiUrl, token);
  } catch (error) {
    session.token = '';
    session.claims = null;
    document.querySelector('#token').value = '';
    showConnectionState(false);
    setMessage(error.status === 401 ? 'Token no válido o expirado. Comprueba las credenciales.' : error.message, 'error');
  }
});

disconnectButton.addEventListener('click', disconnect);
window.addEventListener('hashchange', renderRoute);
window.addEventListener('DOMContentLoaded', renderRoute);