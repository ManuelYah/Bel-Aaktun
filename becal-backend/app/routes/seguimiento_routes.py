import re

from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection

seguimiento_bp = Blueprint('seguimiento_bp', __name__)

_FOLIO_RE = re.compile(r"^#?\s*(RES|APT)[-_]?\s*0*(\d+)$", re.IGNORECASE)
# Quita espacios, guiones, paréntesis y "+" del teléfono guardado para comparar solo dígitos.
_TEL_SQL = "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE({col}, ' ', ''), '-', ''), '+', ''), '(', ''), ')', '')"


def _interpretar_folio(valor):
    """Devuelve ('RES' | 'APT', id) o None si no tiene forma de folio."""
    m = _FOLIO_RE.match((valor or '').strip())
    return (m.group(1).upper(), int(m.group(2))) if m else None


# ==========================================
# CONSULTAR ESTADO POR CORREO O TELÉFONO
# ==========================================
@seguimiento_bp.route('/seguimiento', methods=['POST', 'OPTIONS'])
def consultar_seguimiento():
    """
    Consultar estado de reservas y apartados por correo o teléfono
    ---
    tags:
      - Seguimiento
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - contacto
          properties:
            contacto:
              type: string
              description: Correo o teléfono con el que se hizo la reserva o el apartado
              example: "visitante@correo.com"
            folio:
              type: string
              description: Opcional. Limita el resultado a una solicitud (RES-7 o APT-3)
              example: "RES-7"
    responses:
      200:
        description: Coincidencias encontradas en reservas y/o apartados
      400:
        description: Falta el correo o teléfono
      404:
        description: No se encontraron registros
      500:
        description: Error interno del servidor
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json(silent=True) or {}
    contacto = (data.get('contacto') or '').strip()
    folio_texto = (data.get('folio') or '').strip()

    # Un folio solo (sin correo ni teléfono) permitiría adivinar números y ver
    # datos de otras personas, así que siempre se pide el contacto.
    # Un número corto (p. ej. "7") tampoco puede ser un teléfono: probablemente es un folio.
    if not contacto or _interpretar_folio(contacto) or re.fullmatch(r'\d{1,6}', contacto):
        return jsonify({
            'error': 'Ingresa el correo o el teléfono con el que hiciste tu reserva o apartado. '
                     'Si quieres, agrega tu folio para ver solo esa solicitud.'
        }), 400

    folio = None
    if folio_texto:
        folio = _interpretar_folio(folio_texto)
        if not folio:
            return jsonify({'error': 'El folio no es válido. Ejemplos: RES-7 o APT-3.'}), 400

    correo = contacto.lower()
    digitos = re.sub(r'\D', '', contacto)
    # Evita que un texto cualquiera ("a", "1") coincida con teléfonos parciales.
    digitos = digitos if len(digitos) >= 7 else '__sin_telefono__'

    conn = None
    try:
        conn = get_db_connection(current_app.config)
        with conn.cursor() as cursor:
            reservas, apartados = [], []

            if folio is None or folio[0] == 'RES':
                sql_reservas = f"""
                    SELECT r.id, 'reserva' as tipo, r.nombre_visitante as nombre,
                           r.email_visitante as email, r.telefono_visitante as telefono,
                           r.estado, r.respuesta_artesano,
                           CONCAT(r.fecha_reserva, ' ', COALESCE(r.hora_reserva, '')) as fecha_visita,
                           r.numero_personas,
                           a.nombre_taller, a.telefono_whatsapp, a.google_maps_url
                    FROM reservas r
                    LEFT JOIN artesanias a ON r.taller_id = a.id
                    WHERE (LOWER(r.email_visitante) = %s
                           OR {_TEL_SQL.format(col='r.telefono_visitante')} = %s)
                """
                params = [correo, digitos]
                if folio:
                    sql_reservas += " AND r.id = %s"
                    params.append(folio[1])
                cursor.execute(sql_reservas, tuple(params))
                reservas = cursor.fetchall()

            if folio is None or folio[0] == 'APT':
                sql_apartados = f"""
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
                    WHERE (LOWER(ap.email_cliente) = %s
                           OR {_TEL_SQL.format(col='ap.telefono_cliente')} = %s)
                """
                params = [correo, digitos]
                if folio:
                    sql_apartados += " AND ap.id = %s"
                    params.append(folio[1])
                cursor.execute(sql_apartados, tuple(params))
                apartados = cursor.fetchall()

        if not reservas and not apartados:
            return jsonify({'error': 'No se encontraron registros con ese correo o teléfono.'}), 404

        return jsonify({'reservas': reservas, 'apartados': apartados}), 200

    except Exception:
        current_app.logger.exception("Error en seguimiento")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if conn:
            conn.close()
