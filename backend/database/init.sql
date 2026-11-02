CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Estructura inicial del módulo de pagos. Docker ejecuta este archivo
-- únicamente al crear un volumen de PostgreSQL vacío.
CREATE SCHEMA IF NOT EXISTS financiera;

CREATE TABLE IF NOT EXISTS financiera.pagos_docentes (
    id UUID PRIMARY KEY,
    docente VARCHAR(160) NOT NULL,
    correo_docente VARCHAR(254) NOT NULL,
    modulo VARCHAR(160) NOT NULL,
    carrera VARCHAR(160) NOT NULL,
    periodo_academico VARCHAR(80) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    monto NUMERIC(12, 2),
    modelo VARCHAR(20) NOT NULL DEFAULT 'carrera',
    datos_modelo JSONB,
    estado VARCHAR(20) NOT NULL DEFAULT 'borrador',
    listo_para_pago_en TIMESTAMPTZ,
    aprobado_en TIMESTAMPTZ,
    aprobado_por VARCHAR(254),
    referencia_aprobacion VARCHAR(500),
    aprobado_por_correo BOOLEAN NOT NULL DEFAULT FALSE,
    pagado_en TIMESTAMPTZ,
    creado_en TIMESTAMPTZ NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_pagos_docentes_periodo_carrera
    ON financiera.pagos_docentes (periodo_academico, carrera);
CREATE INDEX IF NOT EXISTS ix_pagos_docentes_estado
    ON financiera.pagos_docentes (estado);
CREATE INDEX IF NOT EXISTS ix_pagos_docentes_modelo
    ON financiera.pagos_docentes (modelo);

CREATE TABLE IF NOT EXISTS financiera.historial_pagos_docentes (
    id UUID PRIMARY KEY,
    pago_id UUID NOT NULL
        REFERENCES financiera.pagos_docentes (id) ON DELETE CASCADE,
    evento VARCHAR(40) NOT NULL,
    detalle TEXT NOT NULL,
    actor VARCHAR(254) NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_historial_pagos_docentes_pago
    ON financiera.historial_pagos_docentes (pago_id, creado_en);

CREATE TABLE IF NOT EXISTS financiera.configuracion_pagos (
    id INTEGER PRIMARY KEY,
    umbral_atraso_dias INTEGER NOT NULL DEFAULT 30,
    umbral_aprobacion_dias INTEGER NOT NULL DEFAULT 7,
    actualizado_en TIMESTAMPTZ NOT NULL
);
