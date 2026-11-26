import pytest

pytestmark = pytest.mark.humo

RUTAS = ["/", "/catalogo", "/contacto", "/foro-talleres", "/seguimiento", "/crear-reserva", "/login", "/cuevas-mapa"]


@pytest.mark.parametrize("ruta", RUTAS)
def test_las_paginas_cargan(pagina, ruta):
    pagina.ir(ruta)
    pagina.wait.until(lambda d: d.find_element("tag name", "app-root").text.strip() != "")


def test_el_catalogo_muestra_productos(pagina):
    pagina.ir("/catalogo")
    pagina.wait.until(lambda d: len(pagina.todos("producto-card")) > 0)


def test_swagger_responde_detras_de_nginx(pagina):
    pagina.ir("/apidocs/")
    pagina.wait.until(lambda d: "swagger" in d.page_source.lower())


def test_ruta_desconocida_vuelve_al_inicio(pagina):
    pagina.ir("/ruta-que-no-existe")
    pagina.wait.until(lambda d: "ruta-que-no-existe" not in d.current_url)
