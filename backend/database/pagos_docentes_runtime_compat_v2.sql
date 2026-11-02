BEGIN;

ALTER TABLE pagos_docentes.modulos
    ADD COLUMN IF NOT EXISTS modelo VARCHAR(20) NOT NULL DEFAULT 'CARRERA',
    ADD COLUMN IF NOT EXISTS contrato VARCHAR(80),
    ADD COLUMN IF NOT EXISTS datos_modelo JSONB;

ALTER TABLE pagos_docentes.modulos
    DROP CONSTRAINT IF EXISTS ck_modulos_modelo;

ALTER TABLE pagos_docentes.modulos
    ADD CONSTRAINT ck_modulos_modelo
    CHECK (modelo IN ('CARRERA', 'VALIDACION'));

COMMIT;
