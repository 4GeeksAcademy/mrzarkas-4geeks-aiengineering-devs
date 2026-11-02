"use client";
import { useEffect, useState } from "react";

export function integer(
  value: FormDataEntryValue | string | null,
  minimum = 1,
) {
  const raw = String(value ?? "").trim();
  const number = Number(raw);
  if (
    !raw ||
    !Number.isInteger(number) ||
    number < minimum ||
    number > 1000000000
  )
    throw new Error(
      "Introduce una cantidad entera dentro del rango permitido.",
    );
  return number;
}

export function presentation(fd: FormData) {
  const pack_label = String(fd.get("pack_label") ?? "").trim() || null;
  const pack_size = integer(fd.get("pack_size"));
  if (!pack_label && pack_size !== 1)
    throw new Error("Sin presentación la equivalencia debe ser 1.");
  return { pack_label, pack_size };
}

export function EventTime({ value }: { value: string }) {
  const [local, setLocal] = useState("");
  useEffect(() => {
    const date = new Date(value);
    if (!Number.isNaN(date.valueOf()))
      setLocal(
        new Intl.DateTimeFormat("es", {
          dateStyle: "medium",
          timeStyle: "long",
        }).format(date),
      );
  }, [value]);
  return (
    <span>
      <time dateTime={value}>{local || value}</time>
      <br />
      <small>UTC: {value}</small>
    </span>
  );
}

export function ReceivedAt({ data }: { data: unknown }) {
  const [value, setValue] = useState("");
  useEffect(() => {
    setValue(data === undefined ? "" : new Date().toISOString());
  }, [data]);
  return value ? (
    <p className="notice">
      Recepción de la consulta (hora local; no timestamp del servidor):{" "}
      <EventTime value={value} />
    </p>
  ) : null;
}
