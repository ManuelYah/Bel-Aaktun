from conftest import ADMIN, sufijo


def test_mensaje_de_contacto_llega_al_admin(pagina, requiere_admin):
    marca = f"E2E-{sufijo()}"
    pagina.ir("/contacto")
    pagina.escribir("contacto-nombre", f"Visitante {marca}")
    pagina.escribir("contacto-email", "visitante@ejemplo.com")
    pagina.escribir("contacto-mensaje", f"Mensaje de prueba {marca}")
    pagina.clic("contacto-enviar")
    pagina.visible("contacto-ok")

    pagina.login(*ADMIN)
    pagina.esperar_url("/admin")
    pagina.clic("tab-mensajes")
    pagina.texto_en_pagina(marca)
