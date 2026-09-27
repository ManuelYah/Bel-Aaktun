import os
import pymysql
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite peticiones desde Angular (http://localhost:4200)

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'mysql_db'),
        user=os.environ.get('DB_USER', 'becal_user'),
        password=os.environ.get('DB_PASSWORD', 'becal_pass'),
        database=os.environ.get('DB_NAME', 'becal_db'),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "API Bécal Arte Bajo Tierra activa"}), 200

@app.route('/api/artesanias', methods=['GET'])
def get_artesanias():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT id, 
                       nombre_taller, 
                       artesano_encargado, 
                       calidad_partidas, 
                       precio_promedio, 
                       telefono_whatsapp, 
                       google_maps_url, 
                       imagen_url
                FROM artesanias
            """
            cursor.execute(sql)
            result = cursor.fetchall()
        connection.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)