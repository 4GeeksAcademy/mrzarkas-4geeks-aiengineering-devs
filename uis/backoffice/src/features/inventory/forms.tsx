"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useMutation } from "@/hooks/use-mutation";
import { Alert, Button, FieldErrors, MutationState } from "@/components/ui";
import { useUnsavedChanges } from "@/hooks/use-unsaved-changes";
import { ApiError } from "@/lib/api/client";
import { useOperationState } from "./operation-state";
export const uuidPattern =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
export const text = (fd: FormData, name: string) =>
  String(fd.get(name) ?? "").trim();
export function OperationForm<T>({
  title,
  path,
  method = "POST",
  body,
  children,
  refresh,
  confirm = false,
  disabled = false,
  canSubmit = true,
  summary,
  context = "",
}: {
  title: string;
  path: string;
  method?: "POST" | "PATCH";
  body: (fd: FormData) => T;
  children: ReactNode;
  refresh: () => void;
  confirm?: boolean;
  disabled?: boolean;
  canSubmit?: boolean;
  summary?: ReactNode;
  context?: string;
}) {
  const mutation = useMutation();
  const operations = useOperationState();
  const [confirmed, setConfirmed] = useState<Record<string, unknown> | null>(
    null,
  );
  const draft = useUnsavedChanges();
  const form = useRef<HTMLFormElement>(null);
  useEffect(() => {
    if (mutation.error)
      form.current
        ?.querySelector<HTMLElement>('[aria-invalid="true"]')
        ?.focus();
  }, [mutation.error]);
  const dialog = useRef<HTMLDialogElement>(null);
  const submit = useRef<HTMLButtonElement>(null);
  const payload = useRef<T | undefined>(undefined);
  const [validation, setValidation] = useState("");
  useEffect(() => {
    if (operations?.acknowledged && mutation.error?.uncertain)
      mutation.acknowledge();
  }, [operations?.acknowledged]);
  useEffect(() => {
    payload.current = undefined;
    dialog.current?.close();
    setConfirmed(null);
  }, [path, context]);
  async function execute() {
    if (
      payload.current === undefined ||
      disabled ||
      !canSubmit ||
      operations?.blocked
    )
      return;
    if (operations && !operations.begin()) return;
    const sent = payload.current;
    let uncertain = false;
    const result = await mutation.mutate(
      path,
      sent,
      method,
      (value) => {
        if (!value || typeof value !== "object")
          throw new ApiError(
            0,
            "Resultado incierto: respuesta no verificable.",
            true,
          );
        const data = value as Record<string, unknown>;
        const configuration = path.endsWith("/configuration");
        if (
          configuration
            ? !data.item_id ||
              !data.clinic_id ||
              !Number.isInteger(data.reorder_point)
            : typeof data.id !== "string" ||
              !new RegExp(`^${uuidPattern}$`).test(data.id)
        )
          throw new ApiError(
            0,
            "Resultado incierto: respuesta no verificable.",
            true,
          );
        const expected = sent as Record<string, unknown>;
        if (
          ["item_id", "clinic_id"].some(
            (key) => expected[key] !== undefined && data[key] !== expected[key],
          )
        )
          throw new ApiError(
            0,
            "Resultado incierto: el contexto de la respuesta no coincide.",
            true,
          );
        if (
          path.endsWith("/correction") &&
          data.correction_of !== path.split("/").at(-2)
        )
          throw new ApiError(
            0,
            "Resultado incierto: el original de la respuesta no coincide.",
            true,
          );
        if (
          path === "/inventory/movements" &&
          (data.kind !== expected.kind ||
            (data.lot_id ?? null) !== (expected.lot_id ?? null))
        )
          throw new ApiError(
            0,
            "Resultado incierto: el movimiento confirmado no coincide.",
            true,
          );
        if (
          path.includes("/movements") &&
          (data.result !== "accepted" ||
            !Number.isInteger(data.delta) ||
            !Number.isInteger(data.previous_quantity) ||
            !Number.isInteger(data.resulting_quantity))
        )
          throw new ApiError(
            0,
            "Resultado incierto: movimiento no verificable.",
            true,
          );
      },
      (error) => {
        uncertain = error.uncertain;
        if (uncertain) operations?.unknown(`${title} · ${context}`);
      },
    );
    if (!uncertain) operations?.finish();
    if (result !== undefined) {
      setConfirmed(result as Record<string, unknown>);
      draft.markClean();
      refresh();
    }
  }
  return (
    <section className="panel">
      <h2>{title}</h2>
      <FieldErrors.Provider value={mutation.error?.fields ?? {}}>
        <form
          ref={form}
          onChange={draft.markDirty}
          onSubmit={(e) => {
            e.preventDefault();
            if (
              disabled ||
              !canSubmit ||
              operations?.blocked ||
              mutation.pending ||
              mutation.error?.uncertain
            )
              return;
            setValidation("");
            setConfirmed(null);
            try {
              payload.current = body(new FormData(e.currentTarget));
            } catch {
              setValidation(
                "Revisa los valores y los campos obligatorios. Las cantidades deben ser enteras; sin presentación, la equivalencia debe ser 1.",
              );
              return;
            }
            if (confirm) dialog.current?.showModal();
            else void execute();
          }}
        >
          <fieldset
            disabled={
              disabled ||
              mutation.pending ||
              !!mutation.error?.uncertain ||
              operations?.blocked
            }
          >
            <legend className="sr-only">{title}</legend>
            {children}
            <div className="actions">
              <button
                ref={submit}
                type="submit"
                className="button button-primary"
                disabled={disabled || !canSubmit || mutation.pending}
              >
                {mutation.pending ? "Enviando…" : title}
              </button>
            </div>
          </fieldset>
        </form>
      </FieldErrors.Provider>
      {validation && <Alert error>{validation}</Alert>}
      {mutation.error && Object.keys(mutation.error.fields).length > 0 && (
        <Alert error>
          Campos rechazados: {Object.keys(mutation.error.fields).join(", ")}.
        </Alert>
      )}
      <MutationState mutation={mutation} verify={refresh} />
      {confirmed && (
        <p role="status">
          Confirmación API: {String(confirmed.id ?? "configuración")}
          {confirmed.resulting_quantity !== undefined
            ? ` · Saldo previo ${confirmed.previous_quantity} · Diferencia ${confirmed.delta} · Saldo resultante ${confirmed.resulting_quantity}`
            : ""}
          {confirmed.correction_of
            ? ` · Compensa ${confirmed.correction_of}`
            : ""}
        </p>
      )}
      {confirm && (
        <dialog
          ref={dialog}
          aria-label={`Confirmar: ${title}`}
          onClose={() => submit.current?.focus()}
        >
          <h2>Confirmar operación</h2>
          <p>
            {title}. La API conservará el movimiento o evento y aplicará sus
            reglas de integridad.
          </p>
          {summary}
          {context && <p>Contexto confirmado: {context}</p>}
          <div className="actions">
            <Button secondary autoFocus onClick={() => dialog.current?.close()}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                dialog.current?.close();
                void execute();
              }}
            >
              Confirmar
            </Button>
          </div>
        </dialog>
      )}
    </section>
  );
}
