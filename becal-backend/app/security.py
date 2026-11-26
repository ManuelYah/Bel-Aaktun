"""Autenticación: contraseñas con hash, tokens firmados y control de acceso."""
import time
from collections import defaultdict, deque
from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import get_db_connection

ROL_ADMIN = "ADMIN"
ROL_ARTESANO = "ARTESANO"

_SALT = "bel-aaktun-sesion-v1"
_PREFIJOS_HASH = ("scrypt:", "pbkdf2:")
# Hash de relleno: permite gastar el mismo tiempo cuando el correo no existe.
_HASH_RELLENO = generate_password_hash("relleno-para-igualar-tiempos")


# ---------------------------------------------------------------- contraseñas
def hash_password(password):
    return generate_password_hash(password)


def es_hash(valor):
    return isinstance(valor, str) and valor.startswith(_PREFIJOS_HASH)


def verificar_password(guardado, ingresado):
    if not es_hash(guardado):
        return False
    return check_password_hash(guardado, ingresado)


def gastar_tiempo_de_verificacion(ingresado):
    check_password_hash(_HASH_RELLENO, ingresado or "")


# ---------------------------------------------------------------- tokens
def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def crear_token(usuario):
    """Devuelve (token, expira_en_epoch_segundos)."""
    token = _serializador().dumps({"uid": int(usuario["id"])})
    expira = int(time.time()) + current_app.config["TOKEN_MAX_AGE"]
    return token, expira


def leer_token(token):
    """Devuelve el id de usuario del token o None si es inválido o expiró."""
    try:
        datos = _serializador().loads(token, max_age=current_app.config["TOKEN_MAX_AGE"])
    except (BadSignature, SignatureExpired):
        return None
    uid = datos.get("uid") if isinstance(datos, dict) else None
    return uid if isinstance(uid, int) else None


def _token_de_la_peticion():
    cabecera = request.headers.get("Authorization", "")
    partes = cabecera.split(None, 1)
    if len(partes) == 2 and partes[0].lower() == "bearer":
        return partes[1].strip()
    return None


def cargar_usuario(uid):
    """Lee el usuario vigente en la base de datos (así borrar o degradar una
    cuenta invalida sus tokens de inmediato)."""
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, email, taller_id, rol FROM usuarios WHERE id = %s",
                (uid,),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def usuario_de_la_peticion():
    token = _token_de_la_peticion()
    if not token:
        return None
    uid = leer_token(token)
    if uid is None:
        return None
    return cargar_usuario(uid)


def usuario_publico(usuario):
    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "taller_id": usuario.get("taller_id"),
        "rol": usuario.get("rol") or ROL_ARTESANO,
    }


# ---------------------------------------------------------------- decoradores
def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if request.method == "OPTIONS":  # preflight de CORS
            return vista(*args, **kwargs)
        usuario = usuario_de_la_peticion()
        if not usuario:
            return jsonify({"error": "Sesión no válida o expirada. Inicia sesión de nuevo."}), 401
        g.usuario = usuario
        return vista(*args, **kwargs)

    return envoltura


def roles_required(*roles):
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(*args, **kwargs):
            if request.method != "OPTIONS" and (g.usuario.get("rol") or ROL_ARTESANO) not in roles:
                return jsonify({"error": "No tienes permiso para realizar esta acción."}), 403
            return vista(*args, **kwargs)

        return envoltura

    return decorador


def puede_gestionar_taller(usuario, taller_id):
    if (usuario.get("rol") or ROL_ARTESANO) == ROL_ADMIN:
        return True
    try:
        return usuario.get("taller_id") is not None and int(usuario["taller_id"]) == int(taller_id)
    except (TypeError, ValueError):
        return False


def sin_permiso_sobre_taller():
    return jsonify({"error": "No tienes permiso sobre este taller."}), 403


# ---------------------------------------------------------------- límite de intentos de login
class LimiteDeFallos:
    """Cuenta intentos fallidos por IP en memoria (por proceso)."""

    def __init__(self):
        self._fallos = defaultdict(deque)

    def _limpiar(self, clave, ventana):
        cola = self._fallos[clave]
        limite = time.time() - ventana
        while cola and cola[0] < limite:
            cola.popleft()
        if not cola:
            self._fallos.pop(clave, None)
        return cola

    def bloqueado(self, clave, maximo, ventana):
        return len(self._limpiar(clave, ventana)) >= maximo

    def registrar(self, clave):
        self._fallos[clave].append(time.time())

    def reiniciar(self, clave):
        self._fallos.pop(clave, None)

    def vaciar(self):
        self._fallos.clear()


limite_login = LimiteDeFallos()
