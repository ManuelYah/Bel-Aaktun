"""Pruebas de la migración y del administrador inicial."""
import logging
import unittest
from unittest import mock

from tests import support  # noqa: F401
from tests.support import BaseFalsa

from app import bootstrap
from app.security import es_hash, verificar_password


class PruebasDeArranque(unittest.TestCase):
    def setUp(self):
        self.db = BaseFalsa()
        self.log = logging.getLogger("prueba")

    def cursor(self):
        return self.db.conexion().cursor()

    def test_las_contrasenas_en_texto_plano_se_convierten_a_hash_una_sola_vez(self):
        self.db.sq.executemany(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?,?,?,?)",
            [("A", "a@x.com", "123456", "ARTESANO"), ("B", "b@x.com", "otra-clave", "ARTESANO")],
        )
        self.db.sq.commit()
        bootstrap.proteger_contrasenas(self.cursor(), self.log)
        filas = self.db.sql("SELECT email, password_hash FROM usuarios ORDER BY id")
        self.assertTrue(all(es_hash(f["password_hash"]) for f in filas))
        self.assertTrue(verificar_password(filas[0]["password_hash"], "123456"))
        self.assertTrue(verificar_password(filas[1]["password_hash"], "otra-clave"))
        antes = [f["password_hash"] for f in filas]
        bootstrap.proteger_contrasenas(self.cursor(), self.log)  # no vuelve a cifrar un hash
        self.assertEqual(antes, [f["password_hash"] for f in self.db.sql("SELECT password_hash FROM usuarios ORDER BY id")])

    def test_crea_el_administrador_solo_si_no_existe(self):
        cfg = {"ADMIN_EMAIL": "admin@belaaktun.com", "ADMIN_PASSWORD": "una-clave-larga-1", "ADMIN_NOMBRE": "Admin"}
        bootstrap.asegurar_administrador(self.cursor(), cfg, self.log)
        bootstrap.asegurar_administrador(self.cursor(), cfg, self.log)
        filas = self.db.sql("SELECT * FROM usuarios")
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["rol"], "ADMIN")
        self.assertTrue(verificar_password(filas[0]["password_hash"], "una-clave-larga-1"))

    def test_no_convierte_a_administrador_una_cuenta_de_artesano(self):
        self.db.sq.execute("INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES ('A','a@x.com','h','ARTESANO')")
        self.db.sq.commit()
        cfg = {"ADMIN_EMAIL": "a@x.com", "ADMIN_PASSWORD": "una-clave-larga-1", "ADMIN_NOMBRE": "Admin"}
        bootstrap.asegurar_administrador(self.cursor(), cfg, self.log)
        self.assertEqual(self.db.sql("SELECT rol FROM usuarios")[0]["rol"], "ARTESANO")

    def test_sin_variables_no_crea_nada(self):
        bootstrap.asegurar_administrador(self.cursor(), {"ADMIN_EMAIL": "", "ADMIN_PASSWORD": "", "ADMIN_NOMBRE": "x"}, self.log)
        self.assertEqual(self.db.sql("SELECT COUNT(*) AS n FROM usuarios")[0]["n"], 0)


class CursorQueRegistra:
    """Simula information_schema para comprobar qué DDL se ejecuta."""

    def __init__(self, existentes):
        self.existentes, self.sentencias, self._ultimo = existentes, [], None

    def execute(self, sql, params=None):
        self.sentencias.append(" ".join(sql.split()))
        self._ultimo = (sql, params)

    def fetchone(self):
        sql, params = self._ultimo
        if "information_schema" in sql:
            return (1,) if tuple(params) in self.existentes else None
        return None


class PruebasDeMigracion(unittest.TestCase):
    def test_en_una_base_antigua_agrega_columnas_y_tabla(self):
        cur = CursorQueRegistra(existentes=set())
        bootstrap.migrar_esquema(cur, logging.getLogger("p"))
        ddl = "\n".join(cur.sentencias)
        self.assertIn("ADD COLUMN estado VARCHAR(12) NOT NULL DEFAULT 'APROBADO'", ddl)
        self.assertIn("ALTER COLUMN estado SET DEFAULT 'PENDIENTE'", ddl)
        self.assertIn("ADD COLUMN rol VARCHAR(20)", ddl)
        self.assertIn("CREATE TABLE IF NOT EXISTS mensajes_contacto", ddl)
        self.assertIn("UPDATE comentario_fotos", ddl)

    def test_en_una_base_ya_migrada_no_altera_nada(self):
        existentes = {
            ("comentarios_taller", c) for c in ("estado", "motivo_rechazo", "moderado_por", "moderado_en")
        } | {("usuarios", "rol"), ("comentarios_taller", "idx_comentarios_estado")}
        cur = CursorQueRegistra(existentes)
        bootstrap.migrar_esquema(cur, logging.getLogger("p"))
        self.assertFalse([s for s in cur.sentencias if s.startswith("ALTER")])

    def test_reintenta_hasta_que_mysql_responde(self):
        intentos = []

        def conectar(**_):
            intentos.append(1)
            if len(intentos) < 3:
                raise bootstrap.pymysql.err.OperationalError("aún no")
            return "conexion"

        with mock.patch.object(bootstrap.pymysql, "connect", conectar), mock.patch.object(bootstrap.time, "sleep"):
            self.assertEqual(bootstrap._conectar_con_reintentos({}, logging.getLogger("p")), "conexion")
        self.assertEqual(len(intentos), 3)


if __name__ == "__main__":
    unittest.main()
