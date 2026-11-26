"""Tareas de arranque: migraciones, contraseñas con hash y administrador.

Todo es idempotente: se puede ejecutar en cada inicio sin duplicar nada.
"""
import time

import pymysql

from app.security import ROL_ADMIN, ROL_ARTESANO, es_hash, hash_password

REINTENTOS_CONEXION = 30
ESPERA_ENTRE_REINTENTOS = 2  # segundos


def _conectar_con_reintentos(db_config, log):
    ultimo_error = None
    for intento in range(1, REINTENTOS_CONEXION + 1):
        try:
            return pymysql.connect(**db_config)
        except pymysql.err.OperationalError as exc:
            ultimo_error = exc
            log.info("Esperando a MySQL (%s/%s)...", intento, REINTENTOS_CONEXION)
            time.sleep(ESPERA_ENTRE_REINTENTOS)
    raise RuntimeError(f"No se pudo conectar a MySQL: {ultimo_error}")


def _columna_existe(cursor, tabla, columna):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (tabla, columna),
    )
    return cursor.fetchone() is not None


def _indice_existe(cursor, tabla, indice):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME = %s
        """,
        (tabla, indice),
    )
    return cursor.fetchone() is not None


def migrar_esquema(cursor, log):
    # 1) Moderación de reseñas. Las reseñas que ya existían se marcan como
    #    APROBADO para que el foro no quede vacío; las nuevas nacen PENDIENTE.
    if not _columna_existe(cursor, "comentarios_taller", "estado"):
        cursor.execute(
            "ALTER TABLE comentarios_taller "
            "ADD COLUMN estado VARCHAR(12) NOT NULL DEFAULT 'APROBADO' AFTER descripcion"
        )
        cursor.execute(
            "ALTER TABLE comentarios_taller ALTER COLUMN estado SET DEFAULT 'PENDIENTE'"
        )
        log.info("Migración: comentarios_taller.estado agregado (existentes = APROBADO).")
    for columna, definicion in (
        ("motivo_rechazo", "VARCHAR(255) NULL"),
        ("moderado_por", "INT NULL"),
        ("moderado_en", "DATETIME NULL"),
    ):
        if not _columna_existe(cursor, "comentarios_taller", columna):
            cursor.execute(f"ALTER TABLE comentarios_taller ADD COLUMN {columna} {definicion}")
    if not _indice_existe(cursor, "comentarios_taller", "idx_comentarios_estado"):
        cursor.execute(
            "ALTER TABLE comentarios_taller ADD INDEX idx_comentarios_estado (estado, created_at)"
        )

    # 2) Rol de los usuarios.
    if not _columna_existe(cursor, "usuarios", "rol"):
        cursor.execute(
            "ALTER TABLE usuarios "
            f"ADD COLUMN rol VARCHAR(20) NOT NULL DEFAULT '{ROL_ARTESANO}' AFTER taller_id"
        )
        log.info("Migración: usuarios.rol agregado.")

    # 3) Mensajes del formulario de contacto.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mensajes_contacto (
          id INT NOT NULL AUTO_INCREMENT,
          nombre VARCHAR(120) NOT NULL,
          email VARCHAR(150) DEFAULT NULL,
          telefono VARCHAR(30) DEFAULT NULL,
          mensaje TEXT NOT NULL,
          estado VARCHAR(12) NOT NULL DEFAULT 'NUEVO',
          ip VARCHAR(45) DEFAULT NULL,
          created_at DATETIME NOT NULL,
          leido_en DATETIME DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_mensajes_estado (estado, created_at),
          KEY idx_mensajes_ip (ip, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # 4) Las fotos guardaban 'http://127.0.0.1:5000/...': ahora se guarda la ruta.
    cursor.execute(
        """
        UPDATE comentario_fotos
        SET foto_url = REPLACE(REPLACE(foto_url, 'http://127.0.0.1:5000', ''), 'http://localhost:5000', '')
        WHERE foto_url LIKE 'http://127.0.0.1:5000/%' OR foto_url LIKE 'http://localhost:5000/%'
        """
    )


def proteger_contrasenas(cursor, log):
    """Convierte a hash las contraseñas que aún estén en texto plano."""
    cursor.execute("SELECT id, password_hash FROM usuarios")
    pendientes = [fila for fila in cursor.fetchall() if not es_hash(fila["password_hash"])]
    for fila in pendientes:
        cursor.execute(
            "UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (hash_password(fila["password_hash"] or ""), fila["id"]),
        )
    if pendientes:
        log.warning("Se protegieron con hash %s contraseñas que estaban en texto plano.", len(pendientes))


def asegurar_administrador(cursor, config, log):
    email = config["ADMIN_EMAIL"]
    password = config["ADMIN_PASSWORD"]
    if not email or not password:
        cursor.execute("SELECT COUNT(*) AS n FROM usuarios WHERE rol = %s", (ROL_ADMIN,))
        if cursor.fetchone()["n"] == 0:
            log.warning(
                "No hay ningún administrador. Define ADMIN_EMAIL y ADMIN_PASSWORD "
                "(o ejecuta `python manage.py crear-admin`) para crear uno."
            )
        return

    cursor.execute("SELECT id, rol FROM usuarios WHERE LOWER(email) = %s", (email,))
    existente = cursor.fetchone()
    if existente is None:
        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, taller_id, rol) "
            "VALUES (%s, %s, %s, NULL, %s)",
            (config["ADMIN_NOMBRE"], email, hash_password(password), ROL_ADMIN),
        )
        log.info("Administrador creado: %s", email)
    elif existente["rol"] != ROL_ADMIN:
        log.warning(
            "ADMIN_EMAIL (%s) ya pertenece a una cuenta de artesano; no se modificó. "
            "Usa otro correo.",
            email,
        )


def ejecutar(app):
    log = app.logger
    conn = _conectar_con_reintentos(app.config["DB_CONFIG"], log)
    try:
        with conn.cursor() as cursor:
            migrar_esquema(cursor, log)
            proteger_contrasenas(cursor, log)
            asegurar_administrador(cursor, app.config, log)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
