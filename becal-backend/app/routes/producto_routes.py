import json
from flask import Blueprint, request, jsonify, current_app
from app.extensions import get_db_connection

producto_bp = Blueprint('producto_bp', __name__)

@producto_bp.route('/productos', methods=['GET', 'POST', 'OPTIONS'])
def handle_productos():
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
            print("ERROR EXACTO AL GUARDAR PRODUCTO:", str(e))
            return jsonify({'error': str(e)}), 500

@producto_bp.route('/productos/taller/<int:taller_id>', methods=['GET', 'OPTIONS'])
def obtener_productos_por_taller(taller_id):
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

@producto_bp.route('/productos/<int:producto_id>', methods=['DELETE', 'PUT', 'OPTIONS'])
def gestionar_producto_individual(producto_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'DELETE':
        try:
            conn = get_db_connection(current_app.config)
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
            print("Error actualizando producto:", str(e))
            return jsonify({'error': str(e)}), 500