-- ============================================================
-- ITQ CONECTA - CAMBIOS AL ESQUEMA pagos_docentes
-- Versión : 1
-- Fecha   : 2026-10-22
-- Autor   : [Tu nombre]
-- Documento: "Control de cambios - Esquema pagos_docentes"
--
-- Notas:
--  * Todos los cambios son aditivos: no borran ni modifican datos.
--  * Se puede ejecutar más de una vez (usa IF NOT EXISTS).
--  * Todo corre en una sola transacción: si algo falla, no se aplica nada.
--  * Las fechas se guardan en UTC como TIMESTAMP, igual que el resto de la BD.
--
-- ANTES DE EJECUTAR:
--  1. Hacer copia de seguridad.
--  2. Verificar que ningún módulo tenga más de un pago (el índice único fallaría):
--       SELECT id_modulo, COUNT(*) FROM pagos_docentes.pagos
--       GROUP BY id_modulo HAVING COUNT(*) > 1;
--     Si devuelve filas, resolverlas antes de continuar.
--
-- EJECUTAR:
--   psql -d <base_de_datos> -f pagos_docentes_cambios_v1.sql
-- ============================================================

-- Esta versión fue reemplazada por pagos_docentes_runtime_compat_v2.sql.
-- Aborta dentro de una transacción para evitar crear configuración/fallos_correo
-- paralelos o agregar un CHECK de estados incompatible con el esquema actual.
BEGIN;
DO $$
BEGIN
    RAISE EXCEPTION 'Migración obsoleta. Use pagos_docentes_runtime_compat_v2.sql.';
END $$;

ROLLBACK;

/*
El contenido histórico queda como referencia; no se ejecuta tras el ROLLBACK.


-- ------------------------------------------------------------
-- 1. MODULOS: datos que necesitan los Excel y el flujo de alertas
-- ------------------------------------------------------------
ALTER TABLE pagos_docentes.modulos
    ADD COLUMN IF NOT EXISTS codigo_eva   VARCHAR(40),                      -- Código del módulo en la plataforma EVA
    ADD COLUMN IF NOT EXISTS modelo       VARCHAR(20) NOT NULL DEFAULT 'CARRERA', -- CARRERA o VALIDACION
    ADD COLUMN IF NOT EXISTS contrato     VARCHAR(80),                      -- Tipo de contrato del docente
    ADD COLUMN IF NOT EXISTS fecha_listo  TIMESTAMP,                        -- Cuándo se marcó "listo para pago" (UTC)
    ADD COLUMN IF NOT EXISTS datos_modelo JSONB;                            -- Campos propios de cada modelo

-- El modelo solo puede tomar dos valores.
ALTER TABLE pagos_docentes.modulos DROP CONSTRAINT IF EXISTS ck_modulos_modelo;
ALTER TABLE pagos_docentes.modulos
    ADD CONSTRAINT ck_modulos_modelo CHECK (modelo IN ('CARRERA', 'VALIDACION'));

-- Estados del flujo. NOT VALID: se aplica a los datos nuevos y no revisa los
-- existentes (por si hubiera valores en otro formato). Se valida al final.
ALTER TABLE pagos_docentes.modulos DROP CONSTRAINT IF EXISTS ck_modulos_estado;
ALTER TABLE pagos_docentes.modulos
    ADD CONSTRAINT ck_modulos_estado
    CHECK (estado IN ('BORRADOR', 'LISTO', 'APROBADO', 'PAGADO')) NOT VALID;


-- ------------------------------------------------------------
-- 2. APROBACIONES: quién registró la aprobación
--    (NULL cuando la registra el sistema desde un correo)
-- ------------------------------------------------------------
ALTER TABLE pagos_docentes.aprobaciones
    ADD COLUMN IF NOT EXISTS id_usuario BIGINT REFERENCES core.usuarios(id_usuario);


-- ------------------------------------------------------------
-- 3. PAGOS: factura y un solo pago por módulo
-- ------------------------------------------------------------
ALTER TABLE pagos_docentes.pagos
    ADD COLUMN IF NOT EXISTS numero_factura VARCHAR(80);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pagos_modulo
    ON pagos_docentes.pagos (id_modulo);


-- ------------------------------------------------------------
-- 4. HISTORIAL: quién ejecutó el cambio de estado
-- ------------------------------------------------------------
ALTER TABLE pagos_docentes.historial
    ADD COLUMN IF NOT EXISTS id_usuario BIGINT REFERENCES core.usuarios(id_usuario);


-- ------------------------------------------------------------
-- 5. CONFIGURACION (tabla nueva): umbrales de atraso, una sola fila
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos_docentes.configuracion (
    id                     INTEGER   PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    umbral_atraso_dias     INTEGER   NOT NULL DEFAULT 30
                           CHECK (umbral_atraso_dias BETWEEN 1 AND 365),
    umbral_aprobacion_dias INTEGER   NOT NULL DEFAULT 7      -- PROVISIONAL: confirmar con Financiero
                           CHECK (umbral_aprobacion_dias BETWEEN 1 AND 365),
    fecha_actualizacion    TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    id_usuario             BIGINT    REFERENCES core.usuarios(id_usuario)
);

-- Fila inicial con los valores por defecto.
INSERT INTO pagos_docentes.configuracion (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;


-- ------------------------------------------------------------
-- 6. FALLOS_CORREO (tabla nueva): correos de aprobación no procesados
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos_docentes.fallos_correo (
    id_fallo           BIGSERIAL PRIMARY KEY,
    fecha_recepcion    TIMESTAMP,
    remitente          VARCHAR(254),
    asunto             TEXT,
    motivo             TEXT      NOT NULL,                 -- Por qué no se pudo procesar
    revisado           BOOLEAN   NOT NULL DEFAULT FALSE,
    fecha_revision     TIMESTAMP,
    id_usuario_revisor BIGINT    REFERENCES core.usuarios(id_usuario)
);


-- ------------------------------------------------------------
-- 7. INDICES: filtros, ficha por docente y alertas
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_modulos_estado
    ON pagos_docentes.modulos (estado);

CREATE INDEX IF NOT EXISTS ix_modulos_docente
    ON pagos_docentes.modulos (id_docente);

CREATE INDEX IF NOT EXISTS ix_modulos_periodo_carrera
    ON pagos_docentes.modulos (periodo, carrera);

CREATE INDEX IF NOT EXISTS ix_aprobaciones_modulo
    ON pagos_docentes.aprobaciones (id_modulo, fecha_aprobacion);

CREATE INDEX IF NOT EXISTS ix_historial_modulo
    ON pagos_docentes.historial (id_modulo, fecha);

CREATE INDEX IF NOT EXISTS ix_alertas_modulo_tipo
    ON pagos_docentes.alertas (id_modulo, tipo, fecha_alerta DESC);

CREATE INDEX IF NOT EXISTS ix_fallos_correo_pendientes
    ON pagos_docentes.fallos_correo (fecha_recepcion)
    WHERE revisado = FALSE;

COMMIT;


-- ============================================================
-- PASOS OPCIONALES (ejecutar aparte, después de revisar los datos)
-- ============================================================

-- A) Validar el CHECK de estados sobre los datos existentes.
--    Si falla, ver qué filas no cumplen:
--      SELECT DISTINCT estado FROM pagos_docentes.modulos;
-- ALTER TABLE pagos_docentes.modulos VALIDATE CONSTRAINT ck_modulos_estado;

-- B) Hacer obligatorios los campos clave. Fallan si hay filas con NULL.
-- ALTER TABLE pagos_docentes.modulos       ALTER COLUMN id_docente SET NOT NULL;
-- ALTER TABLE pagos_docentes.modulos       ALTER COLUMN estado     SET NOT NULL;
-- ALTER TABLE pagos_docentes.aprobaciones  ALTER COLUMN id_modulo  SET NOT NULL;
-- ALTER TABLE pagos_docentes.pagos         ALTER COLUMN id_modulo  SET NOT NULL;
-- ALTER TABLE pagos_docentes.alertas       ALTER COLUMN id_modulo  SET NOT NULL;
-- ALTER TABLE pagos_docentes.historial     ALTER COLUMN id_modulo  SET NOT NULL;


-- ============================================================
-- VERIFICACIÓN (ejecutar después del script)
-- ============================================================

-- Columnas nuevas:
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'pagos_docentes'
--   AND column_name IN ('codigo_eva','modelo','contrato','fecha_listo',
--                       'datos_modelo','id_usuario','numero_factura')
-- ORDER BY table_name, column_name;

-- Configuración inicial (debe devolver una fila: 1, 30, 7):
-- SELECT * FROM pagos_docentes.configuracion;


-- ============================================================
-- REVERSIÓN (deshace todo; las columnas nuevas pierden sus datos)
-- ============================================================
-- BEGIN;
-- DROP TABLE IF EXISTS pagos_docentes.fallos_correo;
-- DROP TABLE IF EXISTS pagos_docentes.configuracion;
-- DROP INDEX IF EXISTS pagos_docentes.ix_alertas_modulo_tipo;
-- DROP INDEX IF EXISTS pagos_docentes.ix_historial_modulo;
-- DROP INDEX IF EXISTS pagos_docentes.ix_aprobaciones_modulo;
-- DROP INDEX IF EXISTS pagos_docentes.ix_modulos_periodo_carrera;
-- DROP INDEX IF EXISTS pagos_docentes.ix_modulos_docente;
-- DROP INDEX IF EXISTS pagos_docentes.ix_modulos_estado;
-- DROP INDEX IF EXISTS pagos_docentes.ux_pagos_modulo;
-- ALTER TABLE pagos_docentes.historial     DROP COLUMN IF EXISTS id_usuario;
-- ALTER TABLE pagos_docentes.pagos         DROP COLUMN IF EXISTS numero_factura;
-- ALTER TABLE pagos_docentes.aprobaciones  DROP COLUMN IF EXISTS id_usuario;
-- ALTER TABLE pagos_docentes.modulos       DROP CONSTRAINT IF EXISTS ck_modulos_estado;
-- ALTER TABLE pagos_docentes.modulos       DROP CONSTRAINT IF EXISTS ck_modulos_modelo;
-- ALTER TABLE pagos_docentes.modulos
--     DROP COLUMN IF EXISTS datos_modelo,
--     DROP COLUMN IF EXISTS fecha_listo,
--     DROP COLUMN IF EXISTS contrato,
--     DROP COLUMN IF EXISTS modelo,
--     DROP COLUMN IF EXISTS codigo_eva;
-- COMMIT;
*/
