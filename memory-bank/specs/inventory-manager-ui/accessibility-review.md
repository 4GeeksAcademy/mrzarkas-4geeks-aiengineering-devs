# Inventory UI — revisión manual pendiente

Estado: NOT RUN para los casos de esta lista. No constituye certificación WCAG ni evidencia de ejecución. Referencias: spec§14, tareas018–019 y plan§21.

## Entorno

Usar exclusivamente la API temporal sintética y el backoffice compilado descritos en plan§21. No usar la base compartida ni tokens reales. Registrar fecha, versión de macOS/Chrome/VoiceOver, viewport original, rol sintético y resultado por caso. No incluir JWT, nombres reales ni grabaciones de credenciales.

## Casos para ejecutar

| ID | Procedimiento | Resultado requerido | Evidencia pendiente |
| --- | --- | --- | --- |
| M01 | En Chrome, abrir dashboard y catálogo; menú Ver/Zoom200%, luego400%; comprobar porcentaje del menú. Repetir detalle, stock, reorden y auditoría con roles autorizados. Restablecer100% al acabar. | Texto y acciones completos; sin scroll horizontal de página; tabla con scroll local accesible. | Porcentaje real y resultado por vista |
| M02 | Sólo Tab/Shift+Tab: salto a contenido, menú, filtros, campos, paginación y región de tabla; flechas para scroll local. | Orden lógico, foco visible, sin trampa ni elementos enfocados ocultos. | Secuencia y anomalías |
| M03 | Manager: completar entrada con3 packs sin enviar; abrir confirmación con Enter; recorrer Tab/Shift+Tab y cerrar Escape. Repetir conteo y compensación sobre original cargado. | Foco inicial en Cancelar; foco contenido en diálogo; nombre/contexto/cantidad legibles; Escape devuelve al botón de origen. | Resultado por diálogo |
| M04 | VoiceOver: recorrer encabezados, regiones y tablas en catálogo/detalle/stock/auditoría. | Un h1 por vista; nombres de campos y estado; caption y asociación de encabezados de tabla. | Transcripción breve de anuncios reales |
| M05 | VoiceOver: consulta lenta y vacía, error de lectura simulado sólo en fixture, validación nativa y error422 sintético; corregir campos. | Carga/vacío/error anunciados; error asociado al campo; recuperación con teclado. | Anuncios y foco por estado |
| M06 | VoiceOver: respuesta perdida en fixture después de escritura sintética; navegar entre rutas. | Aviso incierto anunciado y accesible; escrituras bloqueadas; reconocimiento explícito, sin afirmar fracaso de la operación. | Anuncios y estado de botones |
| M07 | VoiceOver: operación aceptada en fixture y desconexión. | Confirmación/saldo anunciado; identidad y contenido remoto retirados al desconectar. | Anuncios reales |
| M08 | Revisar foco, hover, controles activos, avisos y confirmaciones en todas las vistas. | Texto normal≥4,5:1, texto grande≥3:1, límites informativos/foco≥3:1; estado no depende sólo de color. Controles inactivos exentos de contraste, pero identificables. | Pares de colores y ratio por estado |

La evidencia automatizada existente (axe, viewport320/393/768/1350, CSS200%, borde5,55:1, Escape/retorno de foco) está en plan.md. No sustituye M01 ni anuncios reales M04–M07.

## Registro de ejecución

Por caso: fecha · herramienta/versión · vista/rol · pasos realmente realizados · PASS/FAIL/NOT RUN · anuncio/foco/ratio observado · defecto y referencia de arreglo, si existe. Completar sólo tras observarlo. No registrar PASS por inspección de atributos ARIA.

## Bloqueo observado

El acceso a Chrome nativo tardó470s y encontró una llamada Meet activa. No se modificó ni interrumpió esa ventana; no se ejecutaron zoom ni VoiceOver. El servidor temporal iniciado para esta revisión se detuvo. La tarea018 sigue PARTIAL y019 BLOCKED.
