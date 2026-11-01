'use client';
import dynamic from 'next/dynamic';
import LazyErrorBoundary from './lazy-error-boundary';
import { useRef, useState } from 'react';

const Timeline = dynamic(() => import('./timeline'), { loading: () => <p role="status">Cargando cronología…</p>, ssr: false });

export default function HistoryWorkspace() {
  const [token, setToken] = useState('');
  const [incident, setIncident] = useState('');
  const [data, setData] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const pending = useRef(null);
  const epoch = useRef(0);
  function disconnect() {
    epoch.current++;
    pending.current?.abort();
    setToken(''); setIncident(''); setData(null); setBusy(false); setMessage('Desconectado.');
  }
  async function load(event) {
    event.preventDefault();
    const generation = ++epoch.current;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true); setData(null); setMessage('Consultando historial autorizado…');
    try {
      const response = await fetch('/api/incident-history', { method: 'POST', cache: 'no-store', signal: controller.signal,
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ incident }) });
      if (generation !== epoch.current) return;
      if (!response.ok) throw new Error(response.status === 401 ? 'Token inválido o expirado.' : response.status === 403 ? 'Acceso denegado para este ámbito.' : `No se pudo consultar el historial (${response.status}).`);
      const result = await response.json();
      if (generation !== epoch.current) return;
      setData(result); setMessage('Historial cargado.');
    } catch (error) {
      if (generation === epoch.current && error.name !== 'AbortError') setMessage(error.message);
    } finally { if (generation === epoch.current) setBusy(false); }
  }
  return <section>
    <form onSubmit={load}>
      <p><label>JWT de desarrollo <input type="password" autoComplete="off" required value={token} onChange={event => { epoch.current++; pending.current?.abort(); setBusy(false); setData(null); setToken(event.target.value); }} /></label></p>
      <p><label>UUID de incidencia sintética <input required value={incident} onChange={event => { epoch.current++; pending.current?.abort(); setBusy(false); setData(null); setIncident(event.target.value); }} /></label></p>
      <button disabled={busy} type="submit">Consultar cronología</button>{' '}
      <button type="button" onClick={disconnect}>Desconectar</button>
    </form>
    <p role="status" aria-live="polite">{message}</p>
    <div aria-busy={busy}>{data && <LazyErrorBoundary><Timeline statusHistory={data.statusHistory} assignmentHistory={data.assignmentHistory} /></LazyErrorBoundary>}</div>
  </section>;
}
