-- Ampliacion aditiva del esquema institucional de pagos docentes.
-- Primero debe haberse aplicado el DDL oficial de BD_ITQ_Conecta_pgAdmin.sql.
-- No recrea tablas ni modifica sus datos; agrega los datos del formulario
-- Carrera/Validacion que el backend conserva en pagos_docentes.modulos.

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
