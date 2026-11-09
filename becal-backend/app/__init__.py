from flask import Flask
from app.config import Config
from app.extensions import mail, cors

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    mail.init_app(app)
    cors.init_app(app, resources=app.config['CORS_RESOURCES'])

    # Registrar Blueprints
    
    from app.routes.auth_routes import auth_bp
    from app.routes.reserva_routes import reserva_bp
    from app.routes.producto_routes import producto_bp
    from app.routes.apartado_routes import apartado_bp
    from app.routes.seguimiento_routes import seguimiento_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(reserva_bp, url_prefix='/api')
    app.register_blueprint(producto_bp, url_prefix='/api')
    app.register_blueprint(apartado_bp, url_prefix='/api')
    app.register_blueprint(seguimiento_bp, url_prefix='/api')

    return app