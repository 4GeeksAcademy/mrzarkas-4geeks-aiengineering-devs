'use client';
export default function EventDetails({ event }) {
  const status = event.kind === 'status';
  return <dl>
    <dt>Desde</dt><dd>{(status ? event.from_status_value_id : event.from_responsible_area_id) ?? '—'}</dd>
    <dt>Hasta</dt><dd>{status ? event.to_status_value_id : event.to_responsible_area_id}</dd>
    <dt>Motivo según política de auditoría</dt><dd>{event.reason ?? '—'}</dd>
  </dl>;
}
