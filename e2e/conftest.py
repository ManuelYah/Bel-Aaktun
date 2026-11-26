"""Configuración común de las pruebas Selenium.

Variables de entorno:
  BASE_URL             sitio a probar (por defecto http://localhost)
  SELENIUM_REMOTE_URL  si existe, usa ese Selenium remoto (docker compose); si no, Chrome local
  E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD
  E2E_ARTESANO_EMAIL / E2E_ARTESANO_PASSWORD
"""
import json
import os
import time
import urllib.request
import uuid
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")
REMOTE = os.getenv("SELENIUM_REMOTE_URL", "")
REPORTS = Path(__file__).parent / "reports"
TIMEOUT = 15

ADMIN = (os.getenv("E2E_ADMIN_EMAIL", "e2e-admin@belaaktun.test"), os.getenv("E2E_ADMIN_PASSWORD", ""))
ARTESANO = (os.getenv("E2E_ARTESANO_EMAIL", "acosta@belaaktun.com"), os.getenv("E2E_ARTESANO_PASSWORD", ""))


def _opciones():
    o = webdriver.ChromeOptions()
    if not os.getenv("E2E_VISIBLE"):
        o.add_argument("--headless=new")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--window-size=1366,900")
    o.add_argument("--lang=es-MX")
    return o


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture()
def driver(request):
    if REMOTE:
        d = webdriver.Remote(command_executor=REMOTE, options=_opciones())
    else:
        d = webdriver.Chrome(options=_opciones())
    d.implicitly_wait(0)
    yield d
    # Captura de pantalla si la prueba falló
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        REPORTS.mkdir(exist_ok=True)
        d.save_screenshot(str(REPORTS / f"{request.node.name}.png"))
    d.quit()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


# ---------------------------------------------------------------- ayudas
class Pagina:
    """Atajos sobre el driver para no repetir esperas."""

    def __init__(self, driver, base):
        self.d = driver
        self.base = base
        self.wait = WebDriverWait(driver, TIMEOUT)

    def ir(self, ruta="/"):
        self.d.get(f"{self.base}{ruta}")

    def tid(self, nombre):
        return f'[data-testid="{nombre}"]'

    def visible(self, nombre):
        return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.tid(nombre))))

    def todos(self, nombre):
        return self.d.find_elements(By.CSS_SELECTOR, self.tid(nombre))

    def escribir(self, nombre, texto):
        el = self.visible(nombre)
        el.clear()
        el.send_keys(texto)

    def clic(self, nombre):
        el = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.tid(nombre))))
        el.click()

    def esperar_url(self, fragmento):
        self.wait.until(EC.url_contains(fragmento))

    def texto_en_pagina(self, texto):
        self.wait.until(lambda d: texto in d.find_element(By.TAG_NAME, "body").text)

    def login(self, email, password):
        self.ir("/login")
        self.escribir("login-email", email)
        self.escribir("login-password", password)
        self.clic("login-submit")


@pytest.fixture()
def pagina(driver, base_url):
    return Pagina(driver, base_url)


def api(metodo, ruta, cuerpo=None):
    """Llamada directa a la API (para preparar datos sin pasar por la interfaz)."""
    req = urllib.request.Request(
        f"{BASE_URL}/api{ruta}",
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
        method=metodo,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"{}")


@pytest.fixture()
def requiere_admin():
    if not ADMIN[1]:
        pytest.skip("Falta E2E_ADMIN_PASSWORD")


@pytest.fixture()
def requiere_artesano():
    if not ARTESANO[1]:
        pytest.skip("Falta E2E_ARTESANO_PASSWORD")


def sufijo():
    return uuid.uuid4().hex[:8]
