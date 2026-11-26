from flask import Blueprint, request, jsonify, current_app, g
from app.extensions import get_db_connection
from app.security import (
    gastar_tiempo_de_verificacion,
    crear_token,
    limite_login,
    login_required,
    usuario_publico,
    verificar_password,
)

auth_bp = Blueprint('auth_bp', __name__)


# ==========================================
# AUTH / LOGIN (ARTESANO Y ADMINISTRADOR)
# ==========================================
@auth_bp.route('/auth/login', methods=['POST', 'OPTIONS'])
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Iniciar sesión (artesano o administrador)
    ---
    tags:
      - Autenticación
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "artesano@belaaktun.com"
            password:
              type: string
              example: "123456"
    responses:
      200:
        description: Inicio de sesión exitoso. Devuelve token, fecha de expiración y usuario (con su rol).
      400:
        description: Correo y contraseña requeridos
      401:
        description: Credenciales inválidas
      429:
        description: Demasiados intentos fallidos
      500:
        description: Error interno del servidor
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password or not isinstance(password, str):
        return jsonify({'error': 'Correo y contraseña requeridos'}), 400

    cfg = current_app.config
    clave_ip = request.remote_addr or 'desconocida'
    if limite_login.bloqueado(clave_ip, cfg['LOGIN_MAX_FALLOS'], cfg['LOGIN_VENTANA_SEGUNDOS']):
        return jsonify({'error': 'Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.'}), 429

    conn = None
    try:
        conn = get_db_connection(cfg)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, email, taller_id, rol, password_hash "
                "FROM usuarios WHERE LOWER(email) = %s",
                (email,)
            )
            usuario = cursor.fetchone()

        if usuario and verificar_password(usuario['password_hash'], password):
            limite_login.reiniciar(clave_ip)
            token, expira = crear_token(usuario)
            return jsonify({
                'message': 'Inicio de sesión exitoso',
                'token': token,
                'expires_at': expira,
                'user': usuario_publico(usuario),
            }), 200

        if not usuario:
            gastar_tiempo_de_verificacion(password)
        limite_login.registrar(clave_ip)
        return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception:
        current_app.logger.exception("Error en login")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if conn:
            conn.close()


@auth_bp.route('/auth/me', methods=['GET'])
@login_required
def perfil():
    """
    Datos del usuario con sesión activa
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    responses:
      200:
        description: Usuario autenticado
      401:
        description: Sesión no válida o expirada
    """
    return jsonify({'user': usuario_publico(g.usuario)}), 200
