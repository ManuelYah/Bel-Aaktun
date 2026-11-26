import os
import secrets

import pymysql


def _env_bool(nombre, defecto=False):
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def _env_lista(nombre, defecto):
    valor = os.getenv(nombre)
    if not valor:
        return defecto
    return [item.strip() for item in valor.split(",") if item.strip()]


_CORS_ORIGINS = _env_lista(
    "CORS_ORIGINS",
    ["http://localhost:4200", "http://127.0.0.1:4200"],
)


class Config:
    # --- Seguridad -----------------------------------------------------
    # Firma los tokens de sesión. En producción define SECRET_KEY; si falta
    # se genera una al arrancar y las sesiones se cierran en cada reinicio.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SECRET_KEY_DEFINIDA = bool(os.getenv("SECRET_KEY"))
    TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE_SECONDS", 8 * 3600))
    LOGIN_MAX_FALLOS = int(os.getenv("LOGIN_MAX_FALLOS", 10))
    LOGIN_VENTANA_SEGUNDOS = int(os.getenv("LOGIN_VENTANA_SEGUNDOS", 15 * 60))
    TRUST_PROXY = _env_bool("TRUST_PROXY", False)

    CORS_ORIGINS = _CORS_ORIGINS
    CORS_RESOURCES = {
        r"/api/*": {"origins": _CORS_ORIGINS},
        r"/static/*": {"origins": _CORS_ORIGINS},
    }

    # Las reseñas llevan hasta 3 fotos y los productos imágenes en base64.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_MB", 32)) * 1024 * 1024

    # --- Correo --------------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    # Sin credenciales SMTP no se intenta enviar correo (evita que la petición se cuelgue).
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND", not os.getenv("MAIL_USERNAME"))
    CONTACTO_MAX_POR_HORA = int(os.getenv("CONTACTO_MAX_POR_HORA", 5))
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = (
        "Bel-Aaktun Ruta de las Cuevas",
        os.getenv("MAIL_SENDER_EMAIL") or os.getenv("MAIL_USERNAME", ""),
    )

    # --- Base de datos ---------------------------------------------------
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", 3307)),
        "user": os.getenv("DB_USER", "becal_user"),
        "password": os.getenv("DB_PASSWORD", "becal_pass"),
        "database": os.getenv("DB_NAME", "becal_db"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

    # --- Arranque ----------------------------------------------------------
    # Aplica migraciones y crea el administrador al iniciar la aplicación.
    RUN_BOOTSTRAP = _env_bool("RUN_BOOTSTRAP", True)
    ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or ""
    ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE") or "Administrador"

    # Opcional: https://api.midominio.com (para armar las URLs de las fotos).
    PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
