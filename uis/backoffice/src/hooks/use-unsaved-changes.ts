"use client";
import { useEffect, useRef, useState } from "react";
/** Draft values remain in their form. Only the dirty flag is retained in memory. */
export function useUnsavedChanges() {
  const [dirty, setDirty] = useState(false);
  const current = useRef(dirty);
  current.current = dirty;
  useEffect(() => {
    const unload = (event: BeforeUnloadEvent) => {
      if (current.current) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    const navigate = (event: MouseEvent) => {
      const anchor =
        event.target instanceof Element ? event.target.closest("a") : null;
      if (
        !current.current ||
        !anchor ||
        anchor.getAttribute("href")?.startsWith("#") ||
        event.defaultPrevented
      )
        return;
      if (
        !window.confirm(
          "Hay cambios sin guardar. ¿Quieres salir de este formulario?",
        )
      ) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", unload);
    document.addEventListener("click", navigate, true);
    return () => {
      window.removeEventListener("beforeunload", unload);
      document.removeEventListener("click", navigate, true);
    };
  }, []);
  return {
    markDirty: () => setDirty(true),
    markClean: () => {
      current.current = false;
      setDirty(false);
    },
  };
}
