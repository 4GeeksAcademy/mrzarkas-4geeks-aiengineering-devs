---
title: "Documentación de componentes"
description: "Mantiene la documentación de los componentes completa y bilingüe."
scope: project
alwaysApply: false
globs:
  - "uis/**"
  - "services/**"
  - "agents/**"
  - "skills/**"
  - "mcps/**"
  - "workflows/**"
  - "packages/**"
---

Cada componente independiente debe incluir:
- `README.md`
- `README.es.md`

Cuando un cambio modifique la instalación, configuración, uso o comportamiento público de un componente, actualiza ambos archivos README.

Reglas:
- No documentes el cambio únicamente en uno de los dos idiomas.
- Mantén ambos README coherentes respecto al comportamiento documentado.
- No crees documentación duplicada fuera del componente cuando corresponda documentarla en el propio componente.
