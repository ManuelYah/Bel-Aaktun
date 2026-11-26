from conftest import ADMIN, ARTESANO


def test_login_con_datos_incorrectos_muestra_error(pagina):
    pagina.login("nadie@belaaktun.test", "incorrecta123")
    assert pagina.visible("login-error").text.strip() != ""
    assert "/login" in pagina.d.current_url


def test_dashboard_exige_sesion(pagina):
    pagina.ir("/dashboard")
    pagina.esperar_url("/login")


def test_admin_exige_sesion(pagina):
    pagina.ir("/admin")
    pagina.esperar_url("/login")


def test_artesano_entra_y_cierra_sesion(pagina, requiere_artesano):
    pagina.login(*ARTESANO)
    pagina.esperar_url("/dashboard")
    pagina.clic("dashboard-logout")
    pagina.esperar_url("/login")
    # Sin sesión ya no se puede volver al panel
    pagina.ir("/dashboard")
    pagina.esperar_url("/login")


def test_admin_entra_y_cierra_sesion(pagina, requiere_admin):
    pagina.login(*ADMIN)
    pagina.esperar_url("/admin")
    pagina.clic("admin-logout")
    pagina.esperar_url("/login")


def test_artesano_no_puede_abrir_el_panel_admin(pagina, requiere_artesano):
    pagina.login(*ARTESANO)
    pagina.esperar_url("/dashboard")
    pagina.ir("/admin")
    pagina.wait.until(lambda d: "/admin" not in d.current_url)
