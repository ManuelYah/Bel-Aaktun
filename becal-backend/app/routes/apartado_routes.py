from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from app.extensions import mail, get_db_connection
from app.models import generar_folio

apartado_bp = Blueprint('apartado_bp', __name__)

@apartado_bp.route('/apartados', methods=['POST', 'OPTIONS'])
def crear_apartado():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json() or {}
    try:
        conn = get_db_connection(current_app.config)
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
                    <hr style="border: 0; border-top: 1px solid #eee;">
                </div>
                """
                mail.send(msg)
            except Exception as mail_err:
                print("Error enviando correo de apartado:", str(mail_err))

        return jsonify({'message': 'Producto apartado con éxito', 'folio': folio}), 201
    except Exception as e:
        print("Error creando apartado:", str(e))
        return jsonify({'error': str(e)}), 500

@apartado_bp.route('/api/apartados/taller/<int:taller_id>', methods=['GET', 'OPTIONS']) # O ajustado si usas url_prefix
@apartado_bp.route('/apartados/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def obtener_apartados_taller(taller_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection(current_app.config)
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

@apartado_bp.route('/apartados/<int:apartado_id>', methods=['PATCH', 'DELETE', 'OPTIONS'])
def gestionar_apartado(apartado_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'PATCH':
        data = request.get_json() or {}
        nuevo_estado = data.get('estado', 'Revisado')
        respuesta = data.get('respuesta_artesano', '')
        try:
            conn = get_db_connection(current_app.config)
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
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM apartados WHERE id = %s", (apartado_id,))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Apartado eliminado'}), 200
        except Exception as e:
            print("Error eliminando apartado:", str(e))
            return jsonify({'error': str(e)}), 500