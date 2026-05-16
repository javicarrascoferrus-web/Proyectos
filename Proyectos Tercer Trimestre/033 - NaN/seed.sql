PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO perfiles (id, nombre) VALUES
(1, 'administrador'),
(2, 'profesor'),
(3, 'alumno');

INSERT OR IGNORE INTO usuarios (id, nombre, apellidos, email, password, perfil_id, activo) VALUES
(1, 'Admin', 'Campus', 'admin@nan.local', '1234', 1, 1),
(2, 'Ana', 'Profesora', 'profesor@nan.local', '1234', 2, 1),
(3, 'Luis', 'Alumno', 'alumno@nan.local', '1234', 3, 1);

INSERT OR IGNORE INTO cursos (id, nombre, descripcion, activo) VALUES
(1, 'Desarrollo de Aplicaciones Multiplataforma', 'Curso de programación, bases de datos y desarrollo de software.', 1);

INSERT OR IGNORE INTO asignaturas (id, curso_id, nombre, descripcion, orden, activo) VALUES
(1, 1, 'Programación', 'Fundamentos de programación y desarrollo de aplicaciones.', 1, 1),
(2, 1, 'Bases de datos', 'Diseño, consultas SQL y gestión de bases de datos.', 2, 1),
(3, 1, 'Lenguajes de marcas', 'HTML, CSS, XML y JSON.', 3, 1);

INSERT OR IGNORE INTO matriculas (id, usuario_id, asignatura_id, tipo, activo) VALUES
(1, 3, 1, 'alumno', 1),
(2, 3, 2, 'alumno', 1),
(3, 3, 3, 'alumno', 1),
(4, 2, 1, 'profesor', 1),
(5, 2, 2, 'profesor', 1),
(6, 2, 3, 'profesor', 1);

INSERT OR IGNORE INTO unidades (id, asignatura_id, titulo, descripcion, orden) VALUES
(1, 1, 'Unidad 1. Introducción a la programación', 'Conceptos básicos de programación, variables y algoritmos.', 1),
(2, 1, 'Unidad 2. Estructuras de control', 'Condicionales, bucles y control del flujo.', 2),
(3, 2, 'Unidad 1. Modelo relacional', 'Tablas, claves primarias, claves foráneas y relaciones.', 1),
(4, 3, 'Unidad 1. HTML básico', 'Estructura inicial de una página HTML.', 1);

INSERT OR IGNORE INTO temas (id, unidad_id, titulo, descripcion, orden) VALUES
(1, 1, 'Variables y tipos de datos', 'Uso de variables, textos, números y booleanos.', 1),
(2, 1, 'Entrada y salida de datos', 'Mostrar información y recoger datos del usuario.', 2),
(3, 2, 'Condicionales', 'Uso de if, else y condiciones compuestas.', 1),
(4, 3, 'Tablas SQL', 'Creación y organización de tablas.', 1),
(5, 4, 'Documento HTML mínimo', 'Estructura básica con html, head y body.', 1);

INSERT OR IGNORE INTO lecciones (id, tema_id, titulo, descripcion, orden) VALUES
(1, 1, 'Qué es una variable', 'Una variable permite guardar información temporalmente durante la ejecución de un programa.', 1),
(2, 1, 'Tipos básicos', 'Los tipos básicos más comunes son números, cadenas de texto y valores booleanos.', 2),
(3, 3, 'Condicional if', 'El condicional if permite ejecutar código solamente si se cumple una condición.', 1),
(4, 4, 'Crear una tabla', 'Una tabla permite almacenar registros con una estructura de campos definida.', 1),
(5, 5, 'Primera página HTML', 'Una página HTML básica contiene etiquetas como html, head, title y body.', 1);

INSERT OR IGNORE INTO sesiones (id, leccion_id, titulo, fecha, descripcion) VALUES
(1, 1, 'Sesión 1. Variables', '2026-01-15', 'Ejemplos básicos de variables.'),
(2, 2, 'Sesión 2. Tipos de datos', '2026-01-17', 'Práctica con números, textos y booleanos.'),
(3, 3, 'Sesión 3. Condicionales', '2026-01-20', 'Resolución de ejercicios con if y else.'),
(4, 4, 'Sesión 1. Tablas SQL', '2026-01-18', 'Creación de tablas y campos.'),
(5, 5, 'Sesión 1. HTML básico', '2026-01-19', 'Creación de una primera página web.');

INSERT OR IGNORE INTO recursos (id, leccion_id, titulo, descripcion, url) VALUES
(1, 1, 'Apuntes de variables', 'Documento de apoyo sobre variables.', 'https://example.com/variables'),
(2, 4, 'Guía de SQL', 'Material introductorio para crear tablas SQL.', 'https://example.com/sql');

INSERT OR IGNORE INTO tareas (id, leccion_id, titulo, descripcion, fecha_entrega, puntuacion_maxima) VALUES
(1, 1, 'Ejercicio de variables', 'Crear un programa que utilice variables para calcular un resultado.', '2026-01-30', 10),
(2, 4, 'Crear una tabla SQL', 'Diseñar una tabla sencilla con varios campos.', '2026-02-05', 10);
