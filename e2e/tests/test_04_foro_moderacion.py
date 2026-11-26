"""Flujo completo: reserva -> reseña (queda pendiente) -> el admin la aprueba -> aparece en el foro."""
from conftest import ADMIN, api, sufijo


def _crear_reserva(correo):
    r = api("POST", "/reservas", {
        "taller_id": 1,
        "nombre_visitante": "Visitante E2E",
        "email_visitante": correo,
        "telefono_visitante": "9961234567",
        "numero_personas": 2,
        "fecha_reserva": "2030-01-15",
        "hora_reserva": "10:00",
    })
    return r["folio"]


def test_resena_pasa_por_moderacion_y_aparece_en_el_foro(pagina, requiere_admin):
    marca = sufijo()
    correo = f"e2e-{marca}@ejemplo.com"
    titulo = f"Reseña E2E {marca}"
    folio = _crear_reserva(correo)

    # 1) El visitante publica la reseña
    pagina.ir("/foro-talleres")
    pagina.clic("foro-nuevo")
    pagina.escribir("foro-folio", str(folio))
    pagina.escribir("foro-nombre", "Visitante E2E")
    pagina.escribir("foro-contacto", correo)
    pagina.escribir("foro-titulo", titulo)
    pagina.escribir("foro-descripcion", "Excelente atención, prueba automática.")
    pagina.clic("foro-publicar")
    pagina.visible("foro-exito")

    # 2) Todavía NO es pública
    pagina.ir("/foro-talleres")
    pagina.wait.until(lambda d: "Cargando comentarios" not in d.find_element("tag name", "body").text)
    assert titulo not in pagina.d.find_element("tag name", "body").text

    # 3) El administrador la aprueba
    pagina.login(*ADMIN)
    pagina.esperar_url("/admin")
    pagina.texto_en_pagina(titulo)
    tarjeta = next(t for t in pagina.todos("resena-item") if titulo in t.text)
    tarjeta.find_element("css selector", '[data-testid="resena-aprobar"]').click()
    pagina.wait.until(lambda d: titulo not in d.find_element("tag name", "body").text)

    # 4) Ahora sí aparece en el foro
    pagina.ir("/foro-talleres")
    pagina.texto_en_pagina(titulo)
