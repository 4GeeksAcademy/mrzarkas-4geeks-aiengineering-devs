'use client';
import dynamic from 'next/dynamic';
import LazyErrorBoundary from './lazy-error-boundary';
import { useMemo, useState } from 'react';
import { chronology } from './chronology.mjs';

const EventDetails = dynamic(() => import('./event-details'), { loading: () => <p role="status">Cargando detalle del evento…</p>, ssr: false });

export default function Timeline({ statusHistory, assignmentHistory }) {
  // Selection changes re-render this component; immutable history references
  // remain stable until another authorized fetch replaces the dataset.
  const events = useMemo(() => chronology(statusHistory, assignmentHistory), [statusHistory, assignmentHistory]);
  const [selected, setSelected] = useState(null);
  if (!events.length) return <p>Sin eventos de historial.</p>;
  return <section aria-label="Historial de cambios">
    <ol>{events.map(event => <li key={`${event.kind}:${event.id}`}>
      <button type="button" aria-expanded={selected === event} onClick={() => setSelected(selected === event ? null : event)}>
        {event.kind === 'status' ? 'Cambio de estado' : 'Cambio de área'} · {new Date(event.at).toLocaleString('es')}
      </button>
      {selected === event && <LazyErrorBoundary><EventDetails event={event} /></LazyErrorBoundary>}
    </li>)}</ol>
  </section>;
}
