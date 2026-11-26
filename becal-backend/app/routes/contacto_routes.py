from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from app.extensions import get_db_connection
from app.utils import email_valido

contacto_bp = Blueprint("contacto_bp", __name__)



@contacto_bp.route("/contacto", methods=["POST", "OPTIONS"])
def enviar_contacto():
    """
    Enviar un mensaje desde el formulario de contacto
    ---
    tags:
      - Contacto
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - mensaje
          properties:
            nombre:
              type: string
              example: "María López"
            email:
              type: string
              example: "maria@correo.com"
            telefono:
              type: string
              example: "9961234567"
            mensaje:
              type: string
              example: "¿Tienen visitas guiadas los domingos?"
    responses:
      201:
        description: Mensaje recibido. Lo verá el administrador en su panel
      400:
        description: Datos incompletos o no válidos
      429:
        description: Demasiados mensajes desde la misma conexión
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}

    # Campo trampa para bots: las personas no lo ven ni lo llenan.
    if (data.get("website") or "").strip():
        return jsonify({"message": "Mensaje recibido."}), 201

    nombre = (data.get("nombre") or "").strip()
    email = (data.get("email") or "").strip()
    telefono = (data.get("telefono") or "").strip()
    mensaje = (data.get("mensaje") or "").strip()

    if len(nombre) < 2 or len(nombre) > 120:
        return jsonify({"error": "Escribe tu nombre (entre 2 y 120 caracteres)."}), 400
    if len(mensaje) < 5 or len(mensaje) > 2000:
        return jsonify({"error": "El mensaje debe tener entre 5 y 2000 caracteres."}), 400
    if not email and not telefono:
        return jsonify({"error": "Déjanos un correo o un teléfono para poder responderte."}), 400
    if email and not email_valido(email):
        return jsonify({"error": "El correo no es válido."}), 400
    if telefono and (len(telefono) > 30 or sum(c.isdigit() for c in telefono) < 7):
        return jsonify({"error": "El teléfono no es válido."}), 400

    ip = (request.remote_addr or "")[:45]
    ahora = datetime.now()

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS n FROM mensajes_contacto WHERE ip = %s AND created_at >= %s",
                (ip, ahora - timedelta(hours=1)),
            )
            if cursor.fetchone()["n"] >= current_app.config.get('CONTACTO_MAX_POR_HORA', 5):
                return jsonify({"error": "Has enviado varios mensajes seguidos. Intenta de nuevo más tarde."}), 429

            cursor.execute(
                """
                INSERT INTO mensajes_contacto (nombre, email, telefono, mensaje, estado, ip, created_at)
                VALUES (%s, %s, %s, %s, 'NUEVO', %s, %s)
                """,
                (nombre, email or None, telefono or None, mensaje, ip, ahora),
            )
        conn.commit()
        return jsonify({"message": "Mensaje recibido. Te responderemos pronto."}), 201
    except Exception:
        conn.rollback()
        current_app.logger.exception("Error al guardar mensaje de contacto")
        return jsonify({"error": "No pudimos enviar tu mensaje. Inténtalo de nuevo."}), 500
    finally:
        conn.close()
