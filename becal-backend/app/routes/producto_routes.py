import json
from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection
from app.security import login_required, puede_gestionar_taller, sin_permiso_sobre_taller, ROL_ADMIN
from flask import g

producto_bp = Blueprint('producto_bp', __name__)


@producto_bp.route('/productos', methods=['GET', 'POST', 'OPTIONS'])
def handle_productos():
    """
    Listar o crear piezas artesanales / productos
    ---
    tags:
      - Productos
    consumes:
      - application/json
    parameters:
      - name: taller_id
        in: query
        type: integer
        required: false
        description: Filtra los productos por ID de taller/artesano (solo aplica en GET)
      - in: body
        name: body
        required: false
        description: Requerido en POST para crear un producto
        schema:
          type: object
          required:
            - nombre_pieza
          properties:
            artesano_id:
              type: integer
              example: 1
            taller_id:
              type: integer
              example: 1
            nombre_pieza:
              type: string
              example: "Sombrero de jipi tejido a mano"
            descripcion:
              type: string
              example: "Elaborado con fibra natural de palma de jipi"
            precio:
              type: number
              example: 850
            calidad:
              type: string
              example: "Fina"
            imagenes:
              type: array
              items:
                type: string
              example: ["https://ejemplo.com/sombrero1.jpg"]
    responses:
      200:
        description: Lista de productos obtenida correctamente (GET)
      201:
        description: Producto creado con éxito (POST)
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
                        except (TypeError, ValueError):
                            imgs = []
                    elif not imgs:
                        imgs = []
                    row['imagenes'] = imgs
                    row['imagen_url'] = imgs[0] if len(imgs) > 0 else ''

            conn.close()
            return jsonify(data), 200
        except Exception as e:
            current_app.logger.error("Error obteniendo productos: %s", e)
            return jsonify({'error': 'Error interno del servidor'}), 500

    elif request.method == 'POST':
        from app.security import usuario_de_la_peticion
        usuario = usuario_de_la_peticion()
        if not usuario:
            return jsonify({'error': 'Sesión no válida o expirada. Inicia sesión de nuevo.'}), 401
        data = request.get_json() or {}
        if not puede_gestionar_taller(usuario, data.get('artesano_id') or data.get('taller_id')):
            return sin_permiso_sobre_taller()
        try:
            artesano_id = data.get('artesano_id') or data.get('taller_id')
            imagenes_list = data.get('imagenes', [])
            imagenes_json = json.dumps(imagenes_list)

            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO productos (artesano_id, nombre_pieza, descripcion, precio, calidad, imagenes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    artesano_id,
                    data.get('nombre_pieza'),
                    data.get('descripcion', ''),
                    data.get('precio', 0),
                    data.get('calidad', 'Fina'),
                    imagenes_json
                ))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Producto creado'}), 201
        except Exception as e:
            current_app.logger.error("Error al guardar producto: %s", e)
            return jsonify({'error': 'Error interno del servidor'}), 500


@producto_bp.route('/productos/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def obtener_productos_por_taller(taller_id):
    """
    Obtener productos filtrados por taller
    ---
    tags:
      - Productos
    parameters:
      - name: taller_id
        in: path
        type: integer
        required: true
        description: ID del taller o artesano
    responses:
      200:
        description: Listado de productos del taller indicado
      500:
        description: Error al consultar los productos por taller
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        conn = get_db_connection(current_app.config)
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
                    except (TypeError, ValueError):
                        imgs = []
                elif not imgs:
                    imgs = []
                row['imagenes'] = imgs
                row['imagen_url'] = imgs[0] if len(imgs) > 0 else ''

        conn.close()
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error("Error en productos por taller: %s", e)
        return jsonify({'error': 'Error interno del servidor'}), 500


@producto_bp.route('/productos/<int:producto_id>', methods=['DELETE', 'PUT', 'OPTIONS'])
@login_required
def gestionar_producto_individual(producto_id):
    """
    Actualizar o eliminar un producto por su ID
    ---
    tags:
      - Productos
    consumes:
      - application/json
    parameters:
      - name: producto_id
        in: path
        type: integer
        required: true
        description: ID del producto
      - in: body
        name: body
        required: false
        description: Campos para actualizar en PUT
        schema:
          type: object
          required:
            - nombre_pieza
          properties:
            nombre_pieza:
              type: string
              example: "Sombrero de jipi extra fino"
            descripcion:
              type: string
              example: "Tejido fino de alta calidad"
            precio:
              type: number
              example: 1200
            calidad:
              type: string
              example: "Extra fina"
            imagenes:
              type: array
              items:
                type: string
              example: ["https://ejemplo.com/sombrero-fino.jpg"]
    responses:
      200:
        description: Producto actualizado (PUT) o eliminado (DELETE) con éxito
      500:
        description: Error al actualizar o eliminar el producto
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Solo el dueño del taller (o un administrador) puede tocar este producto.
    conn_check = get_db_connection(current_app.config)
    try:
        with conn_check.cursor() as cursor:
            cursor.execute("SELECT artesano_id FROM productos WHERE id = %s", (producto_id,))
            fila = cursor.fetchone()
    finally:
        conn_check.close()
    if not fila:
        return jsonify({'error': 'Producto no encontrado'}), 404
    if not puede_gestionar_taller(g.usuario, fila['artesano_id']):
        return sin_permiso_sobre_taller()

    if request.method == 'DELETE':
        try:
            conn = get_db_connection(current_app.config)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
                conn.commit()
            conn.close()
            return jsonify({'message': 'Producto eliminado'}), 200
        except Exception as e:
            current_app.logger.error("Error al eliminar producto: %s", e)
            return jsonify({'error': 'Error interno del servidor'}), 500

    elif request.method == 'PUT':
        data = request.get_json() or {}
        try:
            imagenes_list = data.get('imagenes', [])
            imagenes_json = json.dumps(imagenes_list)

            conn = get_db_connection(current_app.config)
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
            current_app.logger.error("Error actualizando producto: %s", e)
            return jsonify({'error': 'Error interno del servidor'}), 500