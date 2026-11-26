from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from app.extensions import mail, get_db_connection
from app.models import generar_folio

reserva_bp = Blueprint('reserva_bp', __name__)


@reserva_bp.route('/reservas', methods=['GET', 'POST', 'OPTIONS'])
def handle_reservas():
    """
    Listar o crear reservas de visitas a talleres/cuevas
    ---
    tags:
      - Reservas
    consumes:
      - application/json
    parameters:
      - name: taller_id
        in: query
        type: integer
        required: false
        description: Filtra las reservas por ID de taller (solo aplica en GET)
      - in: body
        name: body
        required: false
        description: Requerido en POST para crear una nueva reserva
        schema:
          type: object
          required:
            - nombre_visitante
            - email_visitante
            - fecha_reserva
          properties:
            taller_id:
              type: integer
              example: 4
            nombre_visitante:
              type: string
              example: "Ana Méndez"
            email_visitante:
              type: string
              example: "ana@ejemplo.com"
            telefono_visitante:
              type: string
              example: "9991234567"
            numero_personas:
              type: integer
              example: 3
            fecha_reserva:
              type: string
              example: "2026-12-05"
            hora_reserva:
              type: string
              example: "10:00"
    responses:
      200:
        description: Lista de reservas obtenida correctamente (GET)
      201:
        description: Reserva creada con éxito, folio generado y correo enviado (POST)
      500:
        description: Error interno del servidor
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'GET':
        taller_id = request.args.get('taller_id')
        try:
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                sql = """
                    SELECT id, taller_id, nombre_visitante, email_visitante, 
                           telefono_visitante, numero_personas, fecha_reserva, 
                           hora_reserva, estado, respuesta_artesano
                    FROM reservas
                """
                if taller_id:
                    sql += " WHERE taller_id = %s ORDER BY id DESC"
                    cursor.execute(sql, (taller_id,))
                else:
                    sql += " ORDER BY id DESC"
                    cursor.execute(sql)
                data = cursor.fetchall()
            conn.close()
            return jsonify(data), 200
        except Exception as e:
            print("Error obteniendo reservas:", str(e))
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json() or {}
        try:
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO reservas (taller_id, nombre_visitante, email_visitante, telefono_visitante, numero_personas, fecha_reserva, hora_reserva, estado, respuesta_artesano)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pendiente', '')
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

                cursor.execute("SELECT nombre_taller FROM artesanias WHERE id = %s", (data.get('taller_id', 4),))
                taller_info = cursor.fetchone() or {}

            conn.close()

            folio = generar_folio("RES", reserva_id)
            email_visitante = data.get('email_visitante')
            nombre_visitante = data.get('nombre_visitante', 'Visitante')
            nombre_taller = taller_info.get('nombre_taller', 'Taller Artesanal')

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
                        <hr style="border: 0; border-top: 1px solid #eee;">
                    </div>
                    """
                    mail.send(msg)
                except Exception as mail_err:
                    print("Error enviando correo de reserva:", str(mail_err))

            return jsonify({'message': 'Reserva creada', 'folio': folio}), 201
        except Exception as e:
            print("Error creando reserva:", str(e))
            return jsonify({'error': str(e)}), 500


@reserva_bp.route('/reservas/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def reservas_por_taller(taller_id):
    """
    Obtener reservas filtradas por taller
    ---
    tags:
      - Reservas
    parameters:
      - name: taller_id
        in: path
        type: integer
        required: true
        description: ID del taller o artesanía
    responses:
      200:
        description: Listado de reservas del taller indicado
      500:
        description: Error al consultar las reservas por taller
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            sql = """
                SELECT id, taller_id, nombre_visitante, email_visitante, 
                       telefono_visitante, numero_personas, fecha_reserva, 
                       hora_reserva, estado, respuesta_artesano
                FROM reservas 
                WHERE taller_id = %s 
                ORDER BY id DESC
            """
            cursor.execute(sql, (taller_id,))
            data = cursor.fetchall()
        conn.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en reservas por taller:", str(e))
        return jsonify({'error': str(e)}), 500


@reserva_bp.route('/reservas/<int:reserva_id>', methods=['PATCH', 'DELETE', 'OPTIONS'])
def gestionar_reserva(reserva_id):
    """
    Actualizar estado/respuesta o eliminar una reserva
    ---
    tags:
      - Reservas
    consumes:
      - application/json
    parameters:
      - name: reserva_id
        in: path
        type: integer
        required: true
        description: ID de la reserva
      - in: body
        name: body
        required: false
        description: Campos para actualizar en PATCH (estado y respuesta_artesano)
        schema:
          type: object
          properties:
            estado:
              type: string
              example: "Confirmada"
            respuesta_artesano:
              type: string
              example: "¡Te esperamos a las 10:00 hrs en la entrada principal!"
    responses:
      200:
        description: Reserva actualizada (PATCH) o eliminada (DELETE) con éxito
      500:
        description: Error al actualizar o eliminar la reserva
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'PATCH':
        data = request.get_json() or {}
        nuevo_estado = data.get('estado', 'Pendiente')
        respuesta = data.get('respuesta_artesano', '')
        try:
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                sql = """
                    UPDATE reservas 
                    SET estado = %s, respuesta_artesano = %s 
                    WHERE id = %s
                """
                cursor.execute(sql, (nuevo_estado, respuesta, reserva_id))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Reserva actualizada con éxito'}), 200
        except Exception as e:
            print("Error actualizando reserva:", str(e))
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Reserva eliminada'}), 200
        except Exception as e:
            print("Error eliminando reserva:", str(e))
            return jsonify({'error': str(e)}), 500