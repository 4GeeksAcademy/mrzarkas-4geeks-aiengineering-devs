import Link from "next/link";
export default function NotFound() {
  return (
    <>
      <h1>Página no encontrada</h1>
      <Link href="/" prefetch={false}>
        Volver al inicio
      </Link>
    </>
  );
}
