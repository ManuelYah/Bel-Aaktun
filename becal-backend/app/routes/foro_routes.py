import os
import re
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import get_db_connection

foro_bp = Blueprint("foro", __name__, url_prefix="/api/foro")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ESTADOS_ELEGIBLES = {
    "confirmada", "confirmado",
    "rechazada", "rechazado",
    "cancelada", "cancelado",
    "aprobada", "aprobado",
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalizar_texto(valor: str | None) -> str:
    return (valor or "").strip().lower()


def normalizar_contacto(valor: str | None) -> str:
    texto = (valor or "").strip().lower()
    if re.fullmatch(r"[\d\s\-\+\(\)]+", texto):
        return re.sub(r"\D", "", texto)
    return texto


def extraer_id_solicitud(folio: str, prefijo: str) -> int | None:
    limpio = re.sub(r"^[#\s]+", "", (folio or "").strip().upper())
    match = re.fullmatch(rf"{prefijo}[-_]?0*(\d+)", limpio)
    if match:
        return int(match.group(1))
    if prefijo == "RES" and limpio.isdigit():
        return int(limpio)
    return None


def normalizar_folio_canonico(folio: str, tipo: str, solicitud_id: int) -> str:
    limpio = re.sub(r"^[#\s]+", "", (folio or "").strip().upper())
    if re.fullmatch(r"(RES|APT)-\d+", limpio):
        return limpio
    prefijo = "RES" if tipo == "RESERVA" else "APT"
    return f"{prefijo}-{int(solicitud_id):03d}"


def validar_elegibilidad(row: dict) -> bool:
    estado = normalizar_texto(row.get("estado"))
    if estado in ESTADOS_ELEGIBLES:
        return True

    fecha_creacion = row.get("fecha_creacion")
    if fecha_creacion:
        if isinstance(fecha_creacion, str):
            fecha_creacion = datetime.fromisoformat(fecha_creacion.replace(" GMT", ""))
        if (datetime.now() - fecha_creacion) >= timedelta(hours=72):
            return True

    return False


def buscar_y_validar_solicitud(cursor, folio: str, nombre: str, contacto: str):
    nombre_req = normalizar_texto(nombre)
    contacto_req = normalizar_contacto(contacto)

    if not folio or not nombre_req or not contacto_req:
        return None, "Debes ingresar folio, nombre y correo o teléfono."

    # 1. Buscar en reservas
    res_id = extraer_id_solicitud(folio, "RES")
    if res_id is not None:
        cursor.execute(
            """
            SELECT id, taller_id, nombre_visitante, email_visitante, telefono_visitante,
                   estado, fecha_creacion
            FROM reservas
            WHERE id = %s
            """,
            (res_id,),
        )
        row = cursor.fetchone()
        if row:
            if normalizar_texto(row["nombre_visitante"]) != nombre_req:
                return None, "El nombre no coincide con el registro de la reserva."

            contactos_db = {
                c
                for c in (
                    normalizar_contacto(row["email_visitante"]),
                    normalizar_contacto(row["telefono_visitante"]),
                )
                if c
            }
            if contacto_req not in contactos_db:
                return None, "El correo o teléfono no coincide con la reserva."

            if not validar_elegibilidad(row):
                return None, "La reserva aún no ha sido confirmada/rechazada ni han pasado 72 horas."

            return {
                "tipo": "RESERVA",
                "solicitud_id": row["id"],
                "taller_id": row["taller_id"],
                "contacto": contacto_req,
            }, None

    # 2. Buscar en apartados
    apt_id = extraer_id_solicitud(folio, "APT")
    if apt_id is not None:
        cursor.execute(
            """
            SELECT id, taller_id, nombre_cliente, email_cliente, telefono_cliente,
                   estado, fecha_creacion
            FROM apartados
            WHERE id = %s
            """,
            (apt_id,),
        )
        row = cursor.fetchone()
        if row:
            if normalizar_texto(row["nombre_cliente"]) != nombre_req:
                return None, "El nombre no coincide con el registro del apartado."

            contactos_db = {
                c
                for c in (
                    normalizar_contacto(row["email_cliente"]),
                    normalizar_contacto(row["telefono_cliente"]),
                )
                if c
            }
            if contacto_req not in contactos_db:
                return None, "El correo o teléfono no coincide con el apartado."

            if not validar_elegibilidad(row):
                return None, "El apartado aún no ha sido confirmado/rechazada ni han pasado 72 horas."

            return {
                "tipo": "APARTADO",
                "solicitud_id": row["id"],
                "taller_id": row["taller_id"],
                "contacto": contacto_req,
            }, None

    return None, "No se encontró ninguna reserva o apartado válido con ese folio."


def guardar_fotos(archivos, comentario_id: int, cursor):
    fotos_limpias = [
        f for f in (archivos or []) if f and f.filename and allowed_file(f.filename)
    ][:3]

    carpeta = os.path.join(current_app.root_path, "static", "uploads", "comentarios")
    os.makedirs(carpeta, exist_ok=True)

    cursor.execute("DELETE FROM comentario_fotos WHERE comentario_id = %s", (comentario_id,))

    for orden, archivo in enumerate(fotos_limpias, start=1):
        ext = archivo.filename.rsplit(".", 1)[1].lower()
        nombre_unico = f"{uuid.uuid4().hex}.{ext}"
        ruta_fisica = os.path.join(carpeta, secure_filename(nombre_unico))
        archivo.save(ruta_fisica)

        url_foto = f"http://127.0.0.1:5000/static/uploads/comentarios/{nombre_unico}"
        cursor.execute(
            """
            INSERT INTO comentario_fotos (comentario_id, foto_url, orden)
            VALUES (%s, %s, %s)
            """,
            (comentario_id, url_foto, orden),
        )


@foro_bp.route("/resumen", methods=["GET"])
def resumen_calificaciones():
    """
    Obtener promedio de calificación y total de reseñas por taller
    ---
    tags:
      - Foro
    responses:
      200:
        description: Diccionario indexado por taller_id con promedio_calificacion y total_resenas
      500:
        description: Error al calcular calificaciones
    """
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    taller_id,
                    ROUND(AVG(calificacion), 1) AS promedio_calificacion,
                    COUNT(*) AS total_resenas
                FROM comentarios_taller
                GROUP BY taller_id
                """
            )
            filas = cursor.fetchall()

        resumen = {
            fila["taller_id"]: {
                "promedio_calificacion": float(fila["promedio_calificacion"] or 0),
                "total_resenas": int(fila["total_resenas"] or 0),
            }
            for fila in filas
        }
        return jsonify(resumen), 200
    except Exception as exc:
        return jsonify({"error": f"Error al obtener resumen: {exc}"}), 500
    finally:
        conn.close()


@foro_bp.route("/comentarios", methods=["GET"])
def listar_comentarios():
    """
    Listar comentarios del foro con nombre de taller y fotos
    ---
    tags:
      - Foro
    parameters:
      - name: taller_id
        in: query
        type: integer
        required: false
        description: Filtra los comentarios por ID de taller
    responses:
      200:
        description: Lista de comentarios públicos (sin folio ni contacto verificado)
      500:
        description: Error al obtener comentarios
    """
    taller_id = request.args.get("taller_id", type=int)
    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT c.id, c.taller_id, a.nombre_taller, c.calificacion,
                       c.titulo, c.descripcion, c.created_at
                FROM comentarios_taller c
                INNER JOIN artesanias a ON c.taller_id = a.id
            """
            params = []
            if taller_id:
                sql += " WHERE c.taller_id = %s"
                params.append(taller_id)
            sql += " ORDER BY c.created_at DESC, c.id DESC"

            cursor.execute(sql, tuple(params))
            comentarios = cursor.fetchall()

            for item in comentarios:
                cursor.execute(
                    """
                    SELECT foto_url
                    FROM comentario_fotos
                    WHERE comentario_id = %s
                    ORDER BY orden ASC, id ASC
                    LIMIT 3
                    """,
                    (item["id"],),
                )
                item["fotos"] = [f["foto_url"] for f in cursor.fetchall()]

        return jsonify(comentarios), 200
    finally:
        conn.close()


@foro_bp.route("/comentarios", methods=["POST"])
def crear_comentario():
    """
    Publicar un nuevo comentario en el foro validando folio (RES / APT)
    ---
    tags:
      - Foro
    consumes:
      - multipart/form-data
    parameters:
      - name: folio
        in: formData
        type: string
        required: true
        description: Folio de reserva o apartado (ej. RES-007 o APT-020)
      - name: nombre
        in: formData
        type: string
        required: true
        description: Nombre del visitante o cliente registrado en la solicitud
      - name: contacto
        in: formData
        type: string
        required: true
        description: Correo o teléfono ligado a la reserva o apartado
      - name: calificacion
        in: formData
        type: integer
        required: true
        minimum: 1
        maximum: 5
        description: Calificación de 1 a 5 estrellas
      - name: titulo
        in: formData
        type: string
        required: true
      - name: descripcion
        in: formData
        type: string
        required: true
      - name: fotos
        in: formData
        type: file
        required: false
        description: Hasta 3 imágenes (png, jpg, jpeg, webp)
    responses:
      201:
        description: Comentario publicado correctamente
      400:
        description: Datos inválidos, solicitud no elegible o más de 3 fotos
      409:
        description: Ya existe un comentario con ese folio
      500:
        description: Error al guardar el comentario
    """
    folio = (request.form.get("folio") or "").strip()
    nombre = (request.form.get("nombre") or "").strip()
    contacto = (request.form.get("contacto") or "").strip()
    titulo = (request.form.get("titulo") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip()

    try:
        calificacion = int(request.form.get("calificacion", 0))
    except (TypeError, ValueError):
        calificacion = 0

    if calificacion < 1 or calificacion > 5:
        return jsonify({"error": "La calificación debe ser de 1 a 5 estrellas."}), 400

    if not titulo or not descripcion:
        return jsonify({"error": "El título y la descripción son obligatorios."}), 400

    archivos_fotos = request.files.getlist("fotos")
    if len(archivos_fotos) > 3:
        return jsonify({"error": "Solo puedes adjuntar hasta 3 fotografías."}), 400

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            validacion, error_msg = buscar_y_validar_solicitud(cursor, folio, nombre, contacto)
            if error_msg:
                return jsonify({"error": error_msg}), 400

            folio_canonico = normalizar_folio_canonico(
                folio, validacion["tipo"], validacion["solicitud_id"]
            )

            cursor.execute(
                "SELECT id FROM comentarios_taller WHERE folio = %s",
                (folio_canonico,),
            )
            if cursor.fetchone():
                return jsonify({
                    "error": "Ya existe un comentario registrado con este folio. Usa la opción de editar."
                }), 409

            cursor.execute(
                """
                INSERT INTO comentarios_taller (
                    folio, tipo_solicitud, solicitud_id, taller_id,
                    autor_nombre, contacto_verificado, calificacion, titulo, descripcion
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    folio_canonico,
                    validacion["tipo"],
                    validacion["solicitud_id"],
                    validacion["taller_id"],
                    nombre,
                    validacion["contacto"],
                    calificacion,
                    titulo,
                    descripcion,
                ),
            )
            comentario_id = cursor.lastrowid

            if archivos_fotos:
                guardar_fotos(archivos_fotos, comentario_id, cursor)

        conn.commit()
        return jsonify({
            "mensaje": "Comentario publicado correctamente.",
            "id": comentario_id,
            "taller_id": validacion["taller_id"],
        }), 201
    except Exception as exc:
        conn.rollback()
        return jsonify({"error": f"Error al guardar el comentario: {exc}"}), 500
    finally:
        conn.close()


@foro_bp.route("/comentarios", methods=["PUT"])
def editar_comentario():
    """
    Editar un comentario existente validando folio y contacto
    ---
    tags:
      - Foro
    consumes:
      - multipart/form-data
    parameters:
      - name: folio
        in: formData
        type: string
        required: true
        description: Folio del comentario a editar
      - name: contacto
        in: formData
        type: string
        required: true
        description: Correo o teléfono verificado del autor
      - name: calificacion
        in: formData
        type: integer
        required: true
        minimum: 1
        maximum: 5
      - name: titulo
        in: formData
        type: string
        required: true
      - name: descripcion
        in: formData
        type: string
        required: true
      - name: fotos
        in: formData
        type: file
        required: false
        description: Hasta 3 nuevas imágenes para reemplazar las anteriores
    responses:
      200:
        description: Comentario actualizado correctamente
      400:
        description: Datos incompletos o inválidos
      403:
        description: El contacto no coincide con el autor del comentario
      404:
        description: Comentario no encontrado
      500:
        description: Error al actualizar el comentario
    """
    folio = (request.form.get("folio") or "").strip()
    contacto = normalizar_contacto(request.form.get("contacto"))
    titulo = (request.form.get("titulo") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip()

    try:
        calificacion = int(request.form.get("calificacion", 0))
    except (TypeError, ValueError):
        calificacion = 0

    if not folio or not contacto:
        return jsonify({"error": "Debes indicar el folio y el correo o teléfono ligado a él."}), 400

    if calificacion < 1 or calificacion > 5:
        return jsonify({"error": "La calificación debe ser de 1 a 5 estrellas."}), 400

    if not titulo or not descripcion:
        return jsonify({"error": "El título y la descripción son obligatorios."}), 400

    archivos_fotos = request.files.getlist("fotos")
    if len(archivos_fotos) > 3:
        return jsonify({"error": "Solo puedes adjuntar hasta 3 fotografías."}), 400

    conn = get_db_connection(current_app.config)
    try:
        with conn.cursor() as cursor:
            candidatos_folio = {
                re.sub(r"^[#\s]+", "", folio.strip().upper()),
            }
            res_id = extraer_id_solicitud(folio, "RES")
            apt_id = extraer_id_solicitud(folio, "APT")
            if res_id is not None:
                candidatos_folio.add(normalizar_folio_canonico(folio, "RESERVA", res_id))
            if apt_id is not None:
                candidatos_folio.add(normalizar_folio_canonico(folio, "APARTADO", apt_id))

            placeholders = ", ".join(["%s"] * len(candidatos_folio))
            cursor.execute(
                f"""
                SELECT id, contacto_verificado
                FROM comentarios_taller
                WHERE folio IN ({placeholders})
                """,
                tuple(candidatos_folio),
            )
            comentario = cursor.fetchone()
            if not comentario:
                return jsonify({"error": "No se encontró ningún comentario ligado a ese folio."}), 404

            if normalizar_contacto(comentario["contacto_verificado"]) != contacto:
                return jsonify({
                    "error": "El correo o teléfono no coincide con el contacto registrado para este folio."
                }), 403

            cursor.execute(
                """
                UPDATE comentarios_taller
                SET calificacion = %s, titulo = %s, descripcion = %s
                WHERE id = %s
                """,
                (calificacion, titulo, descripcion, comentario["id"]),
            )

            if archivos_fotos:
                guardar_fotos(archivos_fotos, comentario["id"], cursor)

        conn.commit()
        return jsonify({"mensaje": "Comentario actualizado correctamente."}), 200
    except Exception as exc:
        conn.rollback()
        return jsonify({"error": f"Error al actualizar el comentario: {exc}"}), 500
    finally:
        conn.close()