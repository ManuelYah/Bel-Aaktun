from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection

auth_bp = Blueprint('auth_bp', __name__)

# ==========================================
# AUTH / LOGIN
# ==========================================
@auth_bp.route('/auth/login', methods=['POST', 'OPTIONS'])
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Correo y contraseña requeridos'}), 400

    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, email, taller_id, password_hash FROM usuarios WHERE email = %s", 
                (email,)
            )
            usuario = cursor.fetchone()
        conn.close()

        if usuario and usuario['password_hash'] == password:
            del usuario['password_hash']
            return jsonify({'message': 'Inicio de sesión exitoso', 'user': usuario}), 200
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        print("Error en login:", str(e))
        return jsonify({'error': str(e)}), 500


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================
@auth_bp.route('/auth/register', methods=['POST', 'OPTIONS'])
def registrar_usuario():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.get_json() or {}
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')
    taller_id = data.get('taller_id') # Opcional si es un artesano con taller asociado

    if not nombre or not email or not password:
        return jsonify({'error': 'Faltan campos obligatorios (nombre, email, password)'}), 400

    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            # Verificamos si el correo ya existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'El correo electrónico ya está registrado'}), 400

            password_hash = password # Puedes mantenerlo directo o aplicar hash si prefieres

            sql = """
                INSERT INTO usuarios (nombre, email, password_hash, taller_id)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, email, password_hash, taller_id))
            conn.commit()
            nuevo_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Usuario registrado con éxito', 'id': nuevo_id}), 201

    except Exception as e:
        print("Error al registrar usuario:", str(e))
        return jsonify({'error': str(e)}), 500