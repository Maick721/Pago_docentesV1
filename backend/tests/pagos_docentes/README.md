# Pruebas de Pagos a Docentes

## Importar

En Postman importa estos dos archivos:

- `postman/PagoDocentes.postman_collection.json`
- `postman/PagoDocentes.local.postman_environment.json`

Selecciona el entorno **ITQ Conecta - Pagos docentes (local)**. Inicia el
backend local y ejecuta la carpeta **Smoke tests - solo lectura**. La colección
usa `http://127.0.0.1:8000` por defecto; si el servidor usa otro host o puerto,
cambia `baseUrl` en el entorno.

La colección prueba:

- Resumen, alertas, configuración y lookups.
- Listado paginado y contrato básico de las respuestas.
- Errores esperados para paginación, mes y estado inválidos.
- Control de acceso con bearer inválido (falla conocida: actualmente responde
  200 en vez de 401/403, hasta que el router use JWT).
- Historial inexistente y rechazo 422 de un alta con body incompleto.
- Tiempo de respuesta menor a 3 segundos en las consultas principales.

La solicitud de alta envía un body inválido. Debe detenerse en la validación
422 antes de llegar al servicio y no crea datos.

## Alcance y seguridad actual

Las solicitudes de lectura de pagos están disponibles actualmente sin JWT. Las
escrituras usan un `id_usuario` recibido en query, no la identidad validada por
el backend. Esto es un pendiente importante y significa que el módulo no debe
exponerse a usuarios reales hasta integrar JWT central y permisos por rol.

La colección no incluye cambios de estado exitosos (crear, marcar listo,
aprobar o pagar), porque esas llamadas escriben en PostgreSQL y el backend
apunta a la configuración indicada en `backend/.env`. No las ejecutes contra
la base de trabajo/producción. Para probar el flujo completo, prepara primero
una base desechable de pruebas con sus referencias (docente, período, carrera
y usuario), configura el backend para usar únicamente esa base y respalda o
elimina su contenido al finalizar.

En la revisión local se enviaron solicitudes HTTP de solo lectura y de
validación negativa al backend que estaba corriendo: resumen, alertas,
configuración, lookups, lista filtrada, parámetros inválidos y body incompleto.
De las 11 solicitudes comprobadas, 10 dieron el resultado esperado. La prueba
de bearer inválido es la única que falla: el GET devuelve 200 en vez de 401/403.
El historial inexistente devolvió 404 y la creación inválida devolvió 422; se
comparó el total de pagos antes y después y no cambió.

Estas solicitudes se ejecutaron directamente contra el backend local, no desde
la aplicación Postman/Newman. El JSON de la colección y el entorno, además de
la sintaxis de sus scripts JavaScript, se validaron localmente. Importa los
archivos y ejecuta la colección en Postman para guardar el reporte de esa
herramienta. Las pruebas Postman no sustituyen autorización ni pruebas de
concurrencia.

## Pruebas automatizadas

El backend de pagos usa FastAPI, Pydantic, SQLAlchemy asíncrono y PostgreSQL.
El contrato monetario vigente recibe el monto manualmente como `Decimal` y
exige un valor positivo con hasta dos decimales (`NUMERIC(12,2)`). El módulo no
implementa todavía un cálculo de nómina neta, tarifa por hora, deducciones,
bonificaciones, horas dictadas ni validación de cuenta bancaria; no se deben
suponer esas reglas en los resultados de prueba.

`test_pagos_docentes_schemas.py` valida contratos Pydantic: referencias
positivas, fechas, estado inicial, montos, umbrales y correo.
`test_payment_amount_contract.py` agrega dos pruebas unitarias del importe
decimal y una prueba HTTP de integración del endpoint con el servicio simulado:
comprueba el rechazo de importes inválidos y que `1250.10` llega sin alteración
al servicio. La prueba de integración no necesita PostgreSQL y no valida las
escrituras reales del servicio.

Desde `backend/`, ejecutar las pruebas enfocadas:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\pagos_docentes\test_payment_amount_contract.py tests\pagos_docentes\test_pagos_docentes_schemas.py -q
```

También se pueden ejecutar por separado:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\pagos_docentes\test_payment_amount_contract.py -q
..\.venv\Scripts\python.exe -m pytest tests\pagos_docentes\test_pagos_docentes_schemas.py -q
```

Para toda la suite del backend:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

Si todavía no existe el entorno virtual desde la raíz del repositorio:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
```

En la ejecución local de las dos suites enfocadas se obtuvieron **26 pruebas
pasadas**. Los resultados de cobertura deben medirse por separado; pasar las
pruebas enfocadas no implica que toda la lógica del módulo esté cubierta.

## Alcance funcional y datos de prueba

Las rutas de pago comienzan en `/api/v1/finance/payments`. Para ejecutar la
matriz que crea o cambia datos, preparar una base PostgreSQL **desechable** con:

- Docente activo `id_docente=10`, período activo `id_periodo=20`, carrera activa
  `id_carrera=30` y usuario existente `id_usuario=9`.
- Fixtures independientes por caso: módulo `100` en `EN_CURSO` sin pago;
  módulo `101` en `LISTO_PAGO` con pago `POR_PAGAR` de `1250.10`; módulo `102`
  en `EN_CURSO`; y módulo `103` en `LISTO_PAGO` con pago `POR_PAGAR`, sin
  aprobación vigente.
- Para el pago exitoso, preparar el fixture del módulo probado en `APROBADO`,
  con pago `POR_PAGAR` de `1250.10` y aprobación vigente. Cada caso debe
  restaurar su fixture para no depender del orden de ejecución.

Los estados de las respuestas son etiquetas de API: `EN_CURSO` se devuelve
como `borrador`, `LISTO_PAGO` como `listo`, `APROBADO` como `aprobado` y
`PAGADO` como `pagado`. No ejecutar casos de escritura en la base de trabajo o
producción.

## Matriz de casos de prueba

| ID del Caso | Requisito Asociado | Técnica de Diseño Aplicada | Precondiciones | Datos de Entrada exactos | Pasos de Ejecución | Resultado Esperado | Criterio de Aceptación |
|---|---|---|---|---|---|---|---|
| CP-PAG-001 | R-PAG-01 Alta de módulo | Partición de Equivalencia | Docente 10, período 20, carrera 30 y usuario 9 activos. | `POST /api/v1/finance/payments?id_usuario=9`; `{"id_docente":10,"id_periodo":20,"id_carrera":30,"nombre_modulo":"Matemática","fecha_inicio":"2026-01-01","fecha_fin":"2026-01-31"}` | Enviar el POST y consultar el módulo. | HTTP 201; respuesta `borrador`; persistencia `EN_CURSO`; historial inicial. | Se crea un único módulo con referencias y estado inicial correctos. |
| CP-PAG-002 | R-PAG-01 Fechas del módulo | Valores Límite | Referencias activas. | Mismo body de CP-PAG-001, pero `fecha_inicio="2026-01-31"` y `fecha_fin="2026-01-01"`. | Enviar el POST. | HTTP 422; no se crea módulo. | Fechas invertidas se rechazan sin escrituras. |
| CP-PAG-003 | R-PAG-02 Monto positivo | Valores Límite | Módulo 100 en `EN_CURSO`, sin pago. | `POST /api/v1/finance/payments/100/ready?id_usuario=9`; `{"monto":"0.01"}` | Enviar el POST; consultar módulo, pago e historial. | HTTP 200; estado `listo`; monto `0.01`; un pago `POR_PAGAR`. | Se acepta el menor monto válido y se crea exactamente un pago. |
| CP-PAG-004 | R-PAG-02 Rechazo de cero | Valores Límite | Módulo 100 en `EN_CURSO`, sin pago. | `{"monto":"0"}` en el POST `/100/ready`. | Enviar la solicitud y consultar el módulo. | HTTP 422; continúa `EN_CURSO`; no hay pago. | Cero no se acepta y no hay escritura parcial. |
| CP-PAG-005 | R-PAG-02 Rechazo de negativos | Partición de Equivalencia | Módulo 100 en `EN_CURSO`, sin pago. | `{"monto":"-0.01"}` en el POST `/100/ready`. | Enviar la solicitud. | HTTP 422; sin cambios persistidos. | Todo monto negativo se rechaza. |
| CP-PAG-006 | R-PAG-02 Precisión decimal | Valores Límite | Módulo 100 en `EN_CURSO`, sin pago. | `{"monto":"1.001"}` en el POST `/100/ready`. | Enviar la solicitud. | HTTP 422; sin cambios persistidos. | Se rechazan más de dos posiciones decimales. |
| CP-PAG-007 | R-PAG-02 Monto máximo permitido | Valores Límite | Módulo 100 en `EN_CURSO`, sin pago. | `{"monto":"9999999999.99"}` en el POST `/100/ready`. | Enviar la solicitud y leer el monto guardado. | HTTP 200; importe conservado exactamente. | Se acepta el máximo de `NUMERIC(12,2)`. |
| CP-PAG-008 | R-PAG-02 Monto superior al máximo | Valores Límite | Módulo 100 en `EN_CURSO`, sin pago. | `{"monto":"10000000000.00"}` en el POST `/100/ready`. | Enviar la solicitud. | HTTP 422; sin cambios persistidos. | Se rechazan más de 12 dígitos totales. |
| CP-PAG-009 | R-PAG-02 No duplicar pago del módulo | Transición de Estados | Módulo 100 ya en `LISTO_PAGO` con un pago `POR_PAGAR`. | Repetir POST `/100/ready?id_usuario=9` con `{"monto":"1250.10"}`. | Enviar la segunda solicitud; comparar conteo de pagos antes y después. | HTTP 409; no se crea otro pago. | Repetir la transición no duplica el pago ni el historial. |
| CP-PAG-010 | R-PAG-03 Aprobación válida | Transición de Estados | Módulo 101 en `LISTO_PAGO`, pago `POR_PAGAR`, sin aprobación vigente. | `POST /api/v1/finance/payments/101/approval?id_usuario=9`; `{"id_correo":null,"observacion":"Aprobación QA"}` | Enviar la solicitud; consultar estado, aprobación e historial. | HTTP 200; estado `aprobado`; aprobación `VIGENTE`, origen `MANUAL`. | Solo se crea una aprobación vigente y queda historial asociado al actor. |
| CP-PAG-011 | R-PAG-03 Estado no aprobable | Transición de Estados | Módulo 102 en `EN_CURSO`. | `POST /api/v1/finance/payments/102/approval?id_usuario=9`; `{"id_correo":null,"observacion":"Aprobación QA"}`. | Enviar la solicitud. | HTTP 409; sin aprobación. | Solo se aprueban módulos `LISTO_PAGO`. |
| CP-PAG-012 | R-PAG-04 Pago posterior a aprobación | Transición de Estados | Módulo aprobado, pago `POR_PAGAR` de `1250.10` y aprobación vigente. | `POST /api/v1/finance/payments/101/paid?id_usuario=9`; `{"observacion":"Transferencia","numero_factura":"F-2026-001","numero_comprobante":"TRX-0001"}` | Enviar la solicitud; consultar pago, módulo e historial. | HTTP 200; estado `pagado`; fecha no nula; comprobantes guardados; monto sin cambios. | Se paga solo un módulo aprobado y se preserva `1250.10`. |
| CP-PAG-013 | R-PAG-04 Rechazo antes de aprobar | Transición de Estados | Módulo 103 en `LISTO_PAGO` con pago `POR_PAGAR`, sin aprobación. | `POST /api/v1/finance/payments/103/paid?id_usuario=9`; `{"observacion":"Intento prematuro","numero_factura":null,"numero_comprobante":null}`. | Enviar la solicitud; consultar el pago. | HTTP 409; continúa `POR_PAGAR`. | No se marca como pagado antes de la aprobación. |
| CP-PAG-014 | R-PAG-05 Umbral de alertas | Valores Límite | Usuario 9 existente. | `PUT /api/v1/finance/payments/settings?id_usuario=9` con `{"valor":1}`, `{"valor":365}`, `{"valor":0}` y `{"valor":366}`. | Enviar cada solicitud y consultar la configuración tras las válidas. | 1 y 365 se aceptan; 0 y 366 devuelven 422. | Solo se persisten valores entre 1 y 365, inclusive. |
| CP-PAG-015 | R-PAG-05 Filtros y paginación | Valores Límite | API y base de prueba disponibles. | `GET /api/v1/finance/payments?page=0`; `GET /api/v1/finance/payments?page_size=101`; `GET /api/v1/finance/payments?mes=13`. | Enviar cada solicitud. | HTTP 422 en cada caso. | Página ≥1, tamaño 1–100 y mes 1–12. |
| CP-PAG-016 | R-PAG-06 Precisión del importe manual | Partición de Equivalencia | Módulo 100 en `EN_CURSO`, sin pago. | `POST /api/v1/finance/payments/100/ready?id_usuario=9`; `{"monto":"1250.10"}`. | Enviar la solicitud; comparar importe de respuesta y base de datos. | El importe queda `1250.10`, sin artefactos de punto flotante. | Cadena decimal, respuesta y valor persistido coinciden exactamente. |

### Casos de negocio por especificar

- **Doble pago por período:** la restricción actual es por `id_modulo`, no por
  docente/período. Como un docente puede tener varios módulos en el período,
  Product Owner debe definir la clave de duplicidad antes de esperar un rechazo
  por período.
- **Cálculo neto de nómina/honorarios:** no existe una función de cálculo. Antes
  de escribir el caso de cálculo exacto, aprobar tarifa, fuente de horas,
  deducciones, bonificaciones y modo de redondeo.
- **Horas máximas y cuenta bancaria:** no hay campos ni reglas implementadas
  para esas validaciones; son requisitos futuros, no resultados verificables
  del sistema actual.

## Escenarios de seguridad

1. **Autenticación y escalada de privilegios:** llamar a
   `GET /api/v1/finance/payments/summary` sin bearer y enviar
   `POST /api/v1/finance/payments/101/approval?id_usuario=10` como docente.
   Esperar 401/403 y ningún cambio. **Estado actual conocido:** las lecturas no
   requieren JWT y las escrituras confían en el `id_usuario` de la query; no
   hay autorización por rol. Bloqueador para producción.
2. **Integridad financiera:** después de aprobar un pago de `1250.10`, enviar
   `{"monto":"0.01","numero_factura":"F-2026-001"}` al endpoint `/paid`.
   Exigir que un campo inesperado se rechace o, como mínimo, que el pago
   conserve exactamente `1250.10`, con actor e historial correctos. Validar
   también que no se permita cambiar el actor mediante `id_usuario`.
3. **Inyección:** buscar con `q=%27%20OR%20%271%27%3D%271` y crear un nombre de
   módulo `<script>alert(1)</script>`. Esperar que el filtro sea un parámetro,
   que no se altere la consulta SQL y que el valor se muestre escapado en
   Angular, sin ejecución de HTML/JavaScript.

## Métricas sugeridas de salida

Los estándares IEEE 829 / ISO/IEC/IEEE 29119 e ISTQB no fijan porcentajes
universales de aprobación; estos son umbrales propuestos para el proyecto:

- 100 % de requisitos críticos trazados a casos y resultados.
- ≥80 % de cobertura de sentencias y ramas del módulo; ≥90 % en cálculo
  monetario y transiciones cuando exista esa lógica.
- 100 % de transiciones de estado y límites financieros críticos probados.
- Cero defectos abiertos Sev1/Sev2; máximo 0.5 defectos Sev3/Sev4 abiertos por
  KLOC, con aceptación documentada.
- Cero hallazgos de seguridad altos sin resolver; autenticación y permisos
  validados antes de producción.

Para medir cobertura, instalar `pytest-cov` en el entorno de desarrollo y,
desde `backend/`, ejecutar:

```powershell
..\.venv\Scripts\python.exe -m pip install pytest-cov
..\.venv\Scripts\python.exe -m pytest --cov=app.modules.pagos_docentes --cov-branch --cov-report=term-missing
```

## Pendientes para recordar

- Integrar JWT en todas las rutas de Pagos a Docentes y rechazar tokens inválidos.
- Tomar el usuario autenticado del JWT en lugar de confiar en `id_usuario` enviado
  por el cliente; aplicar permisos por rol.
- Ejecutar la colección en Postman/Newman y guardar el reporte.
- Probar las escrituras y transiciones de estado en una base desechable aislada,
  nunca en la base de trabajo o producción.
- Definir reglas de cálculo, horas, deduplicación por período y datos bancarios
  antes de diseñar pruebas para esos requisitos.
