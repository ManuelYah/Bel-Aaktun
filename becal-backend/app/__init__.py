import logging

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import mail, cors, swagger


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    logging.basicConfig(level=logging.INFO)
    if not app.config.get("SECRET_KEY_DEFINIDA"):
        app.logger.warning(
            "SECRET_KEY no está definida: se generó una temporal y las sesiones "
            "se cerrarán al reiniciar. Defínela en el archivo .env."
        )

    # Detrás de nginx/un balanceador, para leer la IP real del visitante.
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Inicializar extensiones
    mail.init_app(app)
    cors.init_app(app, resources=app.config["CORS_RESOURCES"])
    swagger.init_app(app)

    # Migraciones, hash de contraseñas y administrador inicial
    if app.config["RUN_BOOTSTRAP"]:
        from app import bootstrap
        bootstrap.ejecutar(app)

    # Registrar Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.reserva_routes import reserva_bp
    from app.routes.producto_routes import producto_bp
    from app.routes.apartado_routes import apartado_bp
    from app.routes.seguimiento_routes import seguimiento_bp
    from app.routes.foro_routes import foro_bp
    from app.routes.contacto_routes import contacto_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(reserva_bp, url_prefix='/api')
    app.register_blueprint(producto_bp, url_prefix='/api')
    app.register_blueprint(apartado_bp, url_prefix='/api')
    app.register_blueprint(seguimiento_bp, url_prefix='/api')
    app.register_blueprint(contacto_bp, url_prefix='/api')
    app.register_blueprint(admin_bp)
    app.register_blueprint(foro_bp)

    @app.after_request
    def cabeceras_de_seguridad(respuesta):
        # Evita que un archivo subido se interprete como otro tipo de contenido.
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        return respuesta

    return app
