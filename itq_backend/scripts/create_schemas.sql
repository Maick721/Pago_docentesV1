"""
scripts/create_schemas.sql
Script SQL de inicialización de esquemas de base de datos para ITQ Conecta.

Ejecutar en PostgreSQL ANTES de correr las migraciones de Alembic:
  psql -U postgres -d itq_db -f scripts/create_schemas.sql
"""

-- ─── Crear esquemas ─────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS graduacion;
CREATE SCHEMA IF NOT EXISTS docs;

-- ─── Extensiones útiles ─────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- Para búsquedas de texto similitud

-- ─── Esquema CORE ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core.personas (
    id_persona      BIGSERIAL PRIMARY KEY,
    cedula          VARCHAR(20)  NOT NULL UNIQUE,
    nombres         VARCHAR(150) NOT NULL,
    apellidos       VARCHAR(150) NOT NULL,
    correo          VARCHAR(255),
    telefono        VARCHAR(20),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo'
);
CREATE INDEX IF NOT EXISTS idx_personas_cedula ON core.personas(cedula);

CREATE TABLE IF NOT EXISTS core.roles (
    id_rol      BIGSERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    estado      VARCHAR(20)  NOT NULL DEFAULT 'activo'
);

CREATE TABLE IF NOT EXISTS core.usuarios (
    id_usuario              BIGSERIAL PRIMARY KEY,
    id_persona              BIGINT REFERENCES core.personas(id_persona) ON DELETE SET NULL,
    nombre_usuario          VARCHAR(100) NOT NULL UNIQUE,
    correo_institucional    VARCHAR(255) NOT NULL UNIQUE,
    contrasena_hash         VARCHAR(255) NOT NULL,
    estado                  VARCHAR(20)  NOT NULL DEFAULT 'activo',
    fecha_creacion          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usuarios_nombre ON core.usuarios(nombre_usuario);
CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON core.usuarios(correo_institucional);

CREATE TABLE IF NOT EXISTS core.usuario_rol (
    id_usuario_rol  BIGSERIAL PRIMARY KEY,
    id_usuario      BIGINT NOT NULL REFERENCES core.usuarios(id_usuario) ON DELETE CASCADE,
    id_rol          BIGINT NOT NULL REFERENCES core.roles(id_rol) ON DELETE CASCADE,
    fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo'
);

CREATE TABLE IF NOT EXISTS core.auditoria (
    id_auditoria    BIGSERIAL PRIMARY KEY,
    id_usuario      BIGINT REFERENCES core.usuarios(id_usuario) ON DELETE SET NULL,
    modulo          VARCHAR(100) NOT NULL,
    accion          VARCHAR(200) NOT NULL,
    tabla_afectada  VARCHAR(150),
    id_registro     BIGINT,
    fecha_hora      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    direccion_ip    VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON core.auditoria(id_usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha   ON core.auditoria(fecha_hora DESC);

-- ─── Tablas adicionales del core institucional ───────────────────────────────

-- PERMISOS
CREATE TABLE IF NOT EXISTS core.permisos (
    id_permiso   BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(100),
    descripcion  TEXT,
    accion       VARCHAR(100),
    estado       BOOLEAN
);

-- MODULOS
CREATE TABLE IF NOT EXISTS core.modulos (
    id_modulo    BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(100),
    descripcion  TEXT,
    estado       BOOLEAN
);

-- DEPARTAMENTOS / UNIDADES
CREATE TABLE IF NOT EXISTS core.unidades (
    id_unidad    BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(150),
    descripcion  TEXT,
    estado       BOOLEAN
);

-- ESTUDIANTES
CREATE TABLE IF NOT EXISTS core.estudiantes (
    id_estudiante    BIGSERIAL PRIMARY KEY,
    id_persona       BIGINT REFERENCES core.personas(id_persona),
    codigo_estudiante VARCHAR(50),
    estado           BOOLEAN
);

-- EMPLEADOS
CREATE TABLE IF NOT EXISTS core.empleados (
    id_empleado    BIGSERIAL PRIMARY KEY,
    id_persona     BIGINT REFERENCES core.personas(id_persona),
    id_unidad      BIGINT REFERENCES core.unidades(id_unidad),
    codigo_empleado VARCHAR(50),
    cargo          VARCHAR(100),
    fecha_ingreso  DATE,
    estado         BOOLEAN
);

-- CATALOGOS ACADEMICOS
CREATE TABLE IF NOT EXISTS core.catalogos_academicos (
    id_catalogo  BIGSERIAL PRIMARY KEY,
    tipo         VARCHAR(100),
    codigo       VARCHAR(50),
    nombre       VARCHAR(150),
    descripcion  TEXT,
    estado       BOOLEAN
);

-- ACADEMIC PROGRAMS
CREATE TABLE IF NOT EXISTS core.academic_programs (
    id_program   BIGSERIAL PRIMARY KEY,
    codigo       VARCHAR(50) NOT NULL UNIQUE,
    nombre       VARCHAR(200) NOT NULL,
    descripcion  TEXT,
    estado       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_academic_programs_codigo ON core.academic_programs(codigo);

-- ACADEMIC PERIODS
CREATE TABLE IF NOT EXISTS core.academic_periods (
    id_period    BIGSERIAL PRIMARY KEY,
    codigo       VARCHAR(50) NOT NULL UNIQUE,
    nombre       VARCHAR(100) NOT NULL,
    fecha_inicio TIMESTAMP,
    fecha_fin    TIMESTAMP,
    estado       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_academic_periods_codigo ON core.academic_periods(codigo);

-- CAMPUS
CREATE TABLE IF NOT EXISTS core.campus (
    id_campus    BIGSERIAL PRIMARY KEY,
    codigo       VARCHAR(50) NOT NULL UNIQUE,
    nombre       VARCHAR(200) NOT NULL,
    direccion    TEXT,
    estado       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_campus_codigo ON core.campus(codigo);

-- ACADEMIC MODALITIES
CREATE TABLE IF NOT EXISTS core.academic_modalities (
    id_modality  BIGSERIAL PRIMARY KEY,
    codigo       VARCHAR(50) NOT NULL UNIQUE,
    nombre       VARCHAR(150) NOT NULL,
    descripcion  TEXT,
    estado       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_academic_modalities_codigo ON core.academic_modalities(codigo);

-- ACADEMIC PARALLELS
CREATE TABLE IF NOT EXISTS core.academic_parallels (
    id_parallel  BIGSERIAL PRIMARY KEY,
    codigo       VARCHAR(50) NOT NULL UNIQUE,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  TEXT,
    estado       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_academic_parallels_codigo ON core.academic_parallels(codigo);

-- ─── Esquema DOCS ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS docs.file_assets (
    id_file_asset       BIGSERIAL PRIMARY KEY,
    nombre_original     VARCHAR(500) NOT NULL,
    nombre_almacenado   VARCHAR(500) NOT NULL UNIQUE,
    ruta                TEXT         NOT NULL,
    mime_type           VARCHAR(150),
    tamano_bytes        BIGINT,
    checksum_sha256     VARCHAR(64),
    fecha_subida        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    subido_por          BIGINT,
    activo              BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS docs.documents (
    id_document         BIGSERIAL PRIMARY KEY,
    titulo              VARCHAR(500) NOT NULL,
    descripcion         TEXT,
    tipo_documento      VARCHAR(100) NOT NULL,
    modulo_origen       VARCHAR(100) NOT NULL,
    id_entidad_origen   BIGINT,
    estado              VARCHAR(50)  NOT NULL DEFAULT 'borrador',
    fecha_creacion      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    creado_por          BIGINT,
    fecha_actualizacion TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS docs.document_versions (
    id_version      BIGSERIAL PRIMARY KEY,
    id_document     BIGINT NOT NULL REFERENCES docs.documents(id_document) ON DELETE CASCADE,
    id_file_asset   BIGINT NOT NULL REFERENCES docs.file_assets(id_file_asset) ON DELETE RESTRICT,
    numero_version  INTEGER      NOT NULL DEFAULT 1,
    comentario      TEXT,
    es_version_actual BOOLEAN    NOT NULL DEFAULT TRUE,
    fecha_version   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    creado_por      BIGINT
);

CREATE TABLE IF NOT EXISTS docs.document_reviews (
    id_review       BIGSERIAL PRIMARY KEY,
    id_document     BIGINT NOT NULL REFERENCES docs.documents(id_document) ON DELETE CASCADE,
    id_revisor      BIGINT NOT NULL,
    etapa           VARCHAR(100) NOT NULL,
    resultado       VARCHAR(50)  NOT NULL,
    comentario      TEXT,
    fecha_revision  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─── Esquema GRADUACION ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS graduacion.eventos (
    id_evento   BIGSERIAL PRIMARY KEY,
    nombre      VARCHAR(300) NOT NULL,
    fecha       TIMESTAMPTZ  NOT NULL,
    hora        TIME,
    sede        VARCHAR(300),
    jornada     VARCHAR(100),
    aforo       INTEGER,
    estado      VARCHAR(50)  NOT NULL DEFAULT 'activo'
);

CREATE TABLE IF NOT EXISTS graduacion.butacas (
    id_butaca   BIGSERIAL PRIMARY KEY,
    id_evento   BIGINT NOT NULL REFERENCES graduacion.eventos(id_evento) ON DELETE CASCADE,
    fila        VARCHAR(10)  NOT NULL,
    numero      INTEGER      NOT NULL,
    estado      VARCHAR(50)  NOT NULL DEFAULT 'disponible',
    UNIQUE(id_evento, fila, numero)
);

CREATE TABLE IF NOT EXISTS graduacion.pases (
    id_pase         BIGSERIAL PRIMARY KEY,
    id_evento       BIGINT NOT NULL REFERENCES graduacion.eventos(id_evento) ON DELETE RESTRICT,
    id_estudiante   BIGINT REFERENCES core.personas(id_persona) ON DELETE SET NULL,
    id_butaca       BIGINT REFERENCES graduacion.butacas(id_butaca) ON DELETE SET NULL,
    tipo            VARCHAR(50)  NOT NULL,
    fecha_emision   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    estado          VARCHAR(50)  NOT NULL DEFAULT 'emitido',
    cedula_invitado VARCHAR(20),
    nombre_invitado VARCHAR(300)
);
CREATE INDEX IF NOT EXISTS idx_pases_evento    ON graduacion.pases(id_evento);
CREATE INDEX IF NOT EXISTS idx_pases_estudiante ON graduacion.pases(id_estudiante);
CREATE INDEX IF NOT EXISTS idx_pases_cedula_inv ON graduacion.pases(cedula_invitado);

CREATE TABLE IF NOT EXISTS graduacion.qr (
    id_qr               BIGSERIAL PRIMARY KEY,
    id_pase             BIGINT NOT NULL UNIQUE REFERENCES graduacion.pases(id_pase) ON DELETE CASCADE,
    codigo              VARCHAR(500) NOT NULL UNIQUE,
    fecha_generacion    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    fecha_uso           TIMESTAMPTZ,
    utilizado           BOOLEAN      NOT NULL DEFAULT FALSE,
    id_usuario_valida   BIGINT REFERENCES core.usuarios(id_usuario) ON DELETE SET NULL,
    dispositivo_info    TEXT
);
CREATE INDEX IF NOT EXISTS idx_qr_codigo ON graduacion.qr(codigo);

-- ─── Datos iniciales ─────────────────────────────────────────────────────────

-- Roles del sistema
INSERT INTO core.roles (nombre, descripcion) VALUES
    ('administrador',  'Acceso total al sistema ITQ Conecta'),
    ('coordinador',    'Coordinador de eventos de graduación'),
    ('validador',      'Personal de validación de acceso en ceremonia'),
    ('consultor',      'Acceso de solo lectura')
ON CONFLICT (nombre) DO NOTHING;

-- Usuario administrador inicial (contraseña: Admin@ITQ2026)
-- Hash generado con bcrypt rounds=12
INSERT INTO core.usuarios (nombre_usuario, correo_institucional, contrasena_hash, estado)
VALUES (
    'admin',
    'admin@itq.edu.ec',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaRFCMFkxI0C0JR9HH9mNHqH6',
    'activo'
) ON CONFLICT (nombre_usuario) DO NOTHING;
