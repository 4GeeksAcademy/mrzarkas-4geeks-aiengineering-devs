"use client";
import {
  createContext,
  useContext,
  useEffect,
  useId,
  useRef,
  type ReactNode,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { ApiError } from "@/lib/api/client";
export const FieldErrors = createContext<Record<string, string>>({});
export function PageHeader({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <p className="eyebrow">HealthCore Digital · Recursos internos</p>
      <h1>{title}</h1>
      {children}
    </header>
  );
}
export function Button({
  children,
  secondary = false,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { secondary?: boolean }) {
  return (
    <button
      type="button"
      className={`button ${secondary ? "button-secondary" : "button-primary"}`}
      {...props}
    >
      {children}
    </button>
  );
}
export function Field({
  label,
  hint,
  error,
  children,
  id,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
  id: string;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children}
      {hint && (
        <span id={`${id}-hint`} className="field-hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={`${id}-error`} className="error">
          {error}
        </span>
      )}
    </div>
  );
}
export function Input({
  label,
  hint,
  error,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const errors = useContext(FieldErrors);
  error = error ?? (props.name ? errors[props.name] : undefined);
  const auto = useId();
  const id = props.id ?? auto;
  return (
    <Field {...{ label, hint, error, id }}>
      <input
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={
          [hint && `${id}-hint`, error && `${id}-error`]
            .filter(Boolean)
            .join(" ") || undefined
        }
      />
    </Field>
  );
}
export function Select({
  label,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const errors = useContext(FieldErrors);
  const error = props.name ? errors[props.name] : undefined;
  const auto = useId();
  const id = props.id ?? auto;
  return (
    <Field label={label} error={error} id={id}>
      <select
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
      >
        {children}
      </select>
    </Field>
  );
}
export function Textarea({
  label,
  hint,
  error,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const errors = useContext(FieldErrors);
  error = error ?? (props.name ? errors[props.name] : undefined);
  const auto = useId();
  const id = props.id ?? auto;
  return (
    <Field {...{ label, hint, error, id }}>
      <textarea
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={
          [hint && `${id}-hint`, error && `${id}-error`]
            .filter(Boolean)
            .join(" ") || undefined
        }
      />
    </Field>
  );
}
export function Alert({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <p
      className={error ? "notice error" : "notice"}
      role={error ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
export function LoadingState() {
  return <p role="status">Cargando…</p>;
}
export function EmptyState() {
  return <p role="status">Sin resultados.</p>;
}
export function ErrorState({
  error,
  retry,
}: {
  error: Error;
  retry?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, [error]);
  return (
    <div ref={ref} tabIndex={-1}>
      <Alert error>{error.message}</Alert>
      {retry && <Button onClick={retry}>Reintentar lectura</Button>}
    </div>
  );
}
export function MutationState({
  mutation,
  verify,
}: {
  mutation: {
    error: ApiError | null;
    success: string;
    acknowledge: () => void;
  };
  verify?: () => void;
}) {
  return (
    <>
      {mutation.error && <Alert error>{mutation.error.message}</Alert>}
      {mutation.error?.uncertain && (
        <div className="actions">
          <Button secondary onClick={verify}>
            Consultar datos e historial
          </Button>
          <Button secondary onClick={mutation.acknowledge}>
            He verificado el resultado en la API
          </Button>
        </div>
      )}
      {mutation.success && <Alert>{mutation.success}</Alert>}
    </>
  );
}
export function DataTable<T>({
  rows,
  columns,
  label,
  rowKey,
}: {
  rows: T[];
  columns: { label: string; cell: (row: T) => ReactNode }[];
  label: string;
  rowKey: (row: T) => string;
}) {
  if (!rows.length) return <EmptyState />;
  return (
    <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>
      <table>
        <caption className="sr-only">{label}</caption>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th key={i} scope="col">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((c, i) => (
                <td key={i}>{c.cell(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Pagination({
  offset,
  size,
  total,
  onChange,
}: {
  offset: number;
  size: number;
  total?: number;
  onChange: (offset: number) => void;
}) {
  return (
    <nav aria-label="Paginación" className="actions">
      <Button
        secondary
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - size))}
      >
        Anterior
      </Button>
      <span>
        Desde {offset + 1}
        {total !== undefined ? ` · ${total} resultados` : ""}
      </span>
      <Button
        secondary
        disabled={total !== undefined && offset + size >= total}
        onClick={() => onChange(offset + size)}
      >
        Siguiente
      </Button>
    </nav>
  );
}
export function ConfirmationDialog({
  label,
  disabled,
  children,
  onConfirm,
}: {
  label: string;
  disabled?: boolean;
  children: ReactNode;
  onConfirm: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const title = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="button button-primary"
        disabled={disabled}
        onClick={() => ref.current?.showModal()}
      >
        {label}
      </button>
      <dialog
        ref={ref}
        aria-labelledby={title}
        onClose={() => trigger.current?.focus()}
      >
        <h2 id={title}>Confirmar operación</h2>
        {children}
        <div className="actions">
          <Button secondary autoFocus onClick={() => ref.current?.close()}>
            Cancelar
          </Button>
          <Button
            onClick={() => {
              ref.current?.close();
              onConfirm();
            }}
          >
            Confirmar
          </Button>
        </div>
      </dialog>
    </>
  );
}
