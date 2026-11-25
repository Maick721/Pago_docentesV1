-- Esquemas y tablas compartidas requeridas por Pagos a Docentes.
-- Ejecutar antes de inicializar las tablas propias de pagos_docentes:
--   psql -U postgres -d itq_db -f scripts/create_schemas.sql

-- ─── Crear esquemas ─────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS pagos_docentes;

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

-- DEPARTAMENTOS / UNIDADES
CREATE TABLE IF NOT EXISTS core.unidades (
    id_unidad    BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(150),
    descripcion  TEXT,
    estado       BOOLEAN
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

-- ─── Datos iniciales ─────────────────────────────────────────────────────────

-- Roles que pueden operar o aprobar pagos a docentes
INSERT INTO core.roles (nombre, descripcion) VALUES
    ('administrador',  'Acceso administrativo a Pagos a Docentes'),
    ('coordinador',    'Gestión de pagos a docentes'),
    ('financiero',     'Gestión y autorización de pagos a docentes'),
    ('tesorero',       'Confirmación de pagos aprobados')
ON CONFLICT (nombre) DO NOTHING;
