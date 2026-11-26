CREATE DATABASE IF NOT EXISTS becal_db;
USE becal_db;

-- Tabla de Artesanos / Cuevas
CREATE TABLE IF NOT EXISTS artesanos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nombre_cueva VARCHAR(100) NOT NULL,
    telefono_whatsapp VARCHAR(20) NOT NULL,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    direccion VARCHAR(255),
    foto_url VARCHAR(255)
);

-- Tabla de Catálogo de Sombreros / Artesanías
CREATE TABLE IF NOT EXISTS artesanias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artesano_id INT,
    nombre_es VARCHAR(100) NOT NULL,
    nombre_en VARCHAR(100),
    nombre_may VARCHAR(100),
    calidad_partidas VARCHAR(50), -- Ej. '4 Partidas - Finísimo'
    precio_mxn DECIMAL(10,2) NOT NULL,
    imagen_url VARCHAR(255),
    FOREIGN KEY (artesano_id) REFERENCES artesanos(id) ON DELETE CASCADE
);

-- Tabla de Registro de Intenciones de Reserva
CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artesano_id INT,
    nombre_cliente VARCHAR(100) NOT NULL,
    telefono_cliente VARCHAR(20) NOT NULL,
    fecha_visita DATE NOT NULL,
    numero_personas INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Pendiente',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artesano_id) REFERENCES artesanos(id)
);

-- Datos iniciales de prueba (Semilla)
INSERT INTO artesanos (nombre, nombre_cueva, telefono_whatsapp, latitud, longitud, direccion) 
VALUES ('Don Luis Canul', 'Cueva Los Sietes', '529961234567', 20.4578, -90.0245, 'Calle 20 x 15, Centro, Bécal');

INSERT INTO artesanias (artesano_id, nombre_es, nombre_en, nombre_may, calidad_partidas, precio_mxn)
VALUES (1, 'Sombrero Jipi Japa Tradicional', 'Traditional Jipi Japa Hat', 'P''óok Xa''an Jipi', '2 Partidas', 850.00);