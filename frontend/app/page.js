export const dynamic = "force-dynamic";

export default async function Home() {
  let state;
  try {
    const response = await fetch(`${process.env.BACKEND_URL}/status`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) throw new Error("Backend unavailable");
    const data = await response.json();
    if (data.status !== "ok" || data.database !== "connected") {
      throw new Error("Database unavailable");
    }
    state = "Backend accesible · PostgreSQL conectado";
  } catch {
    state = "No se puede confirmar la conexión con el backend y PostgreSQL.";
  }

  return (
    <main style={{ maxWidth: 720, margin: "80px auto", padding: 24, fontFamily: "system-ui" }}>
      <p>HealthCore Digital</p>
      <h1>MVP en marcha</h1>
      <p role="status">{state}</p>
      <nav aria-label="Aplicaciones del backoffice">
        <p><a href={process.env.BACKOFFICE_URL}>Incidencias operativas</a></p>
        <p><a href={`${process.env.BACKOFFICE_URL}/management/`}>Management</a></p>
      </nav>
      <p>Entorno local de aprendizaje. Sin datos de pacientes.</p>
    </main>
  );
}
