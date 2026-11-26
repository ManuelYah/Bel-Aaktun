import os
import re

from flask import current_app, request

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Firmas (magic bytes) para comprobar que el archivo realmente es una imagen.
_FIRMAS_IMAGEN = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")


def email_valido(valor):
    return bool(valor) and len(valor) <= 150 and bool(_EMAIL_RE.match(valor))


def es_imagen_real(archivo):
    """Verifica la firma del archivo (PNG, JPEG o WEBP) y deja el cursor al inicio."""
    cabecera = archivo.stream.read(12)
    archivo.stream.seek(0)
    if any(cabecera.startswith(firma) for firma in _FIRMAS_IMAGEN):
        return True
    return cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP"


def url_publica(ruta):
    """Convierte la ruta guardada de una foto en una URL absoluta.

    Las filas antiguas guardan 'http://127.0.0.1:5000/...'; se respetan tal cual.
    """
    if not ruta:
        return ruta
    if ruta.startswith(("http://", "https://")):
        return ruta
    base = current_app.config.get("PUBLIC_BASE_URL") or request.host_url.rstrip("/")
    return base + (ruta if ruta.startswith("/") else "/" + ruta)


def carpeta_fotos():
    return os.path.join(current_app.root_path, "static", "uploads", "comentarios")


def borrar_archivos_de_fotos(rutas):
    """Elimina del disco las fotos indicadas (solo dentro de la carpeta de fotos)."""
    carpeta = os.path.realpath(carpeta_fotos())
    for ruta in rutas:
        nombre = os.path.basename((ruta or "").split("?")[0])
        if not nombre:
            continue
        destino = os.path.realpath(os.path.join(carpeta, nombre))
        if os.path.dirname(destino) == carpeta and os.path.isfile(destino):
            try:
                os.remove(destino)
            except OSError:
                current_app.logger.warning("No se pudo borrar la foto %s", destino)
