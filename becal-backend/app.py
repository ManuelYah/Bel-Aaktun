from flask_mail import Mail, Message
import json
import pymysql
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Configurar CORS para permitir peticiones desde Angular
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuración de Flask-Mail para Gmail (belaaktun@gmail.com)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'belaaktun@gmail.com'
app.config['MAIL_PASSWORD'] = 'tvwc bwha ehta gtlf'
app.config['MAIL_DEFAULT_SENDER'] = ('Bel-Aaktun Ruta de las Cuevas', 'belaaktun@gmail.com')

mail = Mail(app)

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'becal_user',
    'password': 'becal_pass',
    'database': 'becal_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def generar_folio(prefijo, id_num):
    return f"{prefijo}-{str(id_num).zfill(4)}"

# ==========================================
# AUTH / LOGIN
# ==========================================
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Correo y contraseña requeridos'}), 400

    try:
        conn = get_db_connection()
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
# RESERVAS
# ==========================================
@app.route('/api/reservas', methods=['GET', 'POST', 'OPTIONS'])
def handle_reservas():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'GET':
        taller_id = request.args.get('taller_id')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                if taller_id:
                    cursor.execute("SELECT * FROM reservas WHERE taller_id = %s ORDER BY id DESC", (taller_id,))
                else:
                    cursor.execute("SELECT * FROM reservas ORDER BY id DESC")
                data = cursor.fetchall()
            conn.close()
            return jsonify(data), 200
        except Exception as e:
            print("Error obteniendo reservas:", str(e))
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json() or {}
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO reservas (taller_id, nombre_visitante, email_visitante, telefono_visitante, numero_personas, fecha_reserva, hora_reserva, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pendiente')
                """
                cursor.execute(sql, (
                    data.get('taller_id', 4),
                    data.get('nombre_visitante'),
                    data.get('email_visitante'),
                    data.get('telefono_visitante', ''),
                    data.get('numero_personas', 1),
                    data.get('fecha_reserva'),
                    data.get('hora_reserva', '10:00')
                ))
                conn.commit()
                reserva_id = cursor.lastrowid

                # Obtener nombre del taller para el correo
                cursor.execute("SELECT nombre_taller FROM artesanias WHERE id = %s", (data.get('taller_id', 4),))
                taller_info = cursor.fetchone() or {}

            conn.close()

            folio = generar_folio("RES", reserva_id)
            email_visitante = data.get('email_visitante')
            nombre_visitante = data.get('nombre_visitante', 'Visitante')
            nombre_taller = taller_info.get('nombre_taller', 'Taller Artesanal')

            # Enviar correo de confirmación de reserva
            if email_visitante:
                try:
                    msg = Message(
                        subject=f"Confirmación de Solicitud de Reserva - Folio: {folio}",
                        recipients=[email_visitante]
                    )
                    msg.html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                        <h2 style="color: #c85a32; text-align: center;">Bel-Aaktun: Ruta de las Cuevas</h2>
                        <hr style="border: 0; border-top: 1px solid #eee;">
                        <p>Hola <strong>{nombre_visitante}</strong>,</p>
                        <p>¡Tu solicitud de visita a la cueva/taller ha sido registrada con éxito!</p>
                        
                        <div style="background-color: #f9f8f5; padding: 15px; border-radius: 6px; margin: 15px 0;">
                            <p style="margin: 5px 0;"><strong>Número de Folio:</strong> <span style="color: #c85a32; font-size: 1.1em; font-weight: bold;">{folio}</span></p>
                            <p style="margin: 5px 0;"><strong>Taller a Visitar:</strong> {nombre_taller}</p>
                            <p style="margin: 5px 0;"><strong>Fecha y Hora:</strong> {data.get('fecha_reserva')} a las {data.get('hora_reserva')} hrs</p>
                            <p style="margin: 5px 0;"><strong>Número de Personas:</strong> {data.get('numero_personas', 1)}</p>
                        </div>

                        <p><strong>Estado:</strong> <span style="background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold;">Pendiente de Confirmación</span></p>
                        
                        <p>El artesano revisará su agenda para confirmar la fecha y hora seleccionada. Por favor espera a que el taller confirme o rechace tu petición.</p>
                        
                        <hr style="border: 0; border-top: 1px solid #eee;">
                        <p style="font-size: 0.85em; color: #777; text-align: center;">Este es un mensaje automático de Bel-Aaktun (belaaktun@gmail.com).</p>
                    </div>
                    """
                    mail.send(msg)
                except Exception as mail_err:
                    print("Error enviando correo de reserva:", str(mail_err))

            return jsonify({'message': 'Reserva creada', 'folio': folio}), 201
        except Exception as e:
            print("Error creando reserva:", str(e))
            return jsonify({'error': str(e)}), 500

@app.route('/api/reservas/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def reservas_por_taller(taller_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM reservas WHERE taller_id = %s ORDER BY id DESC", (taller_id,))
            data = cursor.fetchall()
        conn.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en reservas por taller:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservas/<int:reserva_id>', methods=['PATCH', 'DELETE', 'OPTIONS'])
def gestionar_reserva(reserva_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if request.method == 'PATCH':
                estado = request.get_json().get('estado')
                cursor.execute("UPDATE reservas SET estado = %s WHERE id = %s", (estado, reserva_id))
            elif request.method == 'DELETE':
                cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
            conn.commit()
        conn.close()
        return jsonify({'message': 'Operación exitosa'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# PRODUCTOS CON DATOS DEL TALLER (artesanias)
# ==========================================
@app.route('/api/productos', methods=['GET', 'POST', 'OPTIONS'])
def handle_productos():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'GET':
        taller_id = request.args.get('taller_id')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """
                    SELECT p.id, p.artesano_id AS taller_id, p.nombre_pieza, 
                           p.descripcion, p.precio, p.calidad, p.imagenes,
                           a.nombre_taller, a.artesano_encargado, a.telefono_whatsapp, a.google_maps_url
                    FROM productos p
                    LEFT JOIN artesanias a ON p.artesano_id = a.id
                """
                if taller_id:
                    sql += " WHERE p.artesano_id = %s ORDER BY p.id DESC"
                    cursor.execute(sql, (taller_id,))
                else:
                    sql += " ORDER BY p.id DESC"
                    cursor.execute(sql)

                data = cursor.fetchall()
                for row in data:
                    imgs = row.get('imagenes')
                    if isinstance(imgs, str):
                        try:
                            imgs = json.loads(imgs)
                        except:
                            imgs = []
                    elif not imgs:
                        imgs = []
                    row['imagenes'] = imgs
                    row['imagen_url'] = imgs[0] if len(imgs) > 0 else ''

            conn.close()
            return jsonify(data), 200
        except Exception as e:
            print("Error obteniendo productos:", str(e))
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json() or {}
        try:
            imagenes_list = data.get('imagenes', [])
            imagenes_json = json.dumps(imagenes_list)

            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO productos (artesano_id, nombre_pieza, descripcion, precio, calidad, imagenes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data.get('taller_id') or data.get('artesano_id', 4),
                    data.get('nombre_pieza'),
                    data.get('descripcion', ''),
                    data.get('precio') or data.get('precio_promedio', 0),
                    data.get('calidad') or data.get('calidad_partidas', 'Fina'),
                    imagenes_json
                ))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Producto creado'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# ==========================================
# PRODUCTOS POR TALLER (Resuelve el error 404 del Dashboard)
# ==========================================
@app.route('/api/productos/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def obtener_productos_por_taller(taller_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT p.id, p.artesano_id AS taller_id, p.nombre_pieza, 
                       p.descripcion, p.precio, p.calidad, p.imagenes
                FROM productos p
                WHERE p.artesano_id = %s
                ORDER BY p.id DESC
            """
            cursor.execute(sql, (taller_id,))
            data = cursor.fetchall()
            
            for row in data:
                imgs = row.get('imagenes')
                if isinstance(imgs, str):
                    try:
                        imgs = json.loads(imgs)
                    except:
                        imgs = []
                elif not imgs:
                    imgs = []
                row['imagenes'] = imgs
                row['imagen_url'] = imgs[0] if len(imgs) > 0 else ''

        conn.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en productos por taller:", str(e))
        return jsonify({'error': str(e)}), 500


# ==========================================
# EDITAR Y ELIMINAR PRODUCTOS
# ==========================================
@app.route('/api/productos/<int:producto_id>', methods=['DELETE', 'PUT', 'OPTIONS'])
def gestionar_producto_individual(producto_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'DELETE':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Producto eliminado'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        data = request.get_json() or {}
        try:
            imagenes_list = data.get('imagenes', [])
            imagenes_json = json.dumps(imagenes_list)

            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """
                    UPDATE productos 
                    SET nombre_pieza = %s, descripcion = %s, precio = %s, calidad = %s, imagenes = %s
                    WHERE id = %s
                """
                cursor.execute(sql, (
                    data.get('nombre_pieza'),
                    data.get('descripcion', ''),
                    data.get('precio') or data.get('precio_promedio', 0),
                    data.get('calidad') or data.get('calidad_partidas', 'Fina'),
                    imagenes_json,
                    producto_id
                ))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Producto actualizado con éxito'}), 200
        except Exception as e:
            print("Error actualizando producto:", str(e))
            return jsonify({'error': str(e)}), 500


# ==========================================
# APARTAR PRODUCTO
# ==========================================
@app.route('/api/apartados', methods=['POST', 'OPTIONS'])
def crear_apartado():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json() or {}
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO apartados (producto_id, taller_id, nombre_cliente, email_cliente, telefono_cliente, cantidad, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data.get('producto_id'),
                data.get('taller_id'),
                data.get('nombre_cliente'),
                data.get('email_cliente'),
                data.get('telefono_cliente'),
                data.get('cantidad', 1),
                'Pendiente'
            ))
            conn.commit()
            apartado_id = cursor.lastrowid

            # Obtener información del producto y taller para el correo
            cursor.execute("""
                SELECT p.nombre_pieza, COALESCE(a.nombre_taller, 'Taller Artesanal') as nombre_taller 
                FROM productos p 
                LEFT JOIN artesanias a ON p.artesano_id = a.id 
                WHERE p.id = %s
            """, (data.get('producto_id'),))
            info_prod = cursor.fetchone() or {}

        conn.close()

        folio = generar_folio("APT", apartado_id)
        email_cliente = data.get('email_cliente')
        nombre_cliente = data.get('nombre_cliente', 'Cliente')
        nombre_pieza = info_prod.get('nombre_pieza', 'Pieza Artesanal')
        nombre_taller = info_prod.get('nombre_taller', 'Taller Artesanal')

        # Enviar correo de confirmación de apartado
        if email_cliente:
            try:
                msg = Message(
                    subject=f"Confirmación de Solicitud de Apartado - Folio: {folio}",
                    recipients=[email_cliente]
                )
                msg.html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h2 style="color: #c85a32; text-align: center;">Bel-Aaktun: Ruta de las Cuevas</h2>
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p>Hola <strong>{nombre_cliente}</strong>,</p>
                    <p>¡Tu solicitud de apartado se ha registrado con éxito en nuestro sistema!</p>
                    
                    <div style="background-color: #f9f8f5; padding: 15px; border-radius: 6px; margin: 15px 0;">
                        <p style="margin: 5px 0;"><strong>Número de Folio:</strong> <span style="color: #c85a32; font-size: 1.1em; font-weight: bold;">{folio}</span></p>
                        <p style="margin: 5px 0;"><strong>Producto:</strong> {nombre_pieza}</p>
                        <p style="margin: 5px 0;"><strong>Cantidad:</strong> {data.get('cantidad', 1)} pieza(s)</p>
                        <p style="margin: 5px 0;"><strong>Taller:</strong> {nombre_taller}</p>
                    </div>

                    <p><strong>Estado:</strong> <span style="background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold;">Pendiente de Revisión</span></p>
                    
                    <p>Tu solicitud ha sido enviada al taller artesanal. Por favor espera a que el artesano revise la disponibilidad de stock o tiempo de confección para confirmar o rechazar tu petición.</p>
                    
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p style="font-size: 0.85em; color: #777; text-align: center;">Este es un mensaje automático de Bel-Aaktun (belaaktun@gmail.com). Gracias por apoyar la artesanía local.</p>
                </div>
                """
                mail.send(msg)
            except Exception as mail_err:
                print("Error enviando correo de apartado:", str(mail_err))

        return jsonify({'message': 'Producto apartado con éxito', 'folio': folio}), 201
    except Exception as e:
        print("Error creando apartado:", str(e))
        return jsonify({'error': str(e)}), 500

    
# ==========================================
# GESTIÓN DE APARTADOS PARA EL ARTESANO
# ==========================================
@app.route('/api/apartados/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def obtener_apartados_taller(taller_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, a.producto_id, a.taller_id, a.nombre_cliente, a.email_cliente, 
                       a.telefono_cliente, a.cantidad, a.estado, a.respuesta_artesano,
                       a.fecha_creacion, p.nombre_pieza
                FROM apartados a
                LEFT JOIN productos p ON a.producto_id = p.id
                WHERE a.taller_id = %s
                ORDER BY a.id DESC
            """
            cursor.execute(sql, (taller_id,))
            data = cursor.fetchall()
        conn.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error obteniendo apartados:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/api/apartados/<int:apartado_id>', methods=['PATCH', 'DELETE', 'OPTIONS'])
def gestionar_apartado(apartado_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'PATCH':
        data = request.get_json() or {}
        nuevo_estado = data.get('estado', 'Revisado')
        respuesta = data.get('respuesta_artesano', '')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """
                    UPDATE apartados 
                    SET estado = %s, respuesta_artesano = %s 
                    WHERE id = %s
                """
                cursor.execute(sql, (nuevo_estado, respuesta, apartado_id))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Apartado actualizado con éxito'}), 200
        except Exception as e:
            print("Error actualizando apartado:", str(e))
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM apartados WHERE id = %s", (apartado_id,))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Apartado eliminado'}), 200
        except Exception as e:
            print("Error eliminando apartado:", str(e))
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Servidor Flask corriendo en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)