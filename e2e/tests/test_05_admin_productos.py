from conftest import ADMIN


def test_admin_elimina_un_producto_del_catalogo(pagina, requiere_admin):
    nombre = "E2E Producto borrable"
    pagina.login(*ADMIN)
    pagina.esperar_url("/admin")
    pagina.clic("tab-productos")
    pagina.texto_en_pagina(nombre)

    tarjeta = next(t for t in pagina.todos("producto-item") if nombre in t.text)
    tarjeta.find_element("css selector", '[data-testid="producto-eliminar"]').click()
    tarjeta = next(t for t in pagina.todos("producto-item") if nombre in t.text)
    tarjeta.find_element("css selector", '[data-testid="confirmar-eliminar"]').click()

    pagina.wait.until(lambda d: nombre not in d.find_element("tag name", "body").text)

    # Tampoco aparece en el catálogo público
    pagina.ir("/catalogo")
    pagina.wait.until(lambda d: len(pagina.todos("producto-card")) > 0)
    assert nombre not in pagina.d.find_element("tag name", "body").text
