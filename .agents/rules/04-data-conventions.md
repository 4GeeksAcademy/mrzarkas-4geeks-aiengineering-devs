---
title: "Organización y ciclo del dato"
description: "Mantiene separados los datos de origen, los pipelines de transformación, los datos procesados y los recursos de evaluación."
scope: project
alwaysApply: false
globs:
  - "data/**"
---

Mantén los datos organizados según su función:

- `data/raw/`: datos fuente sin transformar.
- `data/pipelines/`: código y configuración de los procesos ETL.
- `data/process/`: datos procesados.
- `data/eval/`: datasets y resultados de evaluación.

Reglas:
- No sobrescribas datos de `raw/` durante las transformaciones.
- Escribe los resultados derivados en `process/` o `eval/` según corresponda.
- No mezcles código ETL con datasets.
- Toda métrica nueva debe documentar explícitamente su fórmula, tratamiento de valores nulos, periodo temporal y criterio de comparación cuando exista.
