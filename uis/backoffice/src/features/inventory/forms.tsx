"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useMutation } from "@/hooks/use-mutation";
import { Alert, Button, FieldErrors, MutationState } from "@/components/ui";
import { useUnsavedChanges } from "@/hooks/use-unsaved-changes";
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
}: {
  title: string;
  path: string;
  method?: "POST" | "PATCH";
  body: (fd: FormData) => T;
  children: ReactNode;
  refresh: () => void;
  confirm?: boolean;
  disabled?: boolean;
}) {
  const mutation = useMutation();
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
  async function execute() {
    if (payload.current === undefined) return;
    const result = await mutation.mutate(path, payload.current, method);
    if (result !== undefined) {
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
            setValidation("");
            try {
              payload.current = body(new FormData(e.currentTarget));
            } catch {
              setValidation("Revisa los valores y los campos obligatorios.");
              return;
            }
            if (confirm) dialog.current?.showModal();
            else void execute();
          }}
        >
          <fieldset
            disabled={
              disabled || mutation.pending || !!mutation.error?.uncertain
            }
          >
            <legend className="sr-only">{title}</legend>
            {children}
            <div className="actions">
              <button
                ref={submit}
                type="submit"
                className="button button-primary"
                disabled={disabled || mutation.pending}
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
