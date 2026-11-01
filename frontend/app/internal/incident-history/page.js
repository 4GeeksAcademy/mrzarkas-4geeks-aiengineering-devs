import HistoryWorkspace from './workspace';

export const dynamic = 'force-dynamic';
export const metadata = { title: 'Cronología interna · HealthCore', robots: { index: false, follow: false } };

export default function IncidentHistoryPage() {
  return <main style={{ maxWidth: 960, margin: 'auto', padding: 24, fontFamily: 'system-ui' }}>
    <a href="/">HealthCore Digital</a>
    <h1>Cronología operativa</h1>
    <p>Vista interna de solo lectura. Desarrollo con datos sintéticos; sin información de pacientes.</p>
    <HistoryWorkspace />
  </main>;
}
