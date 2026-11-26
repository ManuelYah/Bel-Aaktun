from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection

auth_bp = Blueprint('auth_bp', __name__)


# ==========================================
# AUTH / LOGIN (ARTESANO)
# ==========================================
@auth_bp.route('/auth/login', methods=['POST', 'OPTIONS'])
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Iniciar sesión como artesano
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
        description: Inicio de sesión exitoso
      400:
        description: Correo y contraseña requeridos
      401:
        description: Credenciales inválidas
      500:
        description: Error interno del servidor
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Correo y contraseña requeridos'}), 400

    conn = None
    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, email, taller_id, password_hash FROM usuarios WHERE LOWER(email) = %s",
                (email,)
            )
            usuario = cursor.fetchone()

        if usuario and usuario['password_hash'] == password:
            del usuario['password_hash']
            return jsonify({'message': 'Inicio de sesión exitoso', 'user': usuario}), 200
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        print("Error en login:", str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()