import Image from "next/image";
import healthcareTeam from "./assets/imgs/AdobeStock_2207054294.jpeg";
import styles from "./page.module.css";
import SectionHeading from "./section-heading";

export const dynamic = "force-dynamic";

function Icon({ name, className }) {
  const paths = {
    cross: <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7Z" />,
    incident: <><path d="M9 5H5v16h14V5h-4" /><rect x="9" y="3" width="6" height="4" rx="1" /><path d="M8 12h8m-8 4h5" /></>,
    management: <><path d="M4 5h16M4 12h16M4 19h16" /><circle cx="8" cy="5" r="2" /><circle cx="16" cy="12" r="2" /><circle cx="10" cy="19" r="2" /></>,
    arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
    heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />,
  };
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{paths[name]}</svg>;
}

function Brand({ compact = false }) {
  return (
    <span className={styles.brand}>
      <span className={styles.brandMark}><Icon name="cross" /></span>
      <span><span className={styles.brandName}>HealthCore</span>{!compact && <span className={styles.brandUnit}>DIGITAL</span>}</span>
    </span>
  );
}

export default async function Home() {
  let connected = false;
  try {
    const response = await fetch(`${process.env.BACKEND_URL}/status`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok) {
      const data = await response.json();
      connected = data.status === "ok" && data.database === "connected";
    }
  } catch {
    // Keep the landing and existing tool links available during an outage.
  }

  const backofficeUrl = process.env.BACKOFFICE_URL;
  const tools = [
    {
      name: "Gestión de incidencias",
      description: "Registra, consulta y realiza el seguimiento de las incidencias operativas de nuestros centros.",
      icon: "incident",
      href: backofficeUrl,
      color: styles.coralIcon,
      label: "Acceder a incidencias",
    },
    {
      name: "Management",
      description: "Consulta catálogos, datos de referencia y registros de auditoría, según tus permisos de acceso.",
      icon: "management",
      href: `${backofficeUrl}/management/`,
      color: styles.tealIcon,
      label: "Acceder a Management",
    },
  ];

  return (
    <div className={styles.page}>
      <a className={styles.skipLink} href="#contenido">Saltar al contenido</a>
      <header className={styles.header}>
        <div className={`${styles.container} ${styles.headerInner}`}>
          <a href="#inicio" className={styles.brandLink} aria-label="HealthCore Digital, inicio"><Brand /></a>
          <nav aria-label="Navegación principal" className={styles.nav}>
            <a href="#herramientas">Herramientas</a>
            <a href="#acerca">Acerca de HealthCore</a>
          </nav>
        </div>
      </header>

      <main id="contenido">
        <section id="inicio" className={styles.hero} aria-labelledby="welcome-title">
          <div className={`${styles.container} ${styles.heroInner}`}>
            <div className={styles.heroCopy}>
              <p className={styles.eyebrow}><span /> Un espacio para nuestros equipos</p>
              <h1 id="welcome-title">Tecnología al servicio de una <span>mejor atención.</span></h1>
              <p className={styles.intro}>Bienvenido a HealthCore Digital, el espacio donde nuestros equipos encuentran herramientas para simplificar la gestión sanitaria, optimizar los procesos y dedicar más tiempo a lo que realmente importa: las personas.</p>
              <a href="#herramientas" className={styles.primaryButton}>Explorar herramientas <Icon name="arrow" /></a>
            </div>
            <figure className={styles.heroVisual}>
              <div className={styles.imageFrame}>
                <Image src={healthcareTeam} alt="Ilustración de profesionales sanitarios colaborando con herramientas digitales en la recepción de un centro de salud." className={styles.heroImage} sizes="(max-width: 800px) 100vw, 55vw" preload fetchPriority="high" />
              </div>
              <figcaption className={styles.imageCaption}><span className={styles.captionIcon}><Icon name="heart" /></span><span>La tecnología nos conecta.<br /><strong>Las personas nos inspiran.</strong></span></figcaption>
            </figure>
          </div>
        </section>

        <section id="herramientas" className={`${styles.container} ${styles.toolsSection}`} aria-labelledby="tools-title">
          <SectionHeading
            className={styles.sectionHeading}
            id="tools-title"
            eyebrow={{ className: styles.eyebrow, text: "TU TRABAJO, MÁS SENCILLO" }}
            title="Nuestras herramientas"
            description="Accede a los recursos digitales que acompañan el día a día de nuestros equipos."
          />
          <div className={styles.toolGrid}>
            {tools.map((tool) => (
              <article className={styles.toolCard} key={tool.name}>
                <span className={`${styles.toolIcon} ${tool.color}`}><Icon name={tool.icon} /></span>
                <h3>{tool.name}</h3>
                <p>{tool.description}</p>
                <a href={tool.href} className={styles.toolLink}>{tool.label} <Icon name="arrow" /></a>
              </article>
            ))}
          </div>
        </section>

        <section id="acerca" className={`${styles.container} ${styles.aboutSection}`} aria-labelledby="about-title">
          <div className={styles.aboutPanel}>
            <div className={styles.aboutIdentity}>
              <span className={styles.aboutIcon}><Icon name="cross" /></span>
              <SectionHeading
                id="about-title"
                eyebrow={{ className: styles.eyebrow, text: "CUIDAR ES LO QUE NOS UNE" }}
                title={<>Acerca de{" "}<br />HealthCore</>}
              />
            </div>
            <div className={styles.aboutCopy}>
              <p>HealthCore es una organización sanitaria especializada en atención ambulatoria, comprometida con ofrecer servicios accesibles y de calidad.</p>
              <p>A través de HealthCore Digital, impulsamos la modernización de nuestros procesos, conectamos equipos y desarrollamos soluciones que facilitan el trabajo diario de nuestros profesionales.</p>
              <p className={styles.aboutClosing}>Nuestro objetivo es sencillo: utilizar la tecnología para mejorar la eficiencia operativa y contribuir a una mejor experiencia de atención.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={`${styles.container} ${styles.footerInner}`}>
          <div><p className={styles.footerBrand}>HealthCore Digital</p><p>© {new Date().getUTCFullYear()} · Soluciones digitales para nuestros equipos</p></div>
          <div className={styles.footerNotes}>
            <p className={`${styles.connection} ${connected ? styles.connected : styles.disconnected}`} role="status"><span />{connected ? "Conexión disponible" : "Conexión no confirmada"}</p>
            <p>Entorno de desarrollo · Datos sintéticos</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
