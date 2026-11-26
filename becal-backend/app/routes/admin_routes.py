"""Panel de administración: moderación de reseñas y bandeja de mensajes."""
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request

from app.extensions import get_db_connection
from app.security import ROL_ADMIN, roles_required
from app.utils import borrar_archivos_de_fotos, url_publica

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")

ESTADOS_COMENTARIO = ("PENDIENTE", "APROBADO", "RECHAZADO")
ESTADOS_MENSAJE = ("NUEVO", "LEIDO", "ARCHIVADO")
LIMITE_MAXIMO = 200


def _limite():
    valor = request.args.get("limit", default=100, type=int)
    return max(1, min(valor or 100, LIMITE_MAXIMO))


def _error_interno(mensaje_log):
    current_app.logger.exception(mensaje_log)
    return jsonify({"error": "Error interno del servidor"}), 500


# ---------------------------------------------------------------- resumen
@admin_bp.route("/resumen", methods=["GET"])
@roles_required(ROL_ADMIN)
def resumen_admin():
    """
    Contadores para las insignias del panel
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    responses:
      200:
        description: Reseñas pendientes y mensajes nuevos
      401:
        description: Sesión no válida
      403:
        description: Solo administradores
    """
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS n FROM comentarios_taller WHERE estado = 'PENDIENTE'")
            pendientes = cursor.fetchone()["n"]
            cursor.execute("SELECT COUNT(*) AS n FROM mensajes_contacto WHERE estado = 'NUEVO'")
            nuevos = cursor.fetchone()["n"]
        return jsonify({
            "comentarios_pendientes": int(pendientes),
            "mensajes_nuevos": int(nuevos),
        }), 200
    except Exception:
        return _error_interno("Error en resumen de administración")
    finally:
        conn.close()


# ---------------------------------------------------------------- reseñas
@admin_bp.route("/comentarios", methods=["GET"])
@roles_required(ROL_ADMIN)
def listar_comentarios_admin():
    """
    Listar reseñas del foro por estado
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    parameters:
      - in: query
        name: estado
        type: string
        enum: [PENDIENTE, APROBADO, RECHAZADO, TODOS]
        default: PENDIENTE
      - in: query
        name: limit
        type: integer
        default: 100
    responses:
      200:
        description: Lista de reseñas con fotos y datos de contacto
      400:
        description: Estado no válido
      401:
        description: Sesión no válida
      403:
        description: Solo administradores
    """
    estado = (request.args.get("estado") or "PENDIENTE").strip().upper()
    if estado != "TODOS" and estado not in ESTADOS_COMENTARIO:
        return jsonify({"error": "Estado no válido."}), 400

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT c.id, c.folio, c.tipo_solicitud, c.taller_id, a.nombre_taller,
                       c.autor_nombre, c.contacto_verificado AS contacto,
                       c.calificacion, c.titulo, c.descripcion, c.estado,
                       c.motivo_rechazo, c.created_at, c.updated_at, c.moderado_en
                FROM comentarios_taller c
                LEFT JOIN artesanias a ON c.taller_id = a.id
            """
            params = []
            if estado != "TODOS":
                sql += " WHERE c.estado = %s"
                params.append(estado)
            sql += " ORDER BY c.created_at DESC, c.id DESC LIMIT %s"
            params.append(_limite())
            cursor.execute(sql, tuple(params))
            comentarios = cursor.fetchall()

            for item in comentarios:
                cursor.execute(
                    "SELECT foto_url FROM comentario_fotos "
                    "WHERE comentario_id = %s ORDER BY orden ASC, id ASC LIMIT 3",
                    (item["id"],),
                )
                item["fotos"] = [url_publica(f["foto_url"]) for f in cursor.fetchall()]
        return jsonify(comentarios), 200
    except Exception:
        return _error_interno("Error al listar reseñas para el administrador")
    finally:
        conn.close()


@admin_bp.route("/comentarios/<int:comentario_id>", methods=["PATCH"])
@roles_required(ROL_ADMIN)
def moderar_comentario(comentario_id):
    """
    Aprobar, rechazar o regresar a pendiente una reseña
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: comentario_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - estado
          properties:
            estado:
              type: string
              enum: [APROBADO, RECHAZADO, PENDIENTE]
            motivo:
              type: string
              description: Motivo del rechazo (opcional, máximo 255 caracteres)
    responses:
      200:
        description: Reseña actualizada. Solo las APROBADO aparecen en el foro
      400:
        description: Estado no válido
      404:
        description: Reseña no encontrada
    """
    data = request.get_json(silent=True) or {}
    estado = (data.get("estado") or "").strip().upper()
    if estado not in ESTADOS_COMENTARIO:
        return jsonify({"error": "Estado no válido."}), 400

    motivo = (data.get("motivo") or "").strip()[:255] if estado == "RECHAZADO" else ""

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM comentarios_taller WHERE id = %s", (comentario_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Reseña no encontrada."}), 404

            moderado_por = None if estado == "PENDIENTE" else g.usuario["id"]
            moderado_en = None if estado == "PENDIENTE" else datetime.now()
            cursor.execute(
                """
                UPDATE comentarios_taller
                SET estado = %s, motivo_rechazo = %s, moderado_por = %s, moderado_en = %s
                WHERE id = %s
                """,
                (estado, motivo or None, moderado_por, moderado_en, comentario_id),
            )
        conn.commit()
        return jsonify({"message": "Reseña actualizada.", "id": comentario_id, "estado": estado}), 200
    except Exception:
        conn.rollback()
        return _error_interno("Error al moderar reseña")
    finally:
        conn.close()


@admin_bp.route("/comentarios/<int:comentario_id>", methods=["DELETE"])
@roles_required(ROL_ADMIN)
def eliminar_comentario(comentario_id):
    """
    Eliminar una reseña y sus fotos
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comentario_id
        type: integer
        required: true
    responses:
      200:
        description: Reseña eliminada
      404:
        description: Reseña no encontrada
    """
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM comentarios_taller WHERE id = %s", (comentario_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Reseña no encontrada."}), 404

            cursor.execute("SELECT foto_url FROM comentario_fotos WHERE comentario_id = %s", (comentario_id,))
            rutas = [fila["foto_url"] for fila in cursor.fetchall()]
            cursor.execute("DELETE FROM comentario_fotos WHERE comentario_id = %s", (comentario_id,))
            cursor.execute("DELETE FROM comentarios_taller WHERE id = %s", (comentario_id,))
        conn.commit()
        borrar_archivos_de_fotos(rutas)
        return jsonify({"message": "Reseña eliminada."}), 200
    except Exception:
        conn.rollback()
        return _error_interno("Error al eliminar reseña")
    finally:
        conn.close()


# ---------------------------------------------------------------- mensajes de contacto
@admin_bp.route("/mensajes", methods=["GET"])
@roles_required(ROL_ADMIN)
def listar_mensajes():
    """
    Listar mensajes enviados desde el formulario de contacto
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    parameters:
      - in: query
        name: estado
        type: string
        enum: [NUEVO, LEIDO, ARCHIVADO, TODOS]
        default: NUEVO
      - in: query
        name: limit
        type: integer
        default: 100
    responses:
      200:
        description: Lista de mensajes
      400:
        description: Estado no válido
    """
    estado = (request.args.get("estado") or "NUEVO").strip().upper()
    if estado != "TODOS" and estado not in ESTADOS_MENSAJE:
        return jsonify({"error": "Estado no válido."}), 400

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            sql = (
                "SELECT id, nombre, email, telefono, mensaje, estado, created_at, leido_en "
                "FROM mensajes_contacto"
            )
            params = []
            if estado != "TODOS":
                sql += " WHERE estado = %s"
                params.append(estado)
            sql += " ORDER BY created_at DESC, id DESC LIMIT %s"
            params.append(_limite())
            cursor.execute(sql, tuple(params))
            return jsonify(cursor.fetchall()), 200
    except Exception:
        return _error_interno("Error al listar mensajes de contacto")
    finally:
        conn.close()


@admin_bp.route("/mensajes/<int:mensaje_id>", methods=["PATCH"])
@roles_required(ROL_ADMIN)
def actualizar_mensaje(mensaje_id):
    """
    Marcar un mensaje como nuevo, leído o archivado
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: mensaje_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - estado
          properties:
            estado:
              type: string
              enum: [NUEVO, LEIDO, ARCHIVADO]
    responses:
      200:
        description: Mensaje actualizado
      400:
        description: Estado no válido
      404:
        description: Mensaje no encontrado
    """
    data = request.get_json(silent=True) or {}
    estado = (data.get("estado") or "").strip().upper()
    if estado not in ESTADOS_MENSAJE:
        return jsonify({"error": "Estado no válido."}), 400

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM mensajes_contacto WHERE id = %s", (mensaje_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Mensaje no encontrado."}), 404
            leido_en = None if estado == "NUEVO" else datetime.now()
            cursor.execute(
                "UPDATE mensajes_contacto SET estado = %s, leido_en = %s WHERE id = %s",
                (estado, leido_en, mensaje_id),
            )
        conn.commit()
        return jsonify({"message": "Mensaje actualizado.", "id": mensaje_id, "estado": estado}), 200
    except Exception:
        conn.rollback()
        return _error_interno("Error al actualizar mensaje")
    finally:
        conn.close()


@admin_bp.route("/mensajes/<int:mensaje_id>", methods=["DELETE"])
@roles_required(ROL_ADMIN)
def eliminar_mensaje(mensaje_id):
    """
    Eliminar un mensaje de contacto
    ---
    tags:
      - Administración
    security:
      - Bearer: []
    parameters:
      - in: path
        name: mensaje_id
        type: integer
        required: true
    responses:
      200:
        description: Mensaje eliminado
      404:
        description: Mensaje no encontrado
    """
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM mensajes_contacto WHERE id = %s", (mensaje_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Mensaje no encontrado."}), 404
            cursor.execute("DELETE FROM mensajes_contacto WHERE id = %s", (mensaje_id,))
        conn.commit()
        return jsonify({"message": "Mensaje eliminado."}), 200
    except Exception:
        conn.rollback()
        return _error_interno("Error al eliminar mensaje")
    finally:
        conn.close()
