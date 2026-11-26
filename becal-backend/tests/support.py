"""Apoyo para las pruebas: módulos de relleno y una base SQLite que imita a pymysql.

Si las dependencias reales (pymysql, flask-mail, flask-cors, flasgger) están
instaladas se usan tal cual; si no, se registran versiones mínimas de relleno
para poder ejecutar las pruebas sin MySQL ni red.
"""
import sqlite3
import sys
import types
from datetime import datetime


def instalar_modulos_de_relleno():
    try:
        import pymysql  # noqa: F401
    except ImportError:
        pymysql = types.ModuleType("pymysql")
        pymysql.cursors = types.SimpleNamespace(DictCursor=object)
        pymysql.err = types.SimpleNamespace(OperationalError=type("OperationalError", (Exception,), {}))

        def _sin_conexion(**_):
            raise pymysql.err.OperationalError("sin MySQL en pruebas")

        pymysql.connect = _sin_conexion
        sys.modules["pymysql"] = pymysql

    try:
        import flask_mail  # noqa: F401
    except ImportError:
        flask_mail = types.ModuleType("flask_mail")

        class Mail:
            enviados = []

            def init_app(self, app):
                pass

            def send(self, msg):
                Mail.enviados.append(msg)

        class Message:
            def __init__(self, subject="", recipients=None, **kw):
                self.subject, self.recipients, self.html = subject, recipients, None

        flask_mail.Mail, flask_mail.Message = Mail, Message
        sys.modules["flask_mail"] = flask_mail

    try:
        import flask_cors  # noqa: F401
    except ImportError:
        flask_cors = types.ModuleType("flask_cors")

        class CORS:
            def __init__(self, *a, **k):
                pass

            def init_app(self, app, **k):
                pass

        flask_cors.CORS = CORS
        sys.modules["flask_cors"] = flask_cors

    try:
        import flasgger  # noqa: F401
    except ImportError:
        flasgger = types.ModuleType("flasgger")

        class Swagger:
            def __init__(self, *a, **k):
                pass

            def init_app(self, app):
                pass

        flasgger.Swagger = Swagger
        sys.modules["flasgger"] = flasgger


instalar_modulos_de_relleno()

sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))

ESQUEMA = """
CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE,
  password_hash TEXT, taller_id INTEGER, rol TEXT NOT NULL DEFAULT 'ARTESANO', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE artesanias (id INTEGER PRIMARY KEY, nombre_taller TEXT, artesano_encargado TEXT, calidad_partidas TEXT,
  precio_promedio REAL, telefono_whatsapp TEXT, google_maps_url TEXT, imagen_url TEXT);
CREATE TABLE productos (id INTEGER PRIMARY KEY AUTOINCREMENT, artesano_id INTEGER, nombre_pieza TEXT,
  descripcion TEXT, precio REAL, calidad TEXT, imagenes TEXT);
CREATE TABLE reservas (id INTEGER PRIMARY KEY AUTOINCREMENT, taller_id INTEGER, nombre_visitante TEXT,
  email_visitante TEXT, telefono_visitante TEXT, numero_personas INTEGER DEFAULT 1, fecha_reserva TEXT,
  hora_reserva TEXT, estado TEXT DEFAULT 'pendiente', fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
  respuesta_artesano TEXT);
CREATE TABLE apartados (id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER, taller_id INTEGER,
  nombre_cliente TEXT, email_cliente TEXT, telefono_cliente TEXT, cantidad INTEGER DEFAULT 1,
  estado TEXT DEFAULT 'Pendiente', fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP, respuesta_artesano TEXT);
CREATE TABLE comentarios_taller (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT UNIQUE, tipo_solicitud TEXT,
  solicitud_id INTEGER, taller_id INTEGER, autor_nombre TEXT, contacto_verificado TEXT, calificacion INTEGER,
  titulo TEXT, descripcion TEXT, estado TEXT NOT NULL DEFAULT 'PENDIENTE', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP, motivo_rechazo TEXT, moderado_por INTEGER, moderado_en TEXT);
CREATE TABLE comentario_fotos (id INTEGER PRIMARY KEY AUTOINCREMENT, comentario_id INTEGER, foto_url TEXT, orden INTEGER);
CREATE TABLE mensajes_contacto (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT, telefono TEXT,
  mensaje TEXT, estado TEXT NOT NULL DEFAULT 'NUEVO', ip TEXT, created_at TEXT NOT NULL, leido_en TEXT);
"""


class _Cursor:
    def __init__(self, sq):
        self._c = sq.cursor()
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, sql, params=()):
        self._c.execute(sql.replace("%s", "?"), tuple(params or ()))
        self.lastrowid = self._c.lastrowid
        self.rowcount = self._c.rowcount

    def fetchone(self):
        fila = self._c.fetchone()
        return dict(fila) if fila is not None else None

    def fetchall(self):
        return [dict(f) for f in self._c.fetchall()]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Conexion:
    def __init__(self, sq):
        self._sq = sq

    def cursor(self):
        return _Cursor(self._sq)

    def commit(self):
        self._sq.commit()

    def rollback(self):
        self._sq.rollback()

    def close(self):  # la base en memoria es compartida: no se cierra
        pass


class BaseFalsa:
    def __init__(self):
        self.sq = sqlite3.connect(":memory:", check_same_thread=False)
        self.sq.row_factory = sqlite3.Row
        self.sq.executescript(ESQUEMA)

    def conexion(self, _config=None):
        return _Conexion(self.sq)

    def sql(self, consulta, params=()):
        cur = self.sq.execute(consulta, params)
        self.sq.commit()
        return [dict(f) for f in cur.fetchall()]
