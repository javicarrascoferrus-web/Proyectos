PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS perfiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    perfil_id INTEGER NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (perfil_id) REFERENCES perfiles(id)
);

CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS asignaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

CREATE TABLE IF NOT EXISTS matriculas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    asignatura_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('alumno', 'profesor')),
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id)
);

CREATE TABLE IF NOT EXISTS unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asignatura_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER DEFAULT 0,
    FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id)
);

CREATE TABLE IF NOT EXISTS temas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER DEFAULT 0,
    FOREIGN KEY (unidad_id) REFERENCES unidades(id)
);

CREATE TABLE IF NOT EXISTS lecciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER DEFAULT 0,
    FOREIGN KEY (tema_id) REFERENCES temas(id)
);

CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leccion_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    fecha TEXT,
    descripcion TEXT,
    FOREIGN KEY (leccion_id) REFERENCES lecciones(id)
);

CREATE TABLE IF NOT EXISTS recursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leccion_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    url TEXT,
    FOREIGN KEY (leccion_id) REFERENCES lecciones(id)
);

CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leccion_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    fecha_entrega TEXT,
    puntuacion_maxima REAL DEFAULT 10,
    FOREIGN KEY (leccion_id) REFERENCES lecciones(id)
);
