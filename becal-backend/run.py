import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Solo para desarrollo local. En Docker/producción se usa gunicorn.
    debug = os.getenv('FLASK_DEBUG', '0').strip().lower() in {'1', 'true', 'yes'}
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    print(f"Servidor Flask corriendo en http://{host}:5000 (debug={debug})")
    app.run(host=host, port=5000, debug=debug)
