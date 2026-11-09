from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection

seguimiento_bp = Blueprint('seguimiento_bp', __name__)

# ==========================================
# CONSULTAR ESTADO POR CONTACTO O FOLIO
# ==========================================
@seguimiento_bp.route('/seguimiento', methods=['POST', 'OPTIONS'])
def consultar_seguimiento():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.get_json() or {}
    contacto = data.get('contacto', '').strip()

    if not contacto:
        return jsonify({'error': 'Por favor ingresa un correo, número de teléfono o folio'}), 400

    contacto_limpio = contacto.upper().replace('RES-', '').replace('APT-', '').replace('#', '')

    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            # Consultar Reservas unificando fecha y hora
            sql_reservas = """
                SELECT r.id, 'reserva' as tipo, r.nombre_visitante as nombre, 
                       r.email_visitante as email, r.telefono_visitante as telefono, 
                       r.estado, r.respuesta_artesano, 
                       CONCAT(r.fecha_reserva, ' ', COALESCE(r.hora_reserva, '')) as fecha_visita, 
                       r.numero_personas,
                       a.nombre_taller, a.telefono_whatsapp, a.google_maps_url
                FROM reservas r
                LEFT JOIN artesanias a ON r.taller_id = a.id
                WHERE r.email_visitante = %s OR r.telefono_visitante = %s OR r.id = %s
            """
            cursor.execute(sql_reservas, (contacto, contacto, contacto_limpio if contacto_limpio.isdigit() else 0))
            reservas = cursor.fetchall()

            # Consultar Apartados usando fecha_creacion y productos relacionados
            sql_apartados = """
                SELECT ap.id, 'apartado' as tipo, ap.nombre_cliente as nombre, 
                       ap.email_cliente as email, ap.telefono_cliente as telefono, 
                       ap.estado, ap.respuesta_artesano, ap.fecha_creacion as fecha_apartado, 
                       ap.cantidad,
                       COALESCE(p.nombre_pieza, 'Pieza Artesanal') AS nombre_producto,
                       COALESCE(p.precio, 0) AS precio_unitario,
                       (ap.cantidad * COALESCE(p.precio, 0)) AS precio_total,
                       a.nombre_taller, a.telefono_whatsapp, a.google_maps_url
                FROM apartados ap
                LEFT JOIN artesanias a ON ap.taller_id = a.id
                LEFT JOIN productos p ON ap.producto_id = p.id
                WHERE ap.email_cliente = %s OR ap.telefono_cliente = %s OR ap.id = %s
            """
            cursor.execute(sql_apartados, (contacto, contacto, contacto_limpio if contacto_limpio.isdigit() else 0))
            apartados = cursor.fetchall()

        conn.close()

        if not reservas and not apartados:
            return jsonify({'error': 'No se encontraron registros con ese correo, teléfono o folio.'}), 404

        return jsonify({'reservas': reservas, 'apartados': apartados}), 200

    except Exception as e:
        print("Error en seguimiento:", str(e))
        return jsonify({'error': str(e)}), 500