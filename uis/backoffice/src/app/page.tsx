import { PageHeader } from "@/components/ui";
export default function Home() {
  return (
    <>
      <PageHeader title="Backoffice HealthCore" />
      <section className="panel">
        <h2>Herramientas operativas</h2>
        <p>
          Selecciona un módulo de la navegación. Los permisos y ámbitos los
          determina la API.
        </p>
        <p className="privacy-notice">
          Utiliza exclusivamente datos sintéticos. No incluyas datos de
          pacientes.
        </p>
      </section>
    </>
  );
}
