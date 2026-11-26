"""Pruebas de la API (sin MySQL: usan SQLite en memoria).

    cd becal-backend && python -m unittest discover -s tests -t . -v
"""
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from tests import support  # noqa: F401  (registra módulos de relleno si hacen falta)
from tests.support import BaseFalsa

import pymysql
import yaml

from app import create_app
from app.security import hash_password, limite_login

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class PruebaBase(unittest.TestCase):
    def setUp(self):
        self.db = BaseFalsa()
        parche = mock.patch.object(pymysql, "connect", lambda **_: self.db.conexion())
        parche.start()
        self.addCleanup(parche.stop)

        self.app = create_app({
            "RUN_BOOTSTRAP": False, "TESTING": True,
            "SECRET_KEY": "clave-de-pruebas", "SECRET_KEY_DEFINIDA": True,
        })
        self.carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.carpeta, True)
        for destino in ("app.utils.carpeta_fotos", "app.routes.foro_routes.carpeta_fotos"):
            p = mock.patch(destino, lambda: self.carpeta)
            p.start()
            self.addCleanup(p.stop)

        self.cliente = self.app.test_client()
        limite_login.vaciar()

        self.db.sq.executemany(
            "INSERT INTO artesanias (id, nombre_taller) VALUES (?, ?)",
            [(1, "Taller Uno"), (2, "Taller Dos")],
        )
        self.admin_id = self._usuario("Admin", "admin@belaaktun.com", "clave-admin-123", None, "ADMIN")
        self.art1_id = self._usuario("Artesano 1", "uno@belaaktun.com", "clave-uno-123", 1, "ARTESANO")
        self.art2_id = self._usuario("Artesano 2", "dos@belaaktun.com", "clave-dos-123", 2, "ARTESANO")
        self.db.sq.commit()

    # ------------- ayudas
    def _usuario(self, nombre, email, password, taller_id, rol):
        cur = self.db.sq.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, taller_id, rol) VALUES (?,?,?,?,?)",
            (nombre, email, hash_password(password), taller_id, rol),
        )
        return cur.lastrowid

    def login(self, email, password):
        return self.cliente.post("/api/auth/login", json={"email": email, "password": password})

    def cabeceras(self, email, password):
        token = self.login(email, password).get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def admin(self):
        return self.cabeceras("admin@belaaktun.com", "clave-admin-123")

    def reserva_confirmada(self, taller_id=1, nombre="Ana Pérez", email="ana@correo.com", tel="9961072280"):
        cur = self.db.sq.execute(
            "INSERT INTO reservas (taller_id, nombre_visitante, email_visitante, telefono_visitante, "
            "fecha_reserva, hora_reserva, estado) VALUES (?,?,?,?,?,?,?)",
            (taller_id, nombre, email, tel, "2026-12-01", "10:00", "Confirmada"),
        )
        self.db.sq.commit()
        return cur.lastrowid

    def publicar_resena(self, reserva_id, fotos=None, titulo="Excelente", nombre="Ana Pérez", contacto="ana@correo.com"):
        datos = {
            "folio": f"RES-{reserva_id:03d}", "nombre": nombre, "contacto": contacto,
            "calificacion": "5", "titulo": titulo, "descripcion": "Muy bonito taller",
        }
        if fotos:
            datos["fotos"] = fotos
        return self.cliente.post("/api/foro/comentarios", data=datos, content_type="multipart/form-data")


class PruebasDeSesion(PruebaBase):
    def test_login_devuelve_token_y_rol(self):
        r = self.login("Admin@BelAaktun.com ", "clave-admin-123")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.get_json()
        self.assertTrue(cuerpo["token"])
        self.assertEqual(cuerpo["user"]["rol"], "ADMIN")
        self.assertNotIn("password_hash", cuerpo["user"])
        self.assertGreater(cuerpo["expires_at"], 0)

    def test_login_rechaza_clave_incorrecta_y_correo_inexistente(self):
        self.assertEqual(self.login("admin@belaaktun.com", "mala").status_code, 401)
        self.assertEqual(self.login("nadie@belaaktun.com", "x" * 12).status_code, 401)
        self.assertEqual(self.cliente.post("/api/auth/login", json={}).status_code, 400)

    def test_contrasena_en_texto_plano_no_inicia_sesion(self):
        self.db.sq.execute("UPDATE usuarios SET password_hash = '123456' WHERE id = ?", (self.art1_id,))
        self.db.sq.commit()
        self.assertEqual(self.login("uno@belaaktun.com", "123456").status_code, 401)

    def test_bloqueo_tras_muchos_intentos_fallidos(self):
        self.app.config["LOGIN_MAX_FALLOS"] = 3
        for _ in range(3):
            self.assertEqual(self.login("admin@belaaktun.com", "mala").status_code, 401)
        self.assertEqual(self.login("admin@belaaktun.com", "clave-admin-123").status_code, 429)

    def test_me_requiere_token_valido(self):
        self.assertEqual(self.cliente.get("/api/auth/me").status_code, 401)
        self.assertEqual(
            self.cliente.get("/api/auth/me", headers={"Authorization": "Bearer inventado"}).status_code, 401
        )
        r = self.cliente.get("/api/auth/me", headers=self.admin())
        self.assertEqual(r.get_json()["user"]["email"], "admin@belaaktun.com")

    def test_token_expirado_o_de_usuario_borrado_no_sirve(self):
        cab = self.admin()
        self.app.config["TOKEN_MAX_AGE"] = -1
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cab).status_code, 401)
        self.app.config["TOKEN_MAX_AGE"] = 3600
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cab).status_code, 200)
        self.db.sq.execute("DELETE FROM usuarios WHERE id = ?", (self.admin_id,))
        self.db.sq.commit()
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cab).status_code, 401)


class PruebasDeModeracion(PruebaBase):
    def test_solo_el_administrador_entra_al_panel(self):
        for ruta in ("/api/admin/comentarios", "/api/admin/mensajes", "/api/admin/resumen"):
            self.assertEqual(self.cliente.get(ruta).status_code, 401, ruta)
            cab = self.cabeceras("uno@belaaktun.com", "clave-uno-123")
            self.assertEqual(self.cliente.get(ruta, headers=cab).status_code, 403, ruta)
            self.assertEqual(self.cliente.get(ruta, headers=self.admin()).status_code, 200, ruta)
        self.assertEqual(self.cliente.patch("/api/admin/comentarios/1", json={"estado": "APROBADO"}).status_code, 401)

    def test_resena_nueva_queda_pendiente_y_no_se_ve_en_el_foro(self):
        rid = self.reserva_confirmada()
        r = self.publicar_resena(rid)
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(r.get_json()["estado"], "PENDIENTE")

        self.assertEqual(self.cliente.get("/api/foro/comentarios").get_json(), [])
        self.assertEqual(self.cliente.get("/api/foro/resumen").get_json(), {})

        pendientes = self.cliente.get("/api/admin/comentarios", headers=self.admin()).get_json()
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0]["titulo"], "Excelente")
        self.assertEqual(pendientes[0]["contacto"], "ana@correo.com")
        self.assertEqual(self.cliente.get("/api/admin/resumen", headers=self.admin()).get_json()["comentarios_pendientes"], 1)

    def test_aprobar_publica_y_rechazar_oculta(self):
        rid = self.reserva_confirmada()
        cid = self.publicar_resena(rid).get_json()["id"]
        cab = self.admin()

        r = self.cliente.patch(f"/api/admin/comentarios/{cid}", json={"estado": "APROBADO"}, headers=cab)
        self.assertEqual(r.status_code, 200)
        foro = self.cliente.get("/api/foro/comentarios").get_json()
        self.assertEqual([c["id"] for c in foro], [cid])
        self.assertEqual(foro[0]["nombre_taller"], "Taller Uno")
        self.assertNotIn("contacto", foro[0])
        self.assertNotIn("folio", foro[0])
        self.assertEqual(self.cliente.get("/api/foro/resumen").get_json()["1"]["total_resenas"], 1)
        fila = self.db.sql("SELECT moderado_por FROM comentarios_taller WHERE id = ?", (cid,))[0]
        self.assertEqual(fila["moderado_por"], self.admin_id)

        self.cliente.patch(
            f"/api/admin/comentarios/{cid}", json={"estado": "RECHAZADO", "motivo": "Lenguaje ofensivo"}, headers=cab
        )
        self.assertEqual(self.cliente.get("/api/foro/comentarios").get_json(), [])
        rechazados = self.cliente.get("/api/admin/comentarios?estado=RECHAZADO", headers=cab).get_json()
        self.assertEqual(rechazados[0]["motivo_rechazo"], "Lenguaje ofensivo")

    def test_estados_invalidos_y_resena_inexistente(self):
        cab = self.admin()
        self.assertEqual(self.cliente.patch("/api/admin/comentarios/99", json={"estado": "APROBADO"}, headers=cab).status_code, 404)
        self.assertEqual(self.cliente.patch("/api/admin/comentarios/99", json={"estado": "XX"}, headers=cab).status_code, 400)
        self.assertEqual(self.cliente.get("/api/admin/comentarios?estado=XX", headers=cab).status_code, 400)

    def test_editar_una_resena_aprobada_la_regresa_a_revision(self):
        rid = self.reserva_confirmada()
        cid = self.publicar_resena(rid).get_json()["id"]
        self.cliente.patch(f"/api/admin/comentarios/{cid}", json={"estado": "APROBADO"}, headers=self.admin())
        self.assertEqual(len(self.cliente.get("/api/foro/comentarios").get_json()), 1)

        r = self.cliente.put("/api/foro/comentarios", data={
            "folio": f"RES-{rid:03d}", "contacto": "ana@correo.com", "calificacion": "4",
            "titulo": "Editado", "descripcion": "Cambié el texto",
        }, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(r.get_json()["estado"], "PENDIENTE")
        self.assertEqual(self.cliente.get("/api/foro/comentarios").get_json(), [])

    def test_fotos_se_guardan_con_ruta_relativa_y_se_sirven_con_url_completa(self):
        rid = self.reserva_confirmada()
        r = self.publicar_resena(rid, fotos=[(io.BytesIO(PNG), "a.png"), (io.BytesIO(b"<html>no soy imagen"), "b.png")])
        cid = r.get_json()["id"]
        guardadas = self.db.sql("SELECT foto_url FROM comentario_fotos WHERE comentario_id = ?", (cid,))
        self.assertEqual(len(guardadas), 1, "el archivo que no es imagen se descarta")
        self.assertTrue(guardadas[0]["foto_url"].startswith("/static/uploads/comentarios/"))
        self.assertEqual(len(os.listdir(self.carpeta)), 1)

        pendiente = self.cliente.get("/api/admin/comentarios", headers=self.admin()).get_json()[0]
        self.assertTrue(pendiente["fotos"][0].startswith("http://localhost/static/uploads/comentarios/"))

    def test_eliminar_resena_borra_sus_fotos(self):
        rid = self.reserva_confirmada()
        cid = self.publicar_resena(rid, fotos=[(io.BytesIO(PNG), "a.png")]).get_json()["id"]
        self.assertEqual(len(os.listdir(self.carpeta)), 1)
        r = self.cliente.delete(f"/api/admin/comentarios/{cid}", headers=self.admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(os.listdir(self.carpeta), [])
        self.assertEqual(self.db.sql("SELECT COUNT(*) AS n FROM comentarios_taller")[0]["n"], 0)

    def test_fotos_antiguas_con_url_absoluta_se_respetan(self):
        rid = self.reserva_confirmada()
        cid = self.publicar_resena(rid).get_json()["id"]
        self.db.sq.execute("INSERT INTO comentario_fotos (comentario_id, foto_url, orden) VALUES (?,?,1)",
                           (cid, "http://127.0.0.1:5000/static/uploads/comentarios/x.png"))
        self.db.sq.commit()
        item = self.cliente.get("/api/admin/comentarios", headers=self.admin()).get_json()[0]
        self.assertEqual(item["fotos"], ["http://127.0.0.1:5000/static/uploads/comentarios/x.png"])


class PruebasDeContacto(PruebaBase):
    def enviar(self, **extra):
        cuerpo = {"nombre": "María López", "email": "maria@correo.com", "telefono": "", "mensaje": "¿Hay visitas el domingo?"}
        cuerpo.update(extra)
        return self.cliente.post("/api/contacto", json=cuerpo)

    def test_el_mensaje_llega_al_panel_del_administrador(self):
        r = self.enviar()
        self.assertEqual(r.status_code, 201, r.get_json())
        lista = self.cliente.get("/api/admin/mensajes", headers=self.admin()).get_json()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["nombre"], "María López")
        self.assertEqual(lista[0]["estado"], "NUEVO")
        self.assertEqual(self.cliente.get("/api/admin/resumen", headers=self.admin()).get_json()["mensajes_nuevos"], 1)

        mid = lista[0]["id"]
        self.cliente.patch(f"/api/admin/mensajes/{mid}", json={"estado": "LEIDO"}, headers=self.admin())
        self.assertEqual(self.cliente.get("/api/admin/mensajes", headers=self.admin()).get_json(), [])
        leidos = self.cliente.get("/api/admin/mensajes?estado=LEIDO", headers=self.admin()).get_json()
        self.assertEqual(leidos[0]["id"], mid)
        self.assertEqual(self.cliente.delete(f"/api/admin/mensajes/{mid}", headers=self.admin()).status_code, 200)
        self.assertEqual(self.cliente.get("/api/admin/mensajes?estado=TODOS", headers=self.admin()).get_json(), [])

    def test_validaciones(self):
        self.assertEqual(self.enviar(nombre="").status_code, 400)
        self.assertEqual(self.enviar(mensaje="hola").status_code, 400)
        self.assertEqual(self.enviar(email="", telefono="").status_code, 400)
        self.assertEqual(self.enviar(email="no-es-correo").status_code, 400)
        self.assertEqual(self.enviar(email="", telefono="123").status_code, 400)
        self.assertEqual(self.enviar(email="", telefono="996 107 2280").status_code, 201)
        self.assertEqual(self.enviar(mensaje="x" * 2001).status_code, 400)

    def test_campo_trampa_de_bots_no_guarda_nada(self):
        self.assertEqual(self.enviar(website="http://spam").status_code, 201)
        self.assertEqual(self.db.sql("SELECT COUNT(*) AS n FROM mensajes_contacto")[0]["n"], 0)

    def test_limite_de_mensajes_por_hora(self):
        for _ in range(5):
            self.assertEqual(self.enviar().status_code, 201)
        self.assertEqual(self.enviar().status_code, 429)


class PruebasDeSeguimiento(PruebaBase):
    def test_un_folio_solo_ya_no_revela_datos(self):
        rid = self.reserva_confirmada()
        for texto in (f"RES-{rid}", f"#RES-{rid:03d}", str(rid)):
            r = self.cliente.post("/api/seguimiento", json={"contacto": texto})
            self.assertEqual(r.status_code, 400, texto)

    def test_busca_por_correo_telefono_y_folio_con_contacto(self):
        rid = self.reserva_confirmada(email="Ana@Correo.com", tel="996 107-2280")
        for contacto in ("ana@correo.com", "9961072280", "996 107 2280"):
            r = self.cliente.post("/api/seguimiento", json={"contacto": contacto})
            self.assertEqual(r.status_code, 200, contacto)
            self.assertEqual(r.get_json()["reservas"][0]["id"], rid)
        self.assertEqual(self.cliente.post("/api/seguimiento", json={"contacto": "otra@correo.com"}).status_code, 404)

        ok = self.cliente.post("/api/seguimiento", json={"contacto": "ana@correo.com", "folio": f"RES-{rid}"})
        self.assertEqual(ok.status_code, 200)
        otro = self.cliente.post("/api/seguimiento", json={"contacto": "ana@correo.com", "folio": f"RES-{rid + 50}"})
        self.assertEqual(otro.status_code, 404)
        self.assertEqual(self.cliente.post("/api/seguimiento", json={"contacto": "ana@correo.com", "folio": "xx"}).status_code, 400)


class PruebasDeAccesoDeArtesanos(PruebaBase):
    def test_reservas_exigen_sesion_y_taller_propio(self):
        r1 = self.reserva_confirmada(taller_id=1)
        r2 = self.reserva_confirmada(taller_id=2, email="otro@correo.com")
        uno = self.cabeceras("uno@belaaktun.com", "clave-uno-123")

        self.assertEqual(self.cliente.get("/api/reservas").status_code, 401)
        self.assertEqual(self.cliente.get("/api/reservas/taller/1").status_code, 401)

        self.assertEqual(self.cliente.get("/api/reservas/taller/1", headers=uno).status_code, 200)
        self.assertEqual(self.cliente.get("/api/reservas/taller/2", headers=uno).status_code, 403)
        self.assertEqual(self.cliente.get("/api/reservas?taller_id=2", headers=uno).status_code, 403)
        propias = self.cliente.get("/api/reservas", headers=uno).get_json()
        self.assertEqual([r["id"] for r in propias], [r1])
        todas = self.cliente.get("/api/reservas", headers=self.admin()).get_json()
        self.assertEqual({r["id"] for r in todas}, {r1, r2})

        self.assertEqual(self.cliente.patch(f"/api/reservas/{r2}", json={"estado": "Confirmada"}, headers=uno).status_code, 403)
        self.assertEqual(self.cliente.delete(f"/api/reservas/{r2}", headers=uno).status_code, 403)
        self.assertEqual(self.cliente.patch(f"/api/reservas/{r1}", json={"estado": "Confirmada"}, headers=uno).status_code, 200)
        self.assertEqual(self.cliente.patch(f"/api/reservas/{r1}", json={"estado": "Confirmada"}).status_code, 401)
        self.assertEqual(self.cliente.patch("/api/reservas/999", json={}, headers=uno).status_code, 404)

    def test_apartados_y_productos_protegidos(self):
        cur = self.db.sq.execute("INSERT INTO productos (artesano_id, nombre_pieza, precio, calidad) VALUES (2,'Sombrero',100,'Fina')")
        pid = cur.lastrowid
        cur = self.db.sq.execute("INSERT INTO apartados (producto_id, taller_id, nombre_cliente) VALUES (?,2,'Luis')", (pid,))
        aid = cur.lastrowid
        self.db.sq.commit()
        uno = self.cabeceras("uno@belaaktun.com", "clave-uno-123")

        self.assertEqual(self.cliente.get("/api/apartados/taller/2").status_code, 401)
        self.assertEqual(self.cliente.get("/api/apartados/taller/2", headers=uno).status_code, 403)
        self.assertEqual(self.cliente.delete(f"/api/apartados/{aid}", headers=uno).status_code, 403)
        self.assertEqual(self.cliente.delete(f"/api/productos/{pid}", headers=uno).status_code, 403)
        self.assertEqual(self.cliente.put(f"/api/productos/{pid}", json={"nombre_pieza": "x"}, headers=uno).status_code, 403)

        nuevo = {"taller_id": 2, "nombre_pieza": "Robado", "precio": 1}
        self.assertEqual(self.cliente.post("/api/productos", json=nuevo).status_code, 401)
        self.assertEqual(self.cliente.post("/api/productos", json=nuevo, headers=uno).status_code, 403)
        propio = dict(nuevo, taller_id=1)
        self.assertEqual(self.cliente.post("/api/productos", json=propio, headers=uno).status_code, 201)

        dos = self.cabeceras("dos@belaaktun.com", "clave-dos-123")
        self.assertEqual(self.cliente.delete(f"/api/productos/{pid}", headers=dos).status_code, 200)

    def test_el_catalogo_y_las_solicitudes_siguen_siendo_publicos(self):
        self.assertEqual(self.cliente.get("/api/productos").status_code, 200)
        r = self.cliente.post("/api/reservas", json={
            "taller_id": 1, "nombre_visitante": "Eva", "email_visitante": "eva@correo.com",
            "numero_personas": 2, "fecha_reserva": "2026-12-05", "hora_reserva": "11:00"})
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertTrue(r.get_json()["folio"].startswith("RES-"))

    def test_errores_internos_no_exponen_detalles(self):
        with mock.patch.object(pymysql, "connect", side_effect=RuntimeError("secreto-interno-xyz")):
            r = self.cliente.get("/api/productos")
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("secreto-interno-xyz", r.get_data(as_text=True))


class PruebasDeDocumentacion(PruebaBase):
    def test_las_descripciones_swagger_son_yaml_valido(self):
        revisadas = 0
        for regla in self.app.url_map.iter_rules():
            vista = self.app.view_functions[regla.endpoint]
            doc = vista.__doc__ or ""
            if "---" not in doc:
                continue
            yaml.safe_load(doc.split("---", 1)[1])
            revisadas += 1
        self.assertGreater(revisadas, 20)

    def test_las_vistas_protegidas_conservan_su_documentacion(self):
        vista = self.app.view_functions["admin_bp.listar_comentarios_admin"]
        self.assertIn("Listar reseñas", vista.__doc__)


if __name__ == "__main__":
    unittest.main()
